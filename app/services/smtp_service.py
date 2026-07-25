import base64
import json
import uuid
import datetime
from typing import Optional, List, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.db.database import db_helper
from app.core.config import settings

def _get_cipher():
    # Derive 32-byte key from SECRET_KEY
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=b"svarp_email_portal_salt",
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(settings.SECRET_KEY.encode()))
    return Fernet(key)

def encrypt_password(plain: str) -> str:
    cipher = _get_cipher()
    return cipher.encrypt(plain.encode()).decode()

def decrypt_password(cipher_text: str) -> str:
    cipher = _get_cipher()
    return cipher.decrypt(cipher_text.encode()).decode()

class SMTPService:
    async def create_smtp_config(self, data: dict) -> dict:
        config_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        encrypted_pwd = encrypt_password(data["password"])

        async with db_helper.get_db_connection() as db:
            if data.get("is_default", False):
                await db.execute("UPDATE smtp_configs SET is_default = 0")

            await db.execute("""
            INSERT INTO smtp_configs (
                id, name, host, port, username, password, from_email, from_name,
                use_tls, use_ssl, is_default, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                config_id,
                data["name"],
                data["host"],
                data["port"],
                data["username"],
                encrypted_pwd,
                data["from_email"],
                data.get("from_name", "Email Portal"),
                1 if data.get("use_tls", True) else 0,
                1 if data.get("use_ssl", False) else 0,
                1 if data.get("is_default", False) else 0,
                1,
                now,
                now
            ))
            await db.commit()

        return await self.get_smtp_config(config_id)

    async def get_smtp_config(self, config_id: str, include_decrypted_password: bool = False) -> Optional[dict]:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM smtp_configs WHERE id = ?", (config_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            
            d = dict(row)
            d["use_tls"] = bool(d["use_tls"])
            d["use_ssl"] = bool(d["use_ssl"])
            d["is_default"] = bool(d["is_default"])
            d["is_active"] = bool(d["is_active"])
            
            if include_decrypted_password:
                try:
                    d["plain_password"] = decrypt_password(d["password"])
                except Exception:
                    d["plain_password"] = d["password"]
            d.pop("password", None)
            return d

    async def list_smtp_configs(self) -> List[dict]:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM smtp_configs ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                d["use_tls"] = bool(d["use_tls"])
                d["use_ssl"] = bool(d["use_ssl"])
                d["is_default"] = bool(d["is_default"])
                d["is_active"] = bool(d["is_active"])
                d.pop("password", None)
                result.append(d)
            return result

    async def get_default_smtp_config(self, include_decrypted_password: bool = True) -> Optional[dict]:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM smtp_configs WHERE is_default = 1 AND is_active = 1 LIMIT 1")
            row = await cursor.fetchone()
            if not row:
                # Fallback to first active
                cursor = await db.execute("SELECT * FROM smtp_configs WHERE is_active = 1 LIMIT 1")
                row = await cursor.fetchone()
            
            if not row:
                return None

            d = dict(row)
            d["use_tls"] = bool(d["use_tls"])
            d["use_ssl"] = bool(d["use_ssl"])
            d["is_default"] = bool(d["is_default"])
            d["is_active"] = bool(d["is_active"])
            
            if include_decrypted_password:
                try:
                    d["plain_password"] = decrypt_password(d["password"])
                except Exception:
                    d["plain_password"] = d["password"]
            d.pop("password", None)
            return d

    async def update_smtp_config(self, config_id: str, updates: dict) -> Optional[dict]:
        existing = await self.get_smtp_config(config_id)
        if not existing:
            return None

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        async with db_helper.get_db_connection() as db:
            if updates.get("is_default", False):
                await db.execute("UPDATE smtp_configs SET is_default = 0")

            fields = []
            values = []
            for k, v in updates.items():
                if v is not None:
                    if k == "password":
                        fields.append("password = ?")
                        values.append(encrypt_password(v))
                    elif k in ["use_tls", "use_ssl", "is_default", "is_active"]:
                        fields.append(f"{k} = ?")
                        values.append(1 if v else 0)
                    else:
                        fields.append(f"{k} = ?")
                        values.append(v)
            
            fields.append("updated_at = ?")
            values.append(now)
            values.append(config_id)

            sql = f"UPDATE smtp_configs SET {', '.join(fields)} WHERE id = ?"
            await db.execute(sql, values)
            await db.commit()

        return await self.get_smtp_config(config_id)

    async def delete_smtp_config(self, config_id: str) -> bool:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("DELETE FROM smtp_configs WHERE id = ?", (config_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def update_test_status(self, config_id: str, status: str):
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with db_helper.get_db_connection() as db:
            await db.execute("UPDATE smtp_configs SET test_status = ?, last_tested_at = ? WHERE id = ?", (status, now, config_id))
            await db.commit()

    async def test_smtp_connection(self, config_id: str, test_recipient: Optional[str] = None) -> dict:
        config = await self.get_smtp_config(config_id, include_decrypted_password=True)
        if not config:
            return {"success": False, "message": "SMTP configuration not found"}

        import aiosmtplib
        from email.message import EmailMessage

        try:
            smtp = aiosmtplib.SMTP(
                hostname=config["host"],
                port=config["port"],
                use_tls=config["use_ssl"],
                start_tls=config["use_tls"] if not config["use_ssl"] else False,
                timeout=10
            )
            await smtp.connect()
            await smtp.login(config["username"], config["plain_password"])

            if test_recipient:
                msg = EmailMessage()
                msg["From"] = f"{config['from_name']} <{config['from_email']}>"
                msg["To"] = test_recipient
                msg["Subject"] = "SMTP Gateway Test Email"
                msg.set_content("This is a test email confirming your Hostinger/SMTP connection works properly!")
                await smtp.send_message(msg)

            await smtp.quit()
            await self.update_test_status(config_id, "success")
            return {"success": True, "message": "SMTP connection & authentication successful!"}
        except Exception as e:
            await self.update_test_status(config_id, "failed")
            return {"success": False, "message": f"SMTP test failed: {str(e)}"}

smtp_service = SMTPService()

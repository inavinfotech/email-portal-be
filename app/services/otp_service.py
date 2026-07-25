import hashlib
import random
import secrets
import uuid
import datetime
from typing import Optional
from app.db.database import db_helper
from app.core.config import settings
from app.services.email_service import email_service

def _hash_otp(code: str) -> str:
    return hashlib.sha256(code.encode()).hexdigest()

def _mask_identifier(identifier: str) -> str:
    if "@" in identifier:
        user, domain = identifier.split("@", 1)
        if len(user) <= 2:
            masked_user = user[0] + "*"
        else:
            masked_user = user[0] + "*" * (len(user) - 2) + user[-1]
        return f"{masked_user}@{domain}"
    return identifier[:2] + "*" * (len(identifier) - 4) + identifier[-2:]

class OTPService:
    async def generate_and_send_otp(
        self,
        identifier: str,
        purpose: str = "login",
        template_slug: str = "otp-verification",
        app_id: Optional[str] = None,
        app_name: Optional[str] = "Example App",
        custom_code: Optional[str] = None
    ) -> dict:
        otp_id = str(uuid.uuid4())
        if custom_code and custom_code.strip():
            raw_code = custom_code.strip()
        else:
            raw_code = "".join([str(random.randint(0, 9)) for _ in range(settings.OTP_LENGTH)])
        hashed_code = _hash_otp(raw_code)

        now_dt = datetime.datetime.now(datetime.timezone.utc)
        expires_dt = now_dt + datetime.timedelta(minutes=settings.OTP_EXPIRY_MINUTES)
        
        now_str = now_dt.isoformat()
        expires_str = expires_dt.isoformat()

        async with db_helper.get_db_connection() as db:
            # Invalidate previous unverified OTPs for this identifier + purpose
            await db.execute("""
            UPDATE otp_records SET is_verified = 0 WHERE identifier = ? AND purpose = ? AND is_verified = 0
            """, (identifier, purpose))

            await db.execute("""
            INSERT INTO otp_records (
                id, app_id, identifier, otp_code, purpose, attempts, max_attempts,
                is_verified, expires_at, created_at
            ) VALUES (?, ?, ?, ?, ?, 0, ?, 0, ?, ?)
            """, (
                otp_id, app_id, identifier, hashed_code, purpose,
                settings.OTP_MAX_ATTEMPTS, expires_str, now_str
            ))
            await db.commit()

        # Send via email service
        otp_status = "sent"
        try:
            res = await email_service.send_templated_email(
                template_slug=template_slug,
                to_email=identifier,
                variables={
                    "otp_code": raw_code,
                    "expiry_minutes": str(settings.OTP_EXPIRY_MINUTES),
                    "app_name": app_name
                },
                app_id=app_id,
                metadata={"otp_id": otp_id, "purpose": purpose}
            )
            if res and res.get("status") == "failed":
                otp_status = "failed"
        except Exception as e:
            logger.error(f"OTP dispatch error: {e}")
            otp_status = "failed"

        return {
            "otp_id": otp_id,
            "masked_identifier": _mask_identifier(identifier),
            "expires_at": expires_str,
            "purpose": purpose,
            "status": otp_status
        }

    async def verify_otp(self, identifier: str, otp_code: str, purpose: str = "login") -> dict:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("""
            SELECT * FROM otp_records
            WHERE identifier = ? AND purpose = ? AND is_verified = 0
            ORDER BY created_at DESC LIMIT 1
            """, (identifier, purpose))
            row = await cursor.fetchone()

            if not row:
                return {"verified": False, "otp_id": "", "identifier": identifier, "purpose": purpose, "message": "No active OTP request found"}

            record = dict(row)
            now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # Check expiration
            if record["expires_at"] < now_iso:
                return {"verified": False, "otp_id": record["id"], "identifier": identifier, "purpose": purpose, "message": "OTP has expired"}

            # Check max attempts
            if record["attempts"] >= record["max_attempts"]:
                return {"verified": False, "otp_id": record["id"], "identifier": identifier, "purpose": purpose, "message": "Maximum verification attempts exceeded"}

            # Verify hash
            hashed_input = _hash_otp(otp_code)
            if hashed_input != record["otp_code"]:
                new_attempts = record["attempts"] + 1
                await db.execute("UPDATE otp_records SET attempts = ? WHERE id = ?", (new_attempts, record["id"]))
                await db.commit()
                remaining = record["max_attempts"] - new_attempts
                return {"verified": False, "otp_id": record["id"], "identifier": identifier, "purpose": purpose, "message": f"Invalid OTP code. {remaining} attempts remaining."}

            # Success
            await db.execute("""
            UPDATE otp_records SET is_verified = 1, verified_at = ? WHERE id = ?
            """, (now_iso, record["id"]))
            await db.commit()

            return {
                "verified": True,
                "otp_id": record["id"],
                "identifier": identifier,
                "purpose": purpose,
                "message": "OTP verified successfully!"
            }

    async def cleanup_expired_otps(self):
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with db_helper.get_db_connection() as db:
            await db.execute("DELETE FROM otp_records WHERE expires_at < ? AND is_verified = 0", (now_iso,))
            await db.commit()

otp_service = OTPService()

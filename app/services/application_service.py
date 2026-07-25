import json
import uuid
import datetime
from typing import Optional, List, Tuple
from app.db.database import db_helper
from app.auth.security import generate_api_key, generate_api_secret, get_secret_hash

class ApplicationService:
    async def create_application(self, data: dict) -> Tuple[dict, str]:
        app_id = str(uuid.uuid4())
        api_key = generate_api_key()
        plain_secret = generate_api_secret()
        hashed_secret = get_secret_hash(plain_secret)
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        domains = data.get("allowed_domains", ["*"])
        smtp_config_id = data.get("smtp_config_id")

        async with db_helper.get_db_connection() as db:
            await db.execute("""
            INSERT INTO applications (
                id, name, api_key, api_secret, status, allowed_domains, rate_limit, smtp_config_id, created_at, updated_at
            ) VALUES (?, ?, ?, ?, 'active', ?, ?, ?, ?, ?)
            """, (
                app_id,
                data["name"],
                api_key,
                hashed_secret,
                json.dumps(domains),
                data.get("rate_limit", 50),
                smtp_config_id,
                now,
                now
            ))
            await db.commit()

        app_record = await self.get_application_by_id(app_id)
        return app_record, plain_secret

    async def get_application_by_id(self, app_id: str) -> Optional[dict]:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM applications WHERE id = ?", (app_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            return self._format_app(row)

    async def get_application_by_api_key(self, api_key: str) -> Optional[dict]:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM applications WHERE api_key = ?", (api_key,))
            row = await cursor.fetchone()
            if not row:
                return None
            return self._format_app(row)

    async def list_applications(self) -> List[dict]:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM applications ORDER BY created_at DESC")
            rows = await cursor.fetchall()
            return [self._format_app(row) for row in rows]

    async def update_application(self, app_id: str, updates: dict) -> Optional[dict]:
        existing = await self.get_application_by_id(app_id)
        if not existing:
            return None

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        async with db_helper.get_db_connection() as db:
            fields = []
            values = []
            for k, v in updates.items():
                if k == "allowed_domains":
                    fields.append("allowed_domains = ?")
                    values.append(json.dumps(v) if v is not None else '["*"]')
                else:
                    fields.append(f"{k} = ?")
                    values.append(v)

            fields.append("updated_at = ?")
            values.append(now)
            values.append(app_id)

            sql = f"UPDATE applications SET {', '.join(fields)} WHERE id = ?"
            await db.execute(sql, values)
            await db.commit()

        return await self.get_application_by_id(app_id)

    async def delete_application(self, app_id: str) -> bool:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("DELETE FROM applications WHERE id = ?", (app_id,))
            await db.commit()
            return cursor.rowcount > 0

    def _format_app(self, row) -> dict:
        d = dict(row)
        try:
            d["allowed_domains"] = json.loads(d["allowed_domains"]) if isinstance(d["allowed_domains"], str) else ["*"]
        except Exception:
            d["allowed_domains"] = ["*"]
        return d

application_service = ApplicationService()

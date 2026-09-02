import json
import uuid
import datetime
import logging
import aiosmtplib
from email.message import EmailMessage
from typing import Optional, List, Dict, Any, Union
from app.db.database import db_helper
from app.services.smtp_service import smtp_service
from app.services.template_service import template_service
from app.services.application_service import application_service

logger = logging.getLogger("uvicorn.error")

def _normalize_recipients(val: Optional[Union[List[str], str]]) -> Optional[str]:
    """Normalize a list or string of emails into a clean comma-separated string."""
    if not val:
        return None
    if isinstance(val, str):
        emails = [e.strip() for e in val.replace(";", ",").split(",") if e.strip()]
        return ", ".join(emails) if emails else None
    elif isinstance(val, list):
        emails = [str(e).strip() for e in val if str(e).strip()]
        return ", ".join(emails) if emails else None
    return None

class EmailService:
    async def send_templated_email(
        self,
        template_slug: str,
        to_email: str,
        variables: dict,
        to_name: Optional[str] = None,
        cc: Optional[Union[List[str], str]] = None,
        bcc: Optional[Union[List[str], str]] = None,
        app_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        template = await template_service.get_template_by_slug(template_slug)
        if not template:
            raise ValueError(f"Template with slug '{template_slug}' not found.")

        rendered = template_service.render_template(template, variables)
        
        return await self._send_and_log(
            to_email=to_email,
            to_name=to_name,
            cc=cc,
            bcc=bcc,
            subject=rendered["subject"],
            html_body=rendered["html_body"],
            text_body=rendered["text_body"],
            app_id=app_id,
            template_id=template["id"],
            metadata=metadata or {}
        )

    async def send_raw_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: Optional[str] = "",
        to_name: Optional[str] = None,
        cc: Optional[Union[List[str], str]] = None,
        bcc: Optional[Union[List[str], str]] = None,
        app_id: Optional[str] = None,
        metadata: Optional[dict] = None
    ) -> dict:
        return await self._send_and_log(
            to_email=to_email,
            to_name=to_name,
            cc=cc,
            bcc=bcc,
            subject=subject,
            html_body=html_body,
            text_body=text_body or "",
            app_id=app_id,
            template_id=None,
            metadata=metadata or {}
        )

    async def _send_and_log(
        self,
        to_email: str,
        to_name: Optional[str],
        subject: str,
        html_body: str,
        text_body: str,
        app_id: Optional[str],
        template_id: Optional[str],
        metadata: dict,
        cc: Optional[Union[List[str], str]] = None,
        bcc: Optional[Union[List[str], str]] = None,
    ) -> dict:
        log_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()

        cc_str = _normalize_recipients(cc)
        bcc_str = _normalize_recipients(bcc)

        smtp_config = None
        if app_id:
            app_record = await application_service.get_application_by_id(app_id)
            if app_record and app_record.get("smtp_config_id"):
                smtp_config = await smtp_service.get_smtp_config(app_record["smtp_config_id"], include_decrypted_password=True)

        if not smtp_config:
            smtp_config = await smtp_service.get_default_smtp_config(include_decrypted_password=True)

        if not smtp_config:
            error_msg = "No active SMTP configuration found in dashboard settings."
            await self._create_log(log_id, app_id, template_id, None, to_email, to_name, cc_str, bcc_str, subject, "failed", error_msg, metadata, now)
            raise RuntimeError(error_msg)

        msg = EmailMessage()
        msg["From"] = f"{smtp_config['from_name']} <{smtp_config['from_email']}>"
        recipient_header = f"{to_name} <{to_email}>" if to_name else to_email
        msg["To"] = recipient_header
        if cc_str:
            msg["Cc"] = cc_str
        if bcc_str:
            msg["Bcc"] = bcc_str
        msg["Subject"] = subject
        
        if text_body:
            msg.set_content(text_body)
            msg.add_alternative(html_body, subtype="html")
        else:
            msg.set_content(html_body, subtype="html")

        status = "sent"
        error_message = None
        sent_at = now

        try:
            smtp = aiosmtplib.SMTP(
                hostname=smtp_config["host"],
                port=smtp_config["port"],
                use_tls=smtp_config["use_ssl"],
                start_tls=smtp_config["use_tls"] if not smtp_config["use_ssl"] else False,
                timeout=15
            )
            await smtp.connect()
            await smtp.login(smtp_config["username"], smtp_config["plain_password"])
            await smtp.send_message(msg)
            await smtp.quit()
        except Exception as e:
            status = "failed"
            error_message = str(e)
            logger.error(f"Email delivery error: {error_message}")

        await self._create_log(
            log_id, app_id, template_id, smtp_config["id"],
            to_email, to_name, cc_str, bcc_str, subject, status, error_message, metadata, now, sent_at if status == "sent" else None
        )

        return {
            "status": status,
            "log_id": log_id,
            "recipient": to_email,
            "message": "Email sent successfully" if status == "sent" else f"Email failed: {error_message}"
        }

    async def _create_log(
        self, log_id, app_id, template_id, smtp_config_id,
        recipient_email, recipient_name, cc, bcc, subject, status, error_message, metadata, created_at, sent_at=None
    ):
        async with db_helper.get_db_connection() as db:
            await db.execute("""
            INSERT INTO email_logs (
                id, app_id, template_id, smtp_config_id, recipient_email, recipient_name,
                cc, bcc, subject, status, error_message, metadata, sent_at, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                log_id, app_id, template_id, smtp_config_id,
                recipient_email, recipient_name, cc, bcc,
                subject, status, error_message,
                json.dumps(metadata), sent_at, created_at
            ))
            await db.commit()

    async def list_logs(
        self,
        app_id: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[dict]:
        async with db_helper.get_db_connection() as db:
            query = """
            SELECT 
                el.*,
                a.name AS app_name,
                a.api_key AS api_key,
                s.name AS smtp_name,
                s.from_email AS smtp_from_email,
                t.name AS template_name
            FROM email_logs el
            LEFT JOIN applications a ON el.app_id = a.id
            LEFT JOIN smtp_configs s ON el.smtp_config_id = s.id
            LEFT JOIN email_templates t ON el.template_id = t.id
            WHERE 1=1
            """
            params = []

            if app_id:
                query += " AND el.app_id = ?"
                params.append(app_id)

            if status:
                query += " AND el.status = ?"
                params.append(status)

            if search:
                query += " AND (el.recipient_email LIKE ? OR el.subject LIKE ? OR a.name LIKE ? OR a.api_key LIKE ? OR el.cc LIKE ? OR el.bcc LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term, search_term, search_term, search_term])

            query += " ORDER BY el.created_at DESC LIMIT ? OFFSET ?"
            params.extend([limit, offset])

            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            result = []
            for row in rows:
                d = dict(row)
                try:
                    d["metadata"] = json.loads(d["metadata"]) if isinstance(d["metadata"], str) else {}
                except Exception:
                    d["metadata"] = {}
                if not d.get("app_name"):
                    d["app_name"] = "Dashboard Direct" if not d.get("app_id") else "External App"
                result.append(d)
            return result

    async def get_log_stats(self) -> dict:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT COUNT(*) as total FROM email_logs")
            total = (await cursor.fetchone())["total"]

            cursor = await db.execute("SELECT COUNT(*) as sent FROM email_logs WHERE status = 'sent'")
            sent = (await cursor.fetchone())["sent"]

            cursor = await db.execute("SELECT COUNT(*) as failed FROM email_logs WHERE status = 'failed'")
            failed = (await cursor.fetchone())["failed"]

            # Today stats
            today_start = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d 00:00:00")
            cursor = await db.execute("SELECT COUNT(*) as today FROM email_logs WHERE created_at >= ?", (today_start,))
            today = (await cursor.fetchone())["today"]

            return {
                "total_emails": total,
                "total_sent": sent,
                "total_failed": failed,
                "sent_today": today,
                "success_rate": round((sent / total * 100), 1) if total > 0 else 100.0
            }

email_service = EmailService()

import json
import re
import uuid
import datetime
from typing import Optional, List, Dict, Any
from jinja2 import Template as JinjaTemplate
from app.db.database import db_helper

class TemplateService:
    def extract_variables(self, text: str) -> List[str]:
        """Extract {{variable_name}} placeholders from text."""
        if not text:
            return []
        matches = re.findall(r"\{\{\s*([a-zA-Z0-9_]+)\s*\}\}", text)
        return list(dict.fromkeys(matches))  # remove duplicates while preserving order

    async def create_template(self, data: dict, created_by: str = "admin") -> dict:
        template_id = str(uuid.uuid4())
        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Combine variables from subject, html_body, and explicit variables array
        extracted = self.extract_variables(data.get("subject", "")) + self.extract_variables(data.get("html_body", ""))
        provided_vars = data.get("variables", [])
        all_vars = list(dict.fromkeys(extracted + provided_vars))

        async with db_helper.get_db_connection() as db:
            await db.execute("""
            INSERT INTO email_templates (
                id, name, slug, subject, html_body, text_body, category,
                variables, is_builtin, is_active, created_by, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?, ?)
            """, (
                template_id,
                data["name"],
                data["slug"],
                data["subject"],
                data["html_body"],
                data.get("text_body", ""),
                data.get("category", "transactional"),
                json.dumps(all_vars),
                created_by,
                now,
                now
            ))
            await db.commit()

        return await self.get_template_by_id(template_id)

    async def get_template_by_id(self, template_id: str) -> Optional[dict]:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM email_templates WHERE id = ?", (template_id,))
            row = await cursor.fetchone()
            if not row:
                return None
            return self._format_row(row)

    async def get_template_by_slug(self, slug: str) -> Optional[dict]:
        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("SELECT * FROM email_templates WHERE slug = ? AND is_active = 1", (slug,))
            row = await cursor.fetchone()
            if not row:
                return None
            return self._format_row(row)

    async def list_templates(self, category: Optional[str] = None, search: Optional[str] = None) -> List[dict]:
        async with db_helper.get_db_connection() as db:
            query = "SELECT * FROM email_templates WHERE 1=1"
            params = []

            if category:
                query += " AND category = ?"
                params.append(category)

            if search:
                query += " AND (name LIKE ? OR slug LIKE ? OR subject LIKE ?)"
                search_term = f"%{search}%"
                params.extend([search_term, search_term, search_term])

            query += " ORDER BY created_at DESC"
            cursor = await db.execute(query, params)
            rows = await cursor.fetchall()
            return [self._format_row(row) for row in rows]

    async def update_template(self, template_id: str, updates: dict) -> Optional[dict]:
        existing = await self.get_template_by_id(template_id)
        if not existing:
            return None

        now = datetime.datetime.now(datetime.timezone.utc).isoformat()
        
        # Recalculate variables if content updated
        html = updates.get("html_body", existing["html_body"])
        subj = updates.get("subject", existing["subject"])
        extracted = self.extract_variables(subj) + self.extract_variables(html)
        provided = updates.get("variables", existing["variables"])
        all_vars = list(dict.fromkeys(extracted + provided))

        async with db_helper.get_db_connection() as db:
            fields = []
            values = []
            for k, v in updates.items():
                if v is not None and k not in ["variables"]:
                    if k in ["is_active"]:
                        fields.append(f"{k} = ?")
                        values.append(1 if v else 0)
                    else:
                        fields.append(f"{k} = ?")
                        values.append(v)
            
            fields.append("variables = ?")
            values.append(json.dumps(all_vars))
            fields.append("updated_at = ?")
            values.append(now)
            values.append(template_id)

            sql = f"UPDATE email_templates SET {', '.join(fields)} WHERE id = ?"
            await db.execute(sql, values)
            await db.commit()

        return await self.get_template_by_id(template_id)

    async def delete_template(self, template_id: str) -> bool:
        template = await self.get_template_by_id(template_id)
        if not template:
            return False
        if template.get("is_builtin"):
            raise ValueError("Built-in system templates cannot be deleted")

        async with db_helper.get_db_connection() as db:
            cursor = await db.execute("DELETE FROM email_templates WHERE id = ?", (template_id,))
            await db.commit()
            return cursor.rowcount > 0

    def render_template(self, template: dict, variables: dict) -> dict:
        """Render subject, html_body, text_body with provided variables."""
        subject_tmpl = JinjaTemplate(template["subject"])
        html_tmpl = JinjaTemplate(template["html_body"])
        text_tmpl = JinjaTemplate(template.get("text_body", ""))

        rendered_subject = subject_tmpl.render(**variables)
        rendered_html = html_tmpl.render(**variables)
        rendered_text = text_tmpl.render(**variables)

        # Check for unfulfilled variables
        required_vars = template.get("variables", [])
        missing_vars = [v for v in required_vars if v not in variables]

        return {
            "subject": rendered_subject,
            "html_body": rendered_html,
            "text_body": rendered_text,
            "missing_variables": missing_vars
        }

    def _format_row(self, row) -> dict:
        d = dict(row)
        d["is_builtin"] = bool(d["is_builtin"])
        d["is_active"] = bool(d["is_active"])
        try:
            d["variables"] = json.loads(d["variables"]) if isinstance(d["variables"], str) else d["variables"]
        except Exception:
            d["variables"] = []
        return d

template_service = TemplateService()

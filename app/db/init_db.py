import json
import uuid
from datetime import datetime, timezone
from app.db.database import db_helper

BUILTIN_TEMPLATES = [
    {
        "id": str(uuid.uuid4()),
        "name": "OTP Verification",
        "slug": "otp-verification",
        "subject": "Your OTP Code: {{otp_code}}",
        "category": "otp",
        "variables": json.dumps(["otp_code", "expiry_minutes", "app_name"]),
        "is_builtin": True,
        "is_active": True,
        "created_by": "system",
        "html_body": """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
    .header { background: linear-gradient(135deg, #4f46e5, #3b82f6); padding: 30px; text-align: center; color: white; }
    .header h1 { margin: 0; font-size: 24px; font-weight: 700; }
    .content { padding: 40px 30px; text-align: center; color: #374151; }
    .otp-card { background: #f0fdf4; border: 2px dashed #22c55e; border-radius: 10px; padding: 20px; margin: 25px 0; display: inline-block; width: 80%; }
    .otp-code { font-size: 36px; font-weight: 800; letter-spacing: 8px; color: #15803d; margin: 10px 0; font-family: monospace; }
    .expiry { font-size: 14px; color: #6b7280; margin-top: 10px; }
    .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #9ca3af; border-top: 1px solid #f3f4f6; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1>{{app_name}}</h1>
    </div>
    <div class="content">
      <h2>Email Verification Code</h2>
      <p>Use the code below to complete your authentication process.</p>
      <div class="otp-card">
        <div class="otp-code">{{otp_code}}</div>
        <div class="expiry">Expires in <strong>{{expiry_minutes}} minutes</strong></div>
      </div>
      <p style="font-size: 13px; color: #9ca3af;">If you did not request this verification code, please ignore this email.</p>
    </div>
    <div class="footer">
      &copy; {{app_name}}. Sent via Email Gateway.
    </div>
  </div>
</body>
</html>""",
        "text_body": "Your {{app_name}} verification code is: {{otp_code}}. It expires in {{expiry_minutes}} minutes."
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Welcome Email",
        "slug": "welcome-email",
        "subject": "Welcome to {{app_name}}, {{user_name}}!",
        "category": "transactional",
        "variables": json.dumps(["user_name", "app_name", "login_url"]),
        "is_builtin": True,
        "is_active": True,
        "created_by": "system",
        "html_body": """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: 'Segoe UI', sans-serif; background: #f3f4f6; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 40px auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); }
    .header { background: #1e1b4b; padding: 35px; text-align: center; color: #ffffff; }
    .content { padding: 40px 30px; color: #1f2937; line-height: 1.6; }
    .btn { display: inline-block; background: #4f46e5; color: #ffffff !important; padding: 14px 28px; border-radius: 8px; font-weight: 600; text-decoration: none; margin-top: 20px; }
    .footer { background: #f9fafb; padding: 20px; text-align: center; font-size: 12px; color: #6b7280; }
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <h1 style="margin:0;">Welcome Aboard! 🎉</h1>
    </div>
    <div class="content">
      <h2>Hi {{user_name}},</h2>
      <p>Thank you for joining <strong>{{app_name}}</strong>. We are thrilled to have you with us!</p>
      <p>Get started right away by accessing your portal below:</p>
      <div style="text-align: center;">
        <a href="{{login_url}}" class="btn">Go to Dashboard</a>
      </div>
    </div>
    <div class="footer">
      &copy; {{app_name}}. Powered by Email Gateway.
    </div>
  </div>
</body>
</html>""",
        "text_body": "Welcome {{user_name}} to {{app_name}}! Access your account here: {{login_url}}"
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Password Reset",
        "slug": "password-reset",
        "subject": "Reset your password for {{app_name}}",
        "category": "transactional",
        "variables": json.dumps(["user_name", "reset_link", "expiry_minutes", "app_name"]),
        "is_builtin": True,
        "is_active": True,
        "created_by": "system",
        "html_body": """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: sans-serif; background: #f8fafc; margin: 0; padding: 0; }
    .container { max-width: 600px; margin: 40px auto; background: #fff; border-radius: 12px; padding: 30px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }
    .btn { display: inline-block; background: #dc2626; color: #ffffff !important; padding: 12px 24px; border-radius: 6px; font-weight: 600; text-decoration: none; margin: 20px 0; }
  </style>
</head>
<body>
  <div class="container">
    <h2>Password Reset Request</h2>
    <p>Hello {{user_name}},</p>
    <p>We received a request to reset your password for <strong>{{app_name}}</strong>. Click the button below to proceed:</p>
    <div style="text-align: center;">
      <a href="{{reset_link}}" class="btn">Reset Password</a>
    </div>
    <p style="font-size: 13px; color: #64748b;">This link will expire in {{expiry_minutes}} minutes. If you did not request this, please secure your account immediately.</p>
  </div>
</body>
</html>""",
        "text_body": "Hi {{user_name}}, reset your {{app_name}} password using this link: {{reset_link}} (expires in {{expiry_minutes}} mins)."
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Order Confirmation",
        "slug": "order-confirmation",
        "subject": "Order #{{order_id}} Confirmed!",
        "category": "transactional",
        "variables": json.dumps(["user_name", "order_id", "order_total", "order_items"]),
        "is_builtin": True,
        "is_active": True,
        "created_by": "system",
        "html_body": """<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <style>
    body { font-family: sans-serif; background: #f9fafb; margin: 0; padding: 20px; }
    .box { max-width: 600px; margin: 0 auto; background: #fff; border-radius: 12px; padding: 30px; border: 1px solid #e5e7eb; }
    .badge { background: #dcfce7; color: #166534; padding: 6px 12px; border-radius: 20px; font-size: 14px; font-weight: 600; }
  </style>
</head>
<body>
  <div class="box">
    <div style="display:flex; justify-content:space-between; align-items:center;">
      <h2 style="margin:0;">Order Receipt</h2>
      <span class="badge">CONFIRMED</span>
    </div>
    <p>Hi {{user_name}}, thank you for your order!</p>
    <p><strong>Order ID:</strong> #{{order_id}}</p>
    <p><strong>Details:</strong> {{order_items}}</p>
    <hr style="border: none; border-top: 1px solid #e5e7eb; margin: 20px 0;">
    <h3 style="text-align: right; color: #111827;">Total Paid: {{order_total}}</h3>
  </div>
</body>
</html>""",
        "text_body": "Hi {{user_name}}, order #{{order_id}} confirmed for total {{order_total}}."
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Payment Receipt",
        "slug": "payment-receipt",
        "subject": "Payment Receipt for {{amount}}",
        "category": "transactional",
        "variables": json.dumps(["user_name", "amount", "transaction_id", "date"]),
        "is_builtin": True,
        "is_active": True,
        "created_by": "system",
        "html_body": """<!DOCTYPE html>
<html>
<body>
  <div style="font-family: sans-serif; max-width: 500px; margin: 30px auto; padding: 25px; border: 1px solid #e2e8f0; border-radius: 10px;">
    <h2 style="color: #047857;">Payment Successful</h2>
    <p>Dear {{user_name}},</p>
    <p>We received your payment of <strong>{{amount}}</strong>.</p>
    <ul style="background: #f8fafc; padding: 15px 30px; border-radius: 6px; list-style: none;">
      <li><strong>Transaction ID:</strong> {{transaction_id}}</li>
      <li><strong>Date:</strong> {{date}}</li>
    </ul>
    <p>Thank you!</p>
  </div>
</body>
</html>""",
        "text_body": "Payment Receipt: {{user_name}}, payment of {{amount}} received. Txn: {{transaction_id}} on {{date}}."
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Account Deactivation",
        "slug": "account-deactivation",
        "subject": "Account Deactivation Notice",
        "category": "notification",
        "variables": json.dumps(["user_name", "reason", "support_email"]),
        "is_builtin": True,
        "is_active": True,
        "created_by": "system",
        "html_body": """<!DOCTYPE html>
<html>
<body>
  <div style="font-family: sans-serif; max-width: 500px; margin: 30px auto; padding: 25px; border: 1px solid #fee2e2; background: #fff5f5; border-radius: 10px;">
    <h2 style="color: #b91c1c;">Account Deactivated</h2>
    <p>Hello {{user_name}},</p>
    <p>Your account has been deactivated. Reason: {{reason}}.</p>
    <p>If you believe this is an error, please contact support at {{support_email}}.</p>
  </div>
</body>
</html>""",
        "text_body": "Hi {{user_name}}, your account was deactivated due to: {{reason}}. Contact: {{support_email}}"
    },
    {
        "id": str(uuid.uuid4()),
        "name": "Generic Notification",
        "slug": "generic-notification",
        "subject": "{{title}}",
        "category": "notification",
        "variables": json.dumps(["title", "message", "action_url", "action_text"]),
        "is_builtin": True,
        "is_active": True,
        "created_by": "system",
        "html_body": """<!DOCTYPE html>
<html>
<body>
  <div style="font-family: sans-serif; max-width: 600px; margin: 30px auto; padding: 30px; border: 1px solid #e5e7eb; border-radius: 10px;">
    <h2 style="color: #1f2937; margin-top: 0;">{{title}}</h2>
    <p style="color: #4b5563; line-height: 1.6;">{{message}}</p>
    <div style="margin-top: 25px;">
      <a href="{{action_url}}" style="background: #2563eb; color: #fff; padding: 10px 20px; border-radius: 6px; text-decoration: none;">{{action_text}}</a>
    </div>
  </div>
</body>
</html>""",
        "text_body": "{{title}}\n\n{{message}}\n\nLink: {{action_url}}"
    }
]

async def init_db():
    async with db_helper.get_db_connection() as db:
        # 1. smtp_configs table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS smtp_configs (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL DEFAULT 587,
            username TEXT NOT NULL,
            password TEXT NOT NULL,
            from_email TEXT NOT NULL,
            from_name TEXT NOT NULL DEFAULT 'Email Portal',
            use_tls BOOLEAN NOT NULL DEFAULT 1,
            use_ssl BOOLEAN NOT NULL DEFAULT 0,
            is_default BOOLEAN NOT NULL DEFAULT 0,
            is_active BOOLEAN NOT NULL DEFAULT 1,
            last_tested_at TIMESTAMP,
            test_status TEXT DEFAULT 'untested',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. applications table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS applications (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            api_key TEXT UNIQUE NOT NULL,
            api_secret TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'active',
            allowed_domains TEXT DEFAULT '["*"]',
            rate_limit INTEGER DEFAULT 50,
            smtp_config_id TEXT REFERENCES smtp_configs(id),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 3. email_templates table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS email_templates (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            subject TEXT NOT NULL,
            html_body TEXT NOT NULL,
            text_body TEXT NOT NULL,
            category TEXT NOT NULL DEFAULT 'transactional',
            variables TEXT DEFAULT '[]',
            is_builtin BOOLEAN DEFAULT 0,
            is_active BOOLEAN DEFAULT 1,
            created_by TEXT DEFAULT 'admin',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 4. email_logs table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS email_logs (
            id TEXT PRIMARY KEY,
            app_id TEXT,
            template_id TEXT,
            smtp_config_id TEXT,
            recipient_email TEXT NOT NULL,
            recipient_name TEXT,
            subject TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'queued',
            error_message TEXT,
            metadata TEXT DEFAULT '{}',
            sent_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE SET NULL,
            FOREIGN KEY (template_id) REFERENCES email_templates(id) ON DELETE SET NULL
        );
        """)

        # 5. otp_records table
        await db.execute("""
        CREATE TABLE IF NOT EXISTS otp_records (
            id TEXT PRIMARY KEY,
            app_id TEXT,
            identifier TEXT NOT NULL,
            otp_code TEXT NOT NULL,
            purpose TEXT NOT NULL DEFAULT 'login',
            attempts INTEGER DEFAULT 0,
            max_attempts INTEGER DEFAULT 3,
            is_verified BOOLEAN DEFAULT 0,
            expires_at TIMESTAMP NOT NULL,
            verified_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (app_id) REFERENCES applications(id) ON DELETE SET NULL
        );
        """)

        await db.commit()

        # Seed built-in templates if not existing
        for template in BUILTIN_TEMPLATES:
            cursor = await db.execute("SELECT id FROM email_templates WHERE slug = ?", (template["slug"],))
            row = await cursor.fetchone()
            if not row:
                now = datetime.now(timezone.utc).isoformat()
                await db.execute("""
                INSERT INTO email_templates (id, name, slug, subject, html_body, text_body, category, variables, is_builtin, is_active, created_by, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    template["id"],
                    template["name"],
                    template["slug"],
                    template["subject"],
                    template["html_body"],
                    template["text_body"],
                    template["category"],
                    template["variables"],
                    1 if template["is_builtin"] else 0,
                    1 if template["is_active"] else 0,
                    template["created_by"],
                    now,
                    now
                ))
        await db.commit()

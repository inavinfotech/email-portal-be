import datetime
from sqlalchemy import Column, String, Integer, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class SMTPConfig(Base):
    __tablename__ = "smtp_configs"

    id = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    host = Column(String, nullable=False)
    port = Column(Integer, nullable=False, default=587)
    username = Column(String, nullable=False)
    password = Column(String, nullable=False)
    from_email = Column(String, nullable=False)
    from_name = Column(String, nullable=False, default="Email Portal")
    use_tls = Column(Boolean, nullable=False, default=True)
    use_ssl = Column(Boolean, nullable=False, default=False)
    is_default = Column(Boolean, nullable=False, default=False)
    is_active = Column(Boolean, nullable=False, default=True)
    last_tested_at = Column(DateTime, nullable=True)
    test_status = Column(String, default="untested")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class Application(Base):
    __tablename__ = "applications"

    id = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    api_key = Column(String, unique=True, nullable=False)
    api_secret = Column(String, nullable=False)
    status = Column(String, nullable=False, default="active")
    allowed_domains = Column(Text, default='["*"]')
    rate_limit = Column(Integer, default=50)
    smtp_config_id = Column(String, ForeignKey("smtp_configs.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    smtp_config = relationship("SMTPConfig", backref="applications")


class EmailTemplate(Base):
    __tablename__ = "email_templates"

    id = Column(String, primary_key=True, nullable=False)
    name = Column(String, nullable=False)
    slug = Column(String, unique=True, nullable=False)
    subject = Column(String, nullable=False)
    html_body = Column(Text, nullable=False)
    text_body = Column(Text, nullable=False)
    category = Column(String, nullable=False, default="transactional")
    variables = Column(Text, default="[]")
    is_builtin = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_by = Column(String, default="admin")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)


class EmailLog(Base):
    __tablename__ = "email_logs"

    id = Column(String, primary_key=True, nullable=False)
    app_id = Column(String, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    template_id = Column(String, ForeignKey("email_templates.id", ondelete="SET NULL"), nullable=True)
    smtp_config_id = Column(String, nullable=True)
    recipient_email = Column(String, nullable=False)
    recipient_name = Column(String, nullable=True)
    cc = Column(Text, nullable=True)
    bcc = Column(Text, nullable=True)
    subject = Column(String, nullable=False)
    status = Column(String, nullable=False, default="queued")
    error_message = Column(Text, nullable=True)
    metadata_ = Column("metadata", Text, default="{}")
    sent_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("Application", backref="email_logs")
    template = relationship("EmailTemplate", backref="email_logs")


class OTPRecord(Base):
    __tablename__ = "otp_records"

    id = Column(String, primary_key=True, nullable=False)
    app_id = Column(String, ForeignKey("applications.id", ondelete="SET NULL"), nullable=True)
    identifier = Column(String, nullable=False)
    otp_code = Column(String, nullable=False)
    purpose = Column(String, nullable=False, default="login")
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    is_verified = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    verified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    application = relationship("Application", backref="otp_records")

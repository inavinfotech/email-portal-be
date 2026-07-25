from pydantic import BaseModel, EmailStr
from typing import Optional

class SMTPConfigCreate(BaseModel):
    name: str
    host: str
    port: int = 587
    username: str
    password: str
    from_email: EmailStr
    from_name: str = "Email Portal"
    use_tls: bool = True
    use_ssl: bool = False
    is_default: bool = False

class SMTPConfigUpdate(BaseModel):
    name: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    from_email: Optional[EmailStr] = None
    from_name: Optional[str] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None

class SMTPConfigResponse(BaseModel):
    id: str
    name: str
    host: str
    port: int
    username: str
    from_email: str
    from_name: str
    use_tls: bool
    use_ssl: bool
    is_default: bool
    is_active: bool
    last_tested_at: Optional[str] = None
    test_status: str
    created_at: str
    updated_at: str

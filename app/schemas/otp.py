from pydantic import BaseModel, EmailStr
from typing import Optional, Union, List

class OTPGenerateRequest(BaseModel):
    identifier: EmailStr
    purpose: str = "login"
    template_slug: str = "otp-verification"
    app_name: Optional[str] = "Example App"
    otp_code: Optional[str] = None
    custom_otp_code: Optional[str] = None
    cc: Optional[Union[List[str], str]] = None
    bcc: Optional[Union[List[str], str]] = None


class OTPGenerateResponse(BaseModel):
    otp_id: str
    masked_identifier: str
    expires_at: str
    purpose: str
    status: str

class OTPVerifyRequest(BaseModel):
    identifier: EmailStr
    otp_code: str
    purpose: str = "login"

class OTPVerifyResponse(BaseModel):
    verified: bool
    otp_id: str
    identifier: str
    purpose: str
    message: str

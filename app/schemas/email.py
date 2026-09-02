from pydantic import BaseModel, EmailStr
from typing import Dict, Any, Optional, List, Union

class SendTemplatedEmailRequest(BaseModel):
    template_slug: str
    to_email: EmailStr
    to_name: Optional[str] = None
    cc: Optional[Union[List[str], str]] = None
    bcc: Optional[Union[List[str], str]] = None
    variables: Dict[str, Any] = {}
    metadata: Optional[Dict[str, Any]] = {}

class SendRawEmailRequest(BaseModel):
    to_email: EmailStr
    to_name: Optional[str] = None
    cc: Optional[Union[List[str], str]] = None
    bcc: Optional[Union[List[str], str]] = None
    subject: str
    html_body: str
    text_body: Optional[str] = ""
    metadata: Optional[Dict[str, Any]] = {}

class BulkRecipient(BaseModel):
    to_email: EmailStr
    to_name: Optional[str] = None
    cc: Optional[Union[List[str], str]] = None
    bcc: Optional[Union[List[str], str]] = None
    variables: Dict[str, Any] = {}

class SendBulkEmailRequest(BaseModel):
    template_slug: str
    recipients: List[BulkRecipient]
    metadata: Optional[Dict[str, Any]] = {}

class EmailSendResponse(BaseModel):
    status: str
    log_id: str
    recipient: str
    message: str

class EmailLogResponse(BaseModel):
    id: str
    app_id: Optional[str] = None
    app_name: Optional[str] = None
    api_key: Optional[str] = None
    template_id: Optional[str] = None
    template_name: Optional[str] = None
    smtp_config_id: Optional[str] = None
    smtp_name: Optional[str] = None
    smtp_from_email: Optional[str] = None
    recipient_email: str
    recipient_name: Optional[str] = None
    cc: Optional[str] = None
    bcc: Optional[str] = None
    subject: str
    status: str
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = {}
    sent_at: Optional[str] = None
    created_at: str


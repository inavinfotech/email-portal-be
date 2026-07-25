from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ApplicationCreate(BaseModel):
    name: str
    allowed_domains: Optional[List[str]] = ["*"]
    rate_limit: Optional[int] = 50
    smtp_config_id: Optional[str] = None

class ApplicationUpdate(BaseModel):
    name: Optional[str] = None
    status: Optional[str] = None
    allowed_domains: Optional[List[str]] = None
    rate_limit: Optional[int] = None
    smtp_config_id: Optional[str] = None

class ApplicationResponse(BaseModel):
    id: str
    name: str
    api_key: str
    api_secret: Optional[str] = None
    status: str
    allowed_domains: List[str]
    rate_limit: int
    smtp_config_id: Optional[str] = None
    created_at: str
    updated_at: str

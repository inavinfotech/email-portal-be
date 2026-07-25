from pydantic import BaseModel
from typing import List, Optional, Dict, Any

class TemplateCreate(BaseModel):
    name: str
    slug: str
    subject: str
    html_body: str
    text_body: Optional[str] = ""
    category: str = "transactional"
    variables: Optional[List[str]] = []

class TemplateUpdate(BaseModel):
    name: Optional[str] = None
    subject: Optional[str] = None
    html_body: Optional[str] = None
    text_body: Optional[str] = None
    category: Optional[str] = None
    variables: Optional[List[str]] = None
    is_active: Optional[bool] = None

class TemplatePreviewRequest(BaseModel):
    variables: Dict[str, Any]

class TemplatePreviewResponse(BaseModel):
    subject: str
    html_body: str
    text_body: str
    missing_variables: List[str]

class TemplateResponse(BaseModel):
    id: str
    name: str
    slug: str
    subject: str
    html_body: str
    text_body: str
    category: str
    variables: List[str]
    is_builtin: bool
    is_active: bool
    created_by: str
    created_at: str
    updated_at: str

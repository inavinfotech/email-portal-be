from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from app.schemas.email import EmailLogResponse
from app.services.email_service import email_service
from app.auth.deps import get_authenticated_user

router = APIRouter(prefix="/logs", tags=["Email Logs"])

@router.get("", response_model=List[EmailLogResponse])
async def list_logs(
    app_id: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: dict = Depends(get_authenticated_user)
):
    return await email_service.list_logs(app_id=app_id, status=status, search=search, limit=limit, offset=offset)

@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_authenticated_user)):
    return await email_service.get_log_stats()

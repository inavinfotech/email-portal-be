from fastapi import APIRouter, Depends, HTTPException, status
from typing import List, Optional
from pydantic import EmailStr
from app.schemas.smtp import SMTPConfigCreate, SMTPConfigUpdate, SMTPConfigResponse
from app.services.smtp_service import smtp_service
from app.auth.deps import get_authenticated_user

router = APIRouter(prefix="/smtp", tags=["SMTP Settings"])

@router.post("", response_model=SMTPConfigResponse, status_code=status.HTTP_201_CREATED)
async def create_smtp(smtp_in: SMTPConfigCreate, current_user: dict = Depends(get_authenticated_user)):
    return await smtp_service.create_smtp_config(smtp_in.model_dump())

@router.get("", response_model=List[SMTPConfigResponse])
async def list_smtps(current_user: dict = Depends(get_authenticated_user)):
    return await smtp_service.list_smtp_configs()

@router.get("/{config_id}", response_model=SMTPConfigResponse)
async def get_smtp(config_id: str, current_user: dict = Depends(get_authenticated_user)):
    config = await smtp_service.get_smtp_config(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="SMTP configuration not found")
    return config

@router.put("/{config_id}", response_model=SMTPConfigResponse)
async def update_smtp(config_id: str, smtp_in: SMTPConfigUpdate, current_user: dict = Depends(get_authenticated_user)):
    updated = await smtp_service.update_smtp_config(config_id, smtp_in.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="SMTP configuration not found")
    return updated

@router.delete("/{config_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_smtp(config_id: str, current_user: dict = Depends(get_authenticated_user)):
    success = await smtp_service.delete_smtp_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="SMTP configuration not found")
    return None

@router.post("/{config_id}/test")
async def test_smtp(
    config_id: str,
    recipient_email: Optional[EmailStr] = None,
    current_user: dict = Depends(get_authenticated_user)
):
    result = await smtp_service.test_smtp_connection(config_id, test_recipient=recipient_email)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["message"])
    return result

@router.post("/{config_id}/set-default", response_model=SMTPConfigResponse)
async def set_default_smtp(config_id: str, current_user: dict = Depends(get_authenticated_user)):
    updated = await smtp_service.update_smtp_config(config_id, {"is_default": True})
    if not updated:
        raise HTTPException(status_code=404, detail="SMTP configuration not found")
    return updated

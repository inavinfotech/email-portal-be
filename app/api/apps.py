from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from app.schemas.application import ApplicationCreate, ApplicationUpdate, ApplicationResponse
from app.services.application_service import application_service
from app.auth.deps import get_authenticated_user

router = APIRouter(prefix="/apps", tags=["Applications"])

@router.post("", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
async def create_app(app_in: ApplicationCreate, current_user: dict = Depends(get_authenticated_user)):
    db_app, plain_secret = await application_service.create_application(app_in.model_dump())
    response_data = dict(db_app)
    response_data["api_secret"] = plain_secret
    return response_data

@router.get("", response_model=List[ApplicationResponse])
async def list_apps(current_user: dict = Depends(get_authenticated_user)):
    return await application_service.list_applications()

@router.get("/{app_id}", response_model=ApplicationResponse)
async def get_app(app_id: str, current_user: dict = Depends(get_authenticated_user)):
    app_record = await application_service.get_application_by_id(app_id)
    if not app_record:
        raise HTTPException(status_code=404, detail="Application not found")
    return app_record

@router.put("/{app_id}", response_model=ApplicationResponse)
@router.patch("/{app_id}", response_model=ApplicationResponse)
async def update_app(app_id: str, app_in: ApplicationUpdate, current_user: dict = Depends(get_authenticated_user)):
    updated = await application_service.update_application(app_id, app_in.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Application not found")
    return updated

@router.delete("/{app_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_app(app_id: str, current_user: dict = Depends(get_authenticated_user)):
    success = await application_service.delete_application(app_id)
    if not success:
        raise HTTPException(status_code=404, detail="Application not found")
    return None

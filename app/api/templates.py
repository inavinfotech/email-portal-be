from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from app.schemas.template import TemplateCreate, TemplateUpdate, TemplateResponse, TemplatePreviewRequest, TemplatePreviewResponse
from app.services.template_service import template_service
from app.auth.deps import get_authenticated_user

router = APIRouter(prefix="/templates", tags=["Templates"])

@router.post("", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def create_template(template_in: TemplateCreate, current_user: dict = Depends(get_authenticated_user)):
    existing = await template_service.get_template_by_slug(template_in.slug)
    if existing:
        raise HTTPException(status_code=400, detail=f"Template slug '{template_in.slug}' already exists")
    
    return await template_service.create_template(template_in.model_dump(), created_by=current_user.get("email", "admin"))

@router.get("", response_model=List[TemplateResponse])
async def list_templates(
    category: Optional[str] = None,
    search: Optional[str] = None,
    current_user: dict = Depends(get_authenticated_user)
):
    return await template_service.list_templates(category=category, search=search)

@router.get("/{template_id}", response_model=TemplateResponse)
async def get_template(template_id: str, current_user: dict = Depends(get_authenticated_user)):
    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template

@router.put("/{template_id}", response_model=TemplateResponse)
async def update_template(template_id: str, template_in: TemplateUpdate, current_user: dict = Depends(get_authenticated_user)):
    updated = await template_service.update_template(template_id, template_in.model_dump(exclude_unset=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Template not found")
    return updated

@router.delete("/{template_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_template(template_id: str, current_user: dict = Depends(get_authenticated_user)):
    try:
        success = await template_service.delete_template(template_id)
        if not success:
            raise HTTPException(status_code=404, detail="Template not found")
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return None

@router.post("/{template_id}/preview", response_model=TemplatePreviewResponse)
async def preview_template(template_id: str, preview_in: TemplatePreviewRequest, current_user: dict = Depends(get_authenticated_user)):
    template = await template_service.get_template_by_id(template_id)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template_service.render_template(template, preview_in.variables)

@router.post("/{template_id}/duplicate", response_model=TemplateResponse, status_code=status.HTTP_201_CREATED)
async def duplicate_template(template_id: str, current_user: dict = Depends(get_authenticated_user)):
    source = await template_service.get_template_by_id(template_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source template not found")

    new_slug = f"{source['slug']}-copy"
    counter = 1
    while await template_service.get_template_by_slug(new_slug):
        new_slug = f"{source['slug']}-copy-{counter}"
        counter += 1

    new_data = {
        "name": f"{source['name']} (Copy)",
        "slug": new_slug,
        "subject": source["subject"],
        "html_body": source["html_body"],
        "text_body": source["text_body"],
        "category": source["category"],
        "variables": source["variables"]
    }
    return await template_service.create_template(new_data, created_by=current_user.get("email", "admin"))

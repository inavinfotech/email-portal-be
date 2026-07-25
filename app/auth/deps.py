from fastapi import Depends, HTTPException, Header, status
from typing import Optional
from app.core.config import settings

async def get_current_app(
    x_api_key: str = Header(None),
    x_api_secret: str = Header(None)
):
    if not x_api_key or not x_api_secret:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API Key and Secret are required"
        )
    
    from app.services.application_service import application_service
    app_record = await application_service.get_application_by_api_key(x_api_key)
    if not app_record:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key"
        )
    
    if app_record.get("status") != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Application is inactive"
        )
    
    from app.auth.security import verify_secret
    if not verify_secret(x_api_secret, app_record["api_secret"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Secret"
        )
    
    return app_record

async def verify_dashboard_auth(
    authorization: str = Header(None)
):
    if authorization == f"Bearer {settings.DASHBOARD_TOKEN}":
        return True
    
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Dashboard authentication required"
    )

async def get_authenticated_user(
    x_api_key: Optional[str] = Header(None),
    x_api_secret: Optional[str] = Header(None),
    authorization: Optional[str] = Header(None)
):
    import logging
    logger = logging.getLogger("uvicorn.error")

    # JWT auth first
    if authorization and authorization.startswith("Bearer "):
        parts = authorization.split()
        if len(parts) >= 2:
            token = parts[1]
            from app.auth.security import decode_access_token
            payload = decode_access_token(token)
            if payload:
                return {"type": "user", "email": payload.get("sub")}
            else:
                logger.warning(f"Invalid or expired JWT token: {token[:10]}...")

    # Static dashboard token auth
    if authorization == f"Bearer {settings.DASHBOARD_TOKEN}":
        return {"type": "user", "name": "admin"}

    # API key auth
    if x_api_key and x_api_secret:
        return await get_current_app(x_api_key, x_api_secret)

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Authentication required. Please provide valid credentials."
    )

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.otp import OTPGenerateRequest, OTPGenerateResponse, OTPVerifyRequest, OTPVerifyResponse
from app.services.otp_service import otp_service
from app.auth.deps import get_authenticated_user

router = APIRouter(prefix="/otp", tags=["OTP Service"])

@router.post("/generate", response_model=OTPGenerateResponse)
async def generate_otp(req: OTPGenerateRequest, current_client: dict = Depends(get_authenticated_user)):
    app_id = current_client.get("id") if current_client.get("type") != "user" else None
    app_name = current_client.get("name", req.app_name) if current_client.get("type") != "user" else req.app_name

    custom_code = req.otp_code or req.custom_otp_code
    res = await otp_service.generate_and_send_otp(
        identifier=req.identifier,
        purpose=req.purpose,
        template_slug=req.template_slug,
        app_id=app_id,
        app_name=app_name,
        custom_code=custom_code,
        cc=req.cc,
        bcc=req.bcc
    )
    return res

@router.post("/verify", response_model=OTPVerifyResponse)
async def verify_otp(req: OTPVerifyRequest, current_client: dict = Depends(get_authenticated_user)):
    res = await otp_service.verify_otp(
        identifier=req.identifier,
        otp_code=req.otp_code,
        purpose=req.purpose
    )
    return res

from fastapi import APIRouter, Depends, HTTPException, status
from app.schemas.email import SendTemplatedEmailRequest, SendRawEmailRequest, SendBulkEmailRequest, EmailSendResponse
from app.services.email_service import email_service
from app.auth.deps import get_authenticated_user

router = APIRouter(prefix="/send", tags=["Send Emails"])

@router.post("", response_model=EmailSendResponse)
async def send_templated_email(req: SendTemplatedEmailRequest, current_client: dict = Depends(get_authenticated_user)):
    app_id = current_client.get("id") if current_client.get("type") != "user" else None
    try:
        res = await email_service.send_templated_email(
            template_slug=req.template_slug,
            to_email=req.to_email,
            to_name=req.to_name,
            cc=req.cc,
            bcc=req.bcc,
            variables=req.variables,
            app_id=app_id,
            metadata=req.metadata
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/raw", response_model=EmailSendResponse)
async def send_raw_email(req: SendRawEmailRequest, current_client: dict = Depends(get_authenticated_user)):
    app_id = current_client.get("id") if current_client.get("type") != "user" else None
    try:
        res = await email_service.send_raw_email(
            to_email=req.to_email,
            to_name=req.to_name,
            cc=req.cc,
            bcc=req.bcc,
            subject=req.subject,
            html_body=req.html_body,
            text_body=req.text_body,
            app_id=app_id,
            metadata=req.metadata
        )
        return res
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/bulk")
async def send_bulk_emails(req: SendBulkEmailRequest, current_client: dict = Depends(get_authenticated_user)):
    app_id = current_client.get("id") if current_client.get("type") != "user" else None
    results = []
    for recipient in req.recipients:
        try:
            res = await email_service.send_templated_email(
                template_slug=req.template_slug,
                to_email=recipient.to_email,
                to_name=recipient.to_name,
                cc=recipient.cc,
                bcc=recipient.bcc,
                variables=recipient.variables,
                app_id=app_id,
                metadata=req.metadata
            )
            results.append(res)
        except Exception as e:
            results.append({"status": "failed", "recipient": recipient.to_email, "error": str(e)})

    return {"total": len(req.recipients), "results": results}


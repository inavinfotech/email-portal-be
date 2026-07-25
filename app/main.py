import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.middleware import StructuredLoggingMiddleware, RateLimitMiddleware
from app.core.exceptions import global_exception_handler, http_exception_handler
from app.db.init_db import init_db
from app.services.otp_service import otp_service

from app.api.auth import router as auth_router
from app.api.apps import router as apps_router
from app.api.smtp import router as smtp_router
from app.api.templates import router as templates_router
from app.api.send import router as send_router
from app.api.otp import router as otp_router
from app.api.logs import router as logs_router

logger = logging.getLogger("uvicorn.error")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize DB schema & seed templates
    await init_db()
    logger.info("Initialized Email Portal Database")

    # Background task for OTP cleanup
    async def otp_cleanup_loop():
        while True:
            await asyncio.sleep(600)  # Clean expired OTPs every 10 minutes
            try:
                await otp_service.cleanup_expired_otps()
            except Exception as e:
                logger.error(f"OTP cleanup error: {e}")

    task = asyncio.create_task(otp_cleanup_loop())
    yield
    task.cancel()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    debug=settings.DEBUG,
    lifespan=lifespan
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom Middlewares
app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(RateLimitMiddleware, limit=200, window=60)

# Exception Handlers
app.add_exception_handler(Exception, global_exception_handler)
app.add_exception_handler(HTTPException, http_exception_handler)

# Include Routers
app.include_router(auth_router, prefix=settings.API_V1_STR)
app.include_router(apps_router, prefix=settings.API_V1_STR)
app.include_router(smtp_router, prefix=settings.API_V1_STR)
app.include_router(templates_router, prefix=settings.API_V1_STR)
app.include_router(send_router, prefix=settings.API_V1_STR)
app.include_router(otp_router, prefix=settings.API_V1_STR)
app.include_router(logs_router, prefix=settings.API_V1_STR)

@app.get("/health")
async def health_check():
    from app.db.database import db_helper
    try:
        async with db_helper.get_db_connection() as db:
            await db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected", "service": settings.PROJECT_NAME}
    except Exception as e:
        return {"status": "unhealthy", "database": str(e)}, 503

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5005)

from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError
from app.core.config import settings

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

@app.on_event("startup")
def on_startup():
    try:
        from app.db.session import SessionLocal
        from app.models.subject import File, FileStatus, OCRStatus
        db = SessionLocal()
        try:
            stuck_files = db.query(File).filter(File.status == FileStatus.PROCESSING).all()
            for f in stuck_files:
                f.status = FileStatus.FAILED
                f.ocr_status = OCRStatus.FAILED
                f.error_message = "Server restarted during processing."
            db.commit()
            if stuck_files:
                print(f"Cleaned up {len(stuck_files)} files stuck in processing state.")
        except Exception as startup_err:
            print(f"Error resetting stuck files: {str(startup_err)}")
        finally:
            db.close()

        from app.db.seed import seed_db
        seed_db()
    except Exception as e:
        print(f"Failed to auto-seed database on startup: {str(e)}")

# CORS configuration
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Database Integrity Error handler (e.g. duplicate email registrations)
@app.exception_handler(IntegrityError)
async def integrity_exception_handler(request: Request, exc: IntegrityError):
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={"detail": "Database integrity constraint violation (e.g., unique key violation)."},
    )

# Root entrypoint
@app.get("/")
async def root():
    return {
        "message": f"Welcome to the {settings.PROJECT_NAME} API!",
        "docs_url": "/docs",
        "status": "healthy"
    }

from app.api.v1.api import api_router
app.include_router(api_router, prefix=settings.API_V1_STR)

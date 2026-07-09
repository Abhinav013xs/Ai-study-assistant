from fastapi import APIRouter
from app.api.v1.endpoints import auth, materials, chat, study_tools, quiz, planner, analytics

api_router = APIRouter()

# Include endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(materials.router, prefix="/materials", tags=["materials"])
api_router.include_router(chat.router, prefix="/chat", tags=["chat"])
api_router.include_router(study_tools.router, prefix="/study-tools", tags=["study-tools"])
api_router.include_router(quiz.router, prefix="/quiz", tags=["quiz"])
api_router.include_router(planner.router, prefix="/planner", tags=["planner"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])

from fastapi import APIRouter
from app.api.v1.analysis import router as analysis_router
from app.api.v1.assistant import router as assistant_router

api_router = APIRouter()
api_router.include_router(analysis_router, prefix="/analysis", tags=["Analysis"])
api_router.include_router(assistant_router, prefix="/assistant", tags=["Assistant"])
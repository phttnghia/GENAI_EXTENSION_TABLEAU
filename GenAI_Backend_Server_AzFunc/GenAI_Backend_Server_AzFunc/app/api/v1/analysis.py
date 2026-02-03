from fastapi import APIRouter, Depends
from app.models.schemas.analysis import AnalysisRequest, AnalysisResponse
from app.services.analysis_service import AnalysisService
from app.core.security import verify_api_key, verify_jwt

router = APIRouter()

@router.post(
    "",
    response_model=AnalysisResponse,
    dependencies=[Depends(verify_api_key), Depends(verify_jwt)]
)
def analyze_bug_management(request: AnalysisRequest):
    service = AnalysisService()
    return service.execute(request)

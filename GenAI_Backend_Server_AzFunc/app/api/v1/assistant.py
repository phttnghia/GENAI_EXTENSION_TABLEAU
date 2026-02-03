from fastapi import APIRouter, Depends
from app.models.schemas.assistant import AssistantRequest, AssistantResponse
from app.services.assistant_service import AssistantService
from app.core.security import verify_api_key, verify_jwt

router = APIRouter()

@router.post(
    "",
    response_model=AssistantResponse,
    dependencies=[Depends(verify_api_key), Depends(verify_jwt)]
)
def analyze_bug_management(request: AssistantRequest):
    service = AssistantService()
    return service.execute(request)

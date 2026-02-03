from app.models.schemas.assistant import AssistantRequest


class AssistantService:
    def __init__(self):
        self.supervisor = {
            "status": "success",
            "message": """Hello! How can I assist you today?""",
        }

    def execute(self, request: AssistantRequest):
        return self.supervisor

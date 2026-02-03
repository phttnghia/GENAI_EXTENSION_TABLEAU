from app.models.schemas.analysis import AnalysisRequest


class AnalysisService:
    def __init__(self):
        self.supervisor = {
            "status": "success",
            "message": """1. Summary of Defect Detection Status
- Defects detected: 15 high-severity bugs in qdx -_ 2024_1, 8 medium-severity bugs in qdx -_ 2024_1, 7 low-severity bugs in qdx -_ 2024_1, 10 high-severity bugs in qdx -_ 2024_4, 5 medium-severity bugs in qdx -_ 2024_4, and 3 low
-severity bugs in qdx -_ 2024_4.

2. Trend Analysis
- Bug trend analysis: 15% increase in bug reports compared to the previous week, with a 10% decrease from the same period last month.
- High-priority bugs: Steady increase of 5% week-over-week, primarily in qdx -_ 2024_1.

3. Future Concerns
- Potential future issues: 3 recurring bugs identified that may lead to system failures if not addressed, with a projected 20% likelihood of recurrence in the next quarter.
Recommended actions: Monitor bug patterns and allocate resources for early detection.""",
        }

    def execute(self, request: AnalysisRequest):
        return self.supervisor
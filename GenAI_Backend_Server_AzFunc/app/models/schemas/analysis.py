from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import date, datetime


class RequestMeta(BaseModel):
    request_id: str = Field(..., description="Unique request identifier")
    timestamp: datetime = Field(..., description="Request creation timestamp (ISO 8601)")
    mode_type: str = Field(..., description="Type of AI model to be used")


class Period(BaseModel):
    start_date: date = Field(..., description="Analysis start date (YYYY-MM-DD)")
    end_date: date = Field(..., description="Analysis end date (YYYY-MM-DD)")


class Filters(BaseModel):
    redmine_infra: List[str]
    redmine_server: List[str]
    redmine_instance: List[str]
    project_identifier: List[str]
    project_name: List[str]

    filter_1: Optional[List[str]] = None
    filter_2: Optional[List[str]] = None
    filter_3: Optional[List[str]] = None
    filter_4: Optional[List[str]] = None
    filter_5: Optional[List[str]] = None


class MetricsData(BaseModel):
    date: date

    test_case_expected: Optional[int] = Field(None, alias="TestCaseExpected")
    test_case_expected_total: Optional[int] = Field(None, alias="TestCaseExpectedTotal")
    test_case_actual: Optional[int] = Field(None, alias="TestCaseActual")
    test_case_actual_total: Optional[int] = Field(None, alias="TestCaseActualTotal")

    breport_expected: Optional[int] = Field(None, alias="BReportExpected")
    breport_expected_total: Optional[int] = Field(None, alias="BReportExpectedTotal")
    breport_actual: Optional[int] = Field(None, alias="BReportActual")
    breport_actual_total: Optional[int] = Field(None, alias="BReportActualTotal")
    breport_fixed: Optional[int] = Field(None, alias="BReportFixed")
    breport_fixed_total: Optional[int] = Field(None, alias="BReportFixedTotal")
    breport_outstanding: Optional[int] = Field(None, alias="BReportOutstanding")
    breport_upper_bound: Optional[int] = Field(None, alias="BReportUpperBound")
    breport_lower_bound: Optional[int] = Field(None, alias="BReportLowerBound")

    model_config = {
        "populate_by_name": True
    }

class AnalysisRequest(BaseModel):
    request_meta: RequestMeta
    period: Period
    filters: Filters
    metrics_data: List[MetricsData]

class AnalysisResponse(BaseModel):
    status: str
    message: str
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


# =========================
# PDF Document Schemas
# =========================

class PDFDocumentSchema(BaseModel):
    id: int
    filename: str
    status: str
    size: int

    uploaded_by_email: str  # ✅ NEW

    uploaded_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True



class UploadResponseSchema(BaseModel):
    """
    Used for:
    - Response after uploading a PDF (/upload)
    """
    id: int
    filename: str
    status: str


# =========================
# Dashboard Metrics Schemas
# =========================

class DailyUploadMetricSchema(BaseModel):
    """
    Used for:
    - Line chart (daily uploads)
    """
    date: str
    count: int


class DashboardMetricsSchema(BaseModel):
    """
    Used for:
    - KPI cards
    - Analytics dashboard
    """
    total: int
    processed: int
    failed: int
    daily_uploads: List[DailyUploadMetricSchema]


# =========================
# Generic API Message Schema
# =========================

class MessageResponseSchema(BaseModel):
    """
    Used for:
    - Generic API responses
    """
    message: str

# =========================
# Admin Auth Schemas
# =========================

class AdminLoginRequestSchema(BaseModel):
    email: str
    password: str


class AdminLoginResponseSchema(BaseModel):
    access_token: str
    token_type: str = "bearer"

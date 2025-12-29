from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models import PDFDocument
from datetime import datetime
from schemas import DashboardMetricsSchema



router = APIRouter(prefix="/metrics")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("", response_model=DashboardMetricsSchema)
def metrics(
    start_date: str | None = None,
    end_date: str | None = None,
    db: Session = Depends(get_db)
):
    query = db.query(PDFDocument)

    if start_date:
        query = query.filter(
            PDFDocument.uploaded_at >= datetime.fromisoformat(start_date)
        )

    if end_date:
        query = query.filter(
            PDFDocument.uploaded_at <= datetime.fromisoformat(end_date)
        )
    
    total = query.count()
    processed = query.filter(PDFDocument.status == "completed").count()
    failed = query.filter(PDFDocument.status == "failed").count()

    daily = (
        query.with_entities(
            func.date(PDFDocument.uploaded_at).label("date"),
            func.count().label("count")
        )
        .group_by(func.date(PDFDocument.uploaded_at))
        .order_by(func.date(PDFDocument.uploaded_at))
        .all()
    )

    return {
        "total": total,
        "processed": processed,
        "failed": failed,
        "daily_uploads": [
            {"date": str(d.date), "count": d.count} for d in daily
        ]
    }

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import SessionLocal
from models import PDFDocument

router = APIRouter(prefix="/metrics")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("")
def metrics(db: Session = Depends(get_db)):
    total = db.query(PDFDocument).count()
    completed = db.query(PDFDocument).filter_by(status="completed").count()
    failed = db.query(PDFDocument).filter_by(status="failed").count()

    daily = (
        db.query(
            func.date(PDFDocument.uploaded_at).label("date"),
            func.count().label("count")
        )
        .group_by(func.date(PDFDocument.uploaded_at))
        .order_by(func.date(PDFDocument.uploaded_at))
        .all()
    )

    return {
        "total": total,
        "processed": completed,
        "failed": failed,
        "daily_uploads": [
            {"date": str(d.date), "count": d.count} for d in daily
        ]
    }

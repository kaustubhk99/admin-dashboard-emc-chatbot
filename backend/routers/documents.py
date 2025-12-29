from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import SessionLocal
from models import PDFDocument

router = APIRouter(prefix="/documents")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("")
def list_documents(db: Session = Depends(get_db)):
    return db.query(PDFDocument)\
             .order_by(PDFDocument.uploaded_at.desc())\
             .all()

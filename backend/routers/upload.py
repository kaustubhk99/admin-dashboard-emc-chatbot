from fastapi import APIRouter, UploadFile, BackgroundTasks, Depends
from sqlalchemy.orm import Session
import os
from database import SessionLocal
from models import PDFDocument
from services.pdf_pipeline import process_pdf
from auth.deps import get_current_admin


router = APIRouter(prefix="/upload")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("")
async def upload_pdf(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    admin = Depends(get_current_admin)  # ✅ injected admin
):
    os.makedirs("uploads", exist_ok=True)
    path = f"uploads/{file.filename}"

    with open(path, "wb") as f:
        f.write(await file.read())

    pdf = PDFDocument(
        filename=file.filename,
        size=os.path.getsize(path),
        status="uploaded",
        uploaded_by_email=admin.email  # ✅ STORE ADMIN EMAIL
    )

    db.add(pdf)
    db.commit()
    db.refresh(pdf)

    background_tasks.add_task(process_pdf, pdf.id)

    return {
        "id": pdf.id,
        "filename": pdf.filename,
        "status": pdf.status
    }

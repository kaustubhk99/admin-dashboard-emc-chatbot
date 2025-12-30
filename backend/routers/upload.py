from fastapi import APIRouter, UploadFile, BackgroundTasks, Depends, File
from sqlalchemy.orm import Session
from typing import List
from pathlib import Path
import shutil
import os

from database import SessionLocal
from models import PDFDocument
from services.pdf_pipeline import process_pdf
from auth.deps import get_current_admin

from etl_pipeline.src.path import INPUT_PDFS_DIR

router = APIRouter(prefix="/upload")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("")
async def upload_pdf_folder(
    background_tasks: BackgroundTasks,
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
    admin=Depends(get_current_admin),
):
    INPUT_PDFS_DIR.mkdir(parents=True, exist_ok=True)

    total_size = 0

    for f in files:
        target = INPUT_PDFS_DIR / Path(f.filename).name
        with open(target, "wb") as buf:
            shutil.copyfileobj(f.file, buf)
        total_size += os.path.getsize(target)

    pdf = PDFDocument(
        filename=files[0].filename,
        size=total_size,
        status="uploaded",
        uploaded_by_email=admin.email,
    )

    db.add(pdf)
    db.commit()
    db.refresh(pdf)

    background_tasks.add_task(process_pdf, pdf.id)

    return {"id": pdf.id, "status": pdf.status}
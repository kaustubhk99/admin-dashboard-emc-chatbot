import time
from datetime import datetime
from database import SessionLocal
from models import PDFDocument

def process_pdf(pdf_id: int):
    db = SessionLocal()

    try:
        pdf = db.query(PDFDocument).get(pdf_id)
        pdf.status = "processing"
        db.commit()

        # 🔹 Replace this with:
        # - Text extraction
        # - Chunking
        # - Embeddings
        # - Standard classification
        print(f"Processing PDF ID: {pdf_id}, Filename: {pdf.filename}")
        time.sleep(5)
        print(f"Completed processing PDF ID: {pdf_id}, Filename: {pdf.filename}")
        pdf.status = "completed"
        pdf.processed_at = datetime.utcnow()
        db.commit()

    except Exception:
        pdf.status = "failed"
        db.commit()

    finally:
        db.close()

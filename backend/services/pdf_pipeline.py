import logging
from sqlalchemy.orm import Session

from database import SessionLocal
from models import PDFDocument
from etl_pipeline.src.pipeline import run_full_pipeline

logger = logging.getLogger(__name__)

def process_pdf(pdf_id: int) -> None:
    db: Session = SessionLocal()

    try:
        pdf = db.query(PDFDocument).get(pdf_id)
        if not pdf:
            logger.error("PDF not found")
            return

        pdf.status = "processing"
        db.commit()

        logger.info("Starting ETL pipeline")
        run_full_pipeline()

        pdf.status = "completed"
        db.commit()
        logger.info("ETL pipeline completed")

    except Exception as e:
        logger.exception("Pipeline failed")
        pdf.status = "failed"
        db.commit()

    finally:
        db.close()
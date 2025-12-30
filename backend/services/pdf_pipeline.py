from pypdf import PdfReader
from sqlalchemy.orm import Session
from datetime import datetime
import json
import os
from datetime import datetime
from database import SessionLocal
from models import PDFDocument, PDFExtraction


def extract_text_from_pdf(file_path: str):
    reader = PdfReader(file_path)
    pages = []

    for i, page in enumerate(reader.pages):
        text = page.extract_text() or ""
        pages.append({
            "page_number": i + 1,
            "text": text.strip()
        })

    return pages


def clean_text(text: str) -> str:
    return (
        text.replace("\n", " ")
            .replace("\t", " ")
            .strip()
    )


def chunk_text(text: str, chunk_size: int = 800):
    words = text.split()
    return [
        " ".join(words[i:i + chunk_size])
        for i in range(0, len(words), chunk_size)
    ]


def process_pdf(pdf_id: int):
    db: Session = SessionLocal()

    try:
        pdf = db.query(PDFDocument).get(pdf_id)
        pdf.status = "processing"
        db.commit()

        file_path = f"uploads/{pdf.filename}"

        pages = extract_text_from_pdf(file_path)

        all_chunks = []
        chunk_id = 1

        for page in pages:
            cleaned = clean_text(page["text"])
            chunks = chunk_text(cleaned)

            for chunk in chunks:
                if chunk.strip():
                    all_chunks.append({
                        "chunk_id": chunk_id,
                        "page_number": page["page_number"],
                        "text": chunk
                    })
                    chunk_id += 1

        # 🔹 Prepare JSON output
        json_data = {
            "pdf_id": pdf.id,
            "filename": pdf.filename,
            "uploaded_by": pdf.uploaded_by_email,
            "processed_at": datetime.utcnow().isoformat(),
            "chunks": all_chunks
        }

        os.makedirs("extracted_json", exist_ok=True)

        json_file_path = f"extracted_json/{pdf.id}_{pdf.filename}.json"

        with open(json_file_path, "w", encoding="utf-8") as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)

        pdf.status = "completed"
        pdf.processed_at = datetime.utcnow()
        db.commit()

    except Exception as e:
        pdf.status = "failed"
        db.commit()
        print("PDF processing failed:", e)

    finally:
        db.close()

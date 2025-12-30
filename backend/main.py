import sys
from pathlib import Path

# ---------------------------------------------------------
# Ensure etl_pipeline is importable by backend services
# ---------------------------------------------------------
# FastAPI runs from backend/, but etl_pipeline is a
# sibling directory, not a Python package installed via pip.
# Adding etl_pipeline to sys.path allows:
# from etl_pipeline.pipeline import ...
# without copying code or breaking modularity.

REPO_ROOT = Path(__file__).resolve().parents[1]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))\

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import Base, engine    
from routers import upload, documents, metrics, auth

Base.metadata.create_all(bind=engine)

app = FastAPI(title="PDF Analytics Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(upload.router)
app.include_router(documents.router)
app.include_router(metrics.router)

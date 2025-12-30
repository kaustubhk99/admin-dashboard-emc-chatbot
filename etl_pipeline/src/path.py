from pathlib import Path

# etl_pipeline/src/path.py
BASE_DIR = Path(__file__).resolve().parent

DATA_DIR = BASE_DIR / "data"

INPUT_PDFS_DIR = DATA_DIR / "input_pdfs"

OUTPUT_DIR = DATA_DIR / "output"
MARKER_JSON_DIR = OUTPUT_DIR / "marker_json"
MARKER_MD_DIR = OUTPUT_DIR / "marker_md"
OUTPUT_JSON_DIR = OUTPUT_DIR / "output_json"
OUTPUT_SCHEMA_DIR = OUTPUT_DIR / "output_schema"
OUTPUT_JSON_CHUNK_DIR = OUTPUT_DIR / "output_json_chunk"
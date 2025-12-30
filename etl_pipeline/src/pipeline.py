import subprocess
import sys
import logging
import shutil
import json
from pathlib import Path
from typing import Optional

# =========================================================
# Logging Configuration
# =========================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline.log', mode='a', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Fix Windows console encoding
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# =========================================================
# Resolve project paths
# =========================================================

THIS_FILE = Path(__file__).resolve()
SRC_DIR = THIS_FILE.parent
PROJECT_ROOT = SRC_DIR.parent

if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

# =========================================================
# Import paths from path.py
# =========================================================

from path import (
    INPUT_PDFS_DIR,
    MARKER_JSON_DIR,
    MARKER_MD_DIR,
    OUTPUT_JSON_DIR,
    OUTPUT_SCHEMA_DIR,
    OUTPUT_JSON_CHUNK_DIR,
    OUTPUT_DIR,
)

# =========================================================
# Configuration
# =========================================================

MARKER_WORKERS = "1"
MARKER_DISABLE_MP = True

# =========================================================
# Helpers
# =========================================================

def run_cmd(cmd: list, cwd: Optional[Path] = None, stage_name: str = "") -> None:
    """Run a shell command with proper error handling."""
    cmd = [str(c) for c in cmd]
    
    log_prefix = f"[{stage_name}] " if stage_name else ""
    logger.info(f"{log_prefix}Running command: {' '.join(cmd)}")
    
    # Set UTF-8 encoding for subprocess
    import os
    env = os.environ.copy()
    env['PYTHONIOENCODING'] = 'utf-8'
    
    result = subprocess.run(
        cmd,
        cwd=str(cwd) if cwd else None,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8',
        errors='replace',
        check=False,
        env=env
    )
    
    if result.stdout:
        for line in result.stdout.splitlines():
            logger.info(f"{log_prefix}  {line}")
    
    if result.stderr:
        for line in result.stderr.splitlines():
            logger.warning(f"{log_prefix}  {line}")
    
    if result.returncode != 0:
        error_msg = f"Command failed with exit code {result.returncode}: {' '.join(cmd)}"
        logger.error(f"{log_prefix}{error_msg}")
        raise RuntimeError(error_msg)
        
    logger.info(f"{log_prefix}Command completed successfully")


def ensure_dirs() -> None:
    """Create all required directories."""
    dirs_to_create = [
        INPUT_PDFS_DIR,
        MARKER_JSON_DIR,
        MARKER_MD_DIR,
        OUTPUT_JSON_DIR,
        OUTPUT_SCHEMA_DIR,
        OUTPUT_JSON_CHUNK_DIR,
    ]
    
    for d in dirs_to_create:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory exists: {d}")


def validate_input_pdfs() -> int:
    """Validate that input PDFs exist."""
    if not INPUT_PDFS_DIR.exists():
        raise FileNotFoundError(f"Input directory not found: {INPUT_PDFS_DIR}")
    
    pdf_files = list(INPUT_PDFS_DIR.glob("*.pdf"))
    pdf_count = len(pdf_files)
    
    if pdf_count == 0:
        logger.warning(f"No PDF files found in {INPUT_PDFS_DIR}")
        return 0
    
    logger.info(f"Found {pdf_count} PDF file(s) to process")
    for pdf in pdf_files:
        logger.info(f"  - {pdf.name}")
    
    return pdf_count

# =========================================================
# Pipeline Stages
# =========================================================

def stage_1_run_marker() -> None:
    """Run Marker on all PDFs in input_pdfs/."""
    logger.info("=" * 50)
    logger.info("STAGE 1: Running Marker PDF Converter")
    logger.info("=" * 50)
    
    cmd = [
        "marker",
        str(INPUT_PDFS_DIR),
        "--output_dir", str(OUTPUT_DIR),
        "--workers", MARKER_WORKERS,
        "--output_format", "json",
    ]
    
    if MARKER_DISABLE_MP:
        cmd.append("--disable_multiprocessing")
    
    run_cmd(cmd, cwd=PROJECT_ROOT, stage_name="Marker")
    
    # Organize Marker outputs
    logger.info("\nOrganizing Marker outputs...")
    organize_marker_outputs()


def organize_marker_outputs() -> None:
    """Move Marker outputs from data/output/ to data/output/marker_json/."""
    if not OUTPUT_DIR.exists():
        logger.warning(f"Output directory not found: {OUTPUT_DIR}")
        return
    
    moved_count = 0
    
    for item in OUTPUT_DIR.iterdir():
        # Skip our target subdirectories
        if item.name in ['marker_json', 'marker_md', 'output_json', 'output_schema', 'output_json_chunk']:
            continue
        
        if not item.is_dir():
            continue
        
        pdf_name = item.name
        logger.info(f"  Organizing outputs for: {pdf_name}")
        
        target_json_dir = MARKER_JSON_DIR / pdf_name
        target_json_dir.mkdir(parents=True, exist_ok=True)
        
        for file in item.iterdir():
            if file.is_file():
                target_file = target_json_dir / file.name
                if target_file.exists():
                    target_file.unlink()
                shutil.move(str(file), str(target_file))
                logger.info(f"    Moved: {file.name}")
                moved_count += 1
            
            elif file.is_dir():
                target_subdir = target_json_dir / file.name
                if target_subdir.exists():
                    shutil.rmtree(target_subdir)
                shutil.move(str(file), str(target_subdir))
                logger.info(f"    Moved folder: {file.name}/")
                moved_count += 1
        
        if item.exists() and not any(item.iterdir()):
            item.rmdir()
            logger.info(f"    Cleaned up: {pdf_name}/")
    
    if moved_count > 0:
        logger.info(f"\nOrganized {moved_count} items into marker_json/")
    
    json_files = list(MARKER_JSON_DIR.rglob("*.json"))
    non_meta_files = [f for f in json_files if not f.name.endswith("_meta.json")]
    
    if not non_meta_files:
        raise RuntimeError("No JSON files found in marker_json/")
    
    logger.info(f"Found {len(non_meta_files)} JSON file(s) in marker_json/")


def stage_2_collect_marker_json() -> None:
    """Copy Marker JSON files to output_json/."""
    logger.info("=" * 50)
    logger.info("STAGE 2: Collecting Marker JSON outputs")
    logger.info("=" * 50)
    
    collected_count = 0
    
    for doc_dir in MARKER_JSON_DIR.iterdir():
        if not doc_dir.is_dir():
            continue

        json_file = doc_dir / f"{doc_dir.name}.json"
        if json_file.exists():
            dest = OUTPUT_JSON_DIR / json_file.name
            shutil.copy2(json_file, dest)
            logger.info(f"  Collected: {json_file.name}")
            collected_count += 1
    
    if collected_count == 0:
        raise RuntimeError("No JSON files collected to output_json/")
    
    logger.info(f"\nCollected {collected_count} file(s) to output_json/")


def stage_3_json_to_schema() -> None:
    """Convert Marker JSON to hierarchical schema."""
    logger.info("=" * 50)
    logger.info("STAGE 3: Converting JSON to hierarchical schema")
    logger.info("=" * 50)
    
    # Try to import and run the conversion function
    try:
        sys.path.insert(0, str(SRC_DIR))
        from json_to_schema_v5 import main as schema_main
        
        logger.info("  Running json_to_schema_v5...")
        schema_main()
        
    except Exception as e:
        logger.error(f"  Error running json_to_schema_v5: {e}")
        logger.info("  Attempting fallback: running as subprocess...")
        
        # Fallback: run as subprocess
        script_path = SRC_DIR / "json_to_schema_v5.py"
        if not script_path.exists():
            raise RuntimeError(f"Script not found: {script_path}")
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(SRC_DIR),
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")
        
        if result.returncode != 0:
            if result.stderr:
                logger.error(result.stderr)
            raise RuntimeError(f"json_to_schema_v5.py failed with exit code {result.returncode}")
    
    # Verify schema files were created
    schema_files = list(OUTPUT_SCHEMA_DIR.glob("*_final_schema.json"))
    if not schema_files:
        raise RuntimeError("No schema files generated in output_schema/")
    
    logger.info(f"\nGenerated {len(schema_files)} schema file(s)")


def stage_4_schema_to_chunks() -> None:
    """Convert hierarchical schema to clause-wise chunks."""
    logger.info("=" * 50)
    logger.info("STAGE 4: Converting schema to chunks")
    logger.info("=" * 50)
    
    # Try to import and run the chunking function
    try:
        sys.path.insert(0, str(SRC_DIR))
        from schema_to_chunks import main as chunks_main
        
        logger.info("  Running schema_to_chunks...")
        chunks_main()
        
    except Exception as e:
        logger.error(f"  Error running schema_to_chunks: {e}")
        logger.info("  Attempting fallback: running as subprocess...")
        
        # Fallback: run as subprocess
        script_path = SRC_DIR / "schema_to_chunks.py"
        if not script_path.exists():
            raise RuntimeError(f"Script not found: {script_path}")
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(SRC_DIR),
            capture_output=True,
            text=True
        )
        
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.info(f"  {line}")
        
        if result.returncode != 0:
            if result.stderr:
                logger.error(result.stderr)
            raise RuntimeError(f"schema_to_chunks.py failed with exit code {result.returncode}")
    
    # Verify chunks were created
    chunk_files = list(OUTPUT_JSON_CHUNK_DIR.rglob("*.json"))
    if not chunk_files:
        logger.warning("No chunk files generated (may be expected for some documents)")
    else:
        logger.info(f"\nGenerated {len(chunk_files)} chunk file(s)")

# =========================================================
# Main Pipeline
# =========================================================

def run_full_pipeline() -> None:
    """Execute the complete PDF processing pipeline."""
    logger.info("=" * 60)
    logger.info("PDF PROCESSING PIPELINE - START")
    logger.info("=" * 60)
    logger.info(f"Project root : {PROJECT_ROOT}")
    logger.info(f"Source dir   : {SRC_DIR}")
    logger.info(f"Python       : {sys.executable}")
    logger.info(f"Python ver   : {sys.version.split()[0]}")
    
    # Pre-flight checks
    logger.info("\nRunning pre-flight checks...")
    ensure_dirs()
    pdf_count = validate_input_pdfs()
    
    if pdf_count == 0:
        logger.warning("No PDFs to process. Exiting.")
        return
    
    # Execute pipeline stages
    stage_1_run_marker()
    stage_2_collect_marker_json()
    stage_3_json_to_schema()
    stage_4_schema_to_chunks()
    
    logger.info("=" * 60)
    logger.info("PDF PROCESSING PIPELINE - COMPLETED SUCCESSFULLY")
    logger.info("=" * 60)
    logger.info("Final outputs:")
    logger.info(f"  - Schema JSONs  -> {OUTPUT_SCHEMA_DIR}")
    logger.info(f"  - Clause Chunks -> {OUTPUT_JSON_CHUNK_DIR}")
    logger.info("\nPipeline log saved to: pipeline.log")


if __name__ == "__main__":
    run_full_pipeline()
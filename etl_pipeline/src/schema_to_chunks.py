import json
from pathlib import Path
import sys
from pathlib import Path

print("schema to json working!!!")

# Support running as script or module
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from path import OUTPUT_SCHEMA_DIR, OUTPUT_JSON_CHUNK_DIR

# =========================================================
# Helpers
# =========================================================

def safe_filename(clause_id: str) -> str:
    """Make clause ID filesystem-safe"""
    return clause_id.replace("/", "_")

def write_clause_chunk(doc_id: str, clause: dict, out_root: Path):
    """
    Write one clause as a standalone JSON chunk.
    """
    doc_dir = out_root / doc_id
    doc_dir.mkdir(parents=True, exist_ok=True)

    chunk = {
        "chunk_id": clause["id"],
        "document_id": doc_id,
        "title": clause.get("title"),
        "parent_id": clause["id"].rsplit(".", 1)[0] if "." in clause["id"] else None,
        "content": clause.get("content", []),
        "tables": clause.get("tables", []),
        "figures": clause.get("figures", []),
        "requirements": clause.get("requirements", []),
        "children_ids": [c["id"] for c in clause.get("children", [])]
    }

    out_path = doc_dir / f"{safe_filename(clause['id'])}.json"
    out_path.write_text(
        json.dumps(chunk, indent=2, ensure_ascii=False),
        encoding="utf-8"
    )

def walk_clauses(doc_id: str, clauses: list, out_root: Path):
    """
    Depth-first traversal of clause tree.
    """
    for clause in clauses:
        write_clause_chunk(doc_id, clause, out_root)
        walk_clauses(doc_id, clause.get("children", []), out_root)

# =========================================================
# Main (FIXED)
# =========================================================

def main():
    OUTPUT_JSON_CHUNK_DIR.mkdir(parents=True, exist_ok=True)

    schema_files = list(OUTPUT_SCHEMA_DIR.glob("*_final_schema.json"))
    if not schema_files:
        print("No schema files found for chunking")
        return

    for sf in schema_files:
        data = json.loads(sf.read_text(encoding="utf-8"))

        doc_id = data.get("document_id")
        clauses = data.get("clauses", [])

        if not doc_id or not clauses:
            print(f"[SKIP] Invalid schema file: {sf.name}")
            continue

        walk_clauses(doc_id, clauses, OUTPUT_JSON_CHUNK_DIR)

        print(f"[OK] Clause chunks written for document: {doc_id}")

if __name__ == "__main__":
    main()
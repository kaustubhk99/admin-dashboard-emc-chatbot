import json
import re
import base64
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from collections import OrderedDict

import sys
from pathlib import Path

print("json to schema working!!!")

# Support running as script or module
if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).parent))

from path import OUTPUT_JSON_DIR, OUTPUT_SCHEMA_DIR, OUTPUT_DIR

# =========================================================
# REGEX PATTERNS
# =========================================================

CLAUSE_WITH_TITLE_RE = re.compile(r'^([A-Z]|\d+)(?:\.(\d+))*\s+(.+)$', re.IGNORECASE)
CLAUSE_NUM_ONLY_RE = re.compile(r'^([A-Z]|\d+)(?:\.(\d+))*\s*$', re.IGNORECASE)
HTML_TAG_RE = re.compile(r'<[^>]+>')
REQ_RE = re.compile(r'\b(shall not|shall|should|may)\b', re.IGNORECASE)
TABLE_REF_RE = re.compile(r'\btable\s+([A-Z]?\d+(?:\.\d+)*)', re.IGNORECASE)
FIGURE_REF_RE = re.compile(r'\b(?:figure|fig\.?)\s+([A-Z]?\d+(?:\.\d+)*)', re.IGNORECASE)

# =========================================================
# HELPERS
# =========================================================

def strip_html(html: str) -> str:
    return HTML_TAG_RE.sub('', html).strip() if html else ""

def detect_image_format(data: bytes) -> str:
    if data.startswith(b"\x89PNG"):
        return ".png"
    if data.startswith(b"\xff\xd8\xff"):
        return ".jpg"
    if data.startswith(b"GIF8"):
        return ".gif"
    if data.startswith(b"BM"):
        return ".bmp"
    if data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        return ".webp"
    return ".bin"

def extract_clause_info(text: str) -> Optional[Tuple[str, Optional[str]]]:
    if not text:
        return None

    m = CLAUSE_WITH_TITLE_RE.match(text)
    if m:
        cid = text.split()[0]
        title = text[len(cid):].strip()
        return cid, title or None

    m = CLAUSE_NUM_ONLY_RE.match(text)
    if m:
        return m.group(0).strip(), None

    return None

def extract_table_number(caption: str) -> Optional[str]:
    m = TABLE_REF_RE.search(caption) if caption else None
    return m.group(1) if m else None

def extract_figure_number(caption: str) -> Optional[str]:
    m = FIGURE_REF_RE.search(caption) if caption else None
    return m.group(1) if m else None

def extract_requirements(text: str) -> List[Dict[str, str]]:
    if not text:
        return []

    for m in REQ_RE.finditer(text):
        keyword = m.group(1).lower()
        return [{
            "type": {
                "shall not": "prohibition",
                "shall": "mandatory",
                "should": "recommendation",
                "may": "permission"
            }[keyword],
            "keyword": keyword,
            "text": text
        }]
    return []

# =========================================================
# CONTEXT
# =========================================================

class ProcessingContext:
    def __init__(self):
        self.current_clause_id = None
        self.pending_number = None
        self.pending_caption = None

    def reset(self):
        self.pending_caption = None

# =========================================================
# BLOCK PROCESSOR (UNCHANGED)
# =========================================================

def process_block(block, clauses, context, counters, img_root, misc_img_dir):
    if not isinstance(block, dict):
        return

    btype = block.get("block_type")

    if btype in ("PageHeader", "PageFooter"):
        return

    if btype == "SectionHeader":
        text = strip_html(block.get("html", ""))
        info = extract_clause_info(text)

        if info:
            cid, title = info
            if title:
                clauses.setdefault(cid, {
                    "id": cid,
                    "title": title,
                    "children": [],
                    "content": [],
                    "tables": [],
                    "figures": [],
                    "requirements": []
                })
                context.current_clause_id = cid
                context.pending_number = None
                context.reset()
            else:
                context.pending_number = cid

        elif context.pending_number:
            cid = context.pending_number
            clauses[cid] = {
                "id": cid,
                "title": text,
                "children": [],
                "content": [],
                "tables": [],
                "figures": [],
                "requirements": []
            }
            context.current_clause_id = cid
            context.pending_number = None
            context.reset()

    elif btype == "Text":
        text = strip_html(block.get("html", ""))
        cid = context.current_clause_id
        if text and cid in clauses:
            clauses[cid]["content"].append({"type": "paragraph", "text": text})
            clauses[cid]["requirements"].extend(extract_requirements(text))

    for child in block.get("children", []) or []:
        process_block(child, clauses, context, counters, img_root, misc_img_dir)

# =========================================================
# CONVERT ONE FILE (THIS IS THE KEY)
# =========================================================

def convert_file(path: Path) -> Dict:
    raw = json.loads(path.read_text(encoding="utf-8"))

    doc_id = path.stem
    img_root = OUTPUT_DIR / "output_images" / doc_id
    img_root.mkdir(parents=True, exist_ok=True)

    misc_img_dir = img_root / "misc"
    misc_img_dir.mkdir(parents=True, exist_ok=True)

    clauses = OrderedDict()
    context = ProcessingContext()

    counters = {
        "total_images": 0,
        "clause_images": 0,
        "misc_images": 0,
        "total_tables": 0
    }

    for child in raw.get("children", []):
        process_block(child, clauses, context, counters, img_root, misc_img_dir)

    return {
        "document_id": doc_id,
        "statistics": counters,
        "clauses": list(clauses.values())
    }

# =========================================================
# PIPELINE ENTRY (FIXED)
# =========================================================

def main():
    OUTPUT_SCHEMA_DIR.mkdir(parents=True, exist_ok=True)

    files = [
        f for f in OUTPUT_JSON_DIR.glob("*.json")
        if not f.name.endswith("_meta.json")
    ]

    if not files:
        print("No Marker JSON files found")
        return

    for f in files:
        schema = convert_file(f)

        out = OUTPUT_SCHEMA_DIR / f"{f.stem}_final_schema.json"
        out.write_text(json.dumps(schema, indent=2), encoding="utf-8")

        print(f"[OK] Schema created: {out.name}")

if __name__ == "__main__":
    main()
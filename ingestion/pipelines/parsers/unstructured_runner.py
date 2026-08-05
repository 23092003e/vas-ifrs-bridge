"""
Parse raw documents (PDF/DOCX/XLSX/TXT) into plain text + metadata JSON.

Output format (one JSON file per input document):
  {
    "source_path": "...",
    "filename": "...",
    "lang": "vi|en|bi",
    "standard_code": "VAS-15|IFRS-15|null",
    "text": "full plain text...",
    "sections": [{"heading": "...", "text": "..."}, ...]
  }

Run:
  python ingestion/unstructured_runner.py --input ingestion/documents/shared/vas --output ingestion/parsed/shared/vas
  python ingestion/unstructured_runner.py --input ingestion/documents/shared/ifrs --output ingestion/parsed/shared/ifrs
"""
from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

logger = logging.getLogger(__name__)

_STANDARD_CODE_RE = re.compile(
    r"\b(VAS|IAS|IFRS|VFRS)[\s\-]?(\d+[A-Z]?)\b"
    r"|(\b\d+/\d+/(?:TT-BTC|NĐ-CP|ND-CP|QĐ-BTC)\b)",
    re.IGNORECASE
)


def _detect_lang(text: str) -> str:
    vi_chars = sum(1 for c in text.lower() if c in "àáảãạăắằẵặẳâấầẫậẩđèéẻẽẹêếềễệểìíỉĩịòóỏõọôốồỗộổơớờỡợởùúủũụưứừữựửỳýỷỹỵ")
    if vi_chars / max(len(text), 1) > 0.02:
        return "vi"
    return "en"


def _extract_standard_code(filename: str, text: str) -> str | None:
    m = _STANDARD_CODE_RE.search(filename) or _STANDARD_CODE_RE.search(text[:2000])
    if m:
        if m.group(1) and m.group(2):
            prefix = m.group(1).upper()
            num = m.group(2)
            return f"{prefix}-{num}"
        return m.group(3).upper()
    return None


_PDF_FOOTER_RE = re.compile(
    r"^\s*(?:©\s*IFRS\s*Foundation"
    r"|IFRS\s*\d+"
    r"|IAS\s*\d+"
    r"|[A-C]\d+"
    r"|\d+"
    r")\s*$",
    re.IGNORECASE
)


def _parse_pdf(path: Path) -> tuple[str, list[dict]]:
    # pyrefly: ignore [missing-import]
    from collections import Counter

    import fitz  # pymupdf

    doc = fitz.open(str(path))
    
    # 1. Determine dominant font size across the document
    sizes = []
    for page in doc:
        blocks = page.get_text("dict").get("blocks", [])
        for b in blocks:
            if "lines" in b:
                for l in b["lines"]:
                    for s in l["spans"]:
                        sizes.append(round(s["size"], 1))
    
    body_size = 10.0
    if sizes:
        body_size = Counter(sizes).most_common(1)[0][0]
    
    sections: list[dict] = []
    current_heading = ""
    current_text_parts: list[str] = []
    full_text_parts: list[str] = []

    # 2. Iterate through pages to extract structured text & tables
    for page in doc:
        rect = page.rect
        height = rect.height
        top_margin = height * 0.08
        bottom_margin = height * 0.92

        # Extract tables
        tables = page.find_tables()
        table_bboxes = []
        markdown_tables = []
        for table in tables.tables:
            table_bboxes.append(table.bbox)
            try:
                rows = table.extract()
                if not rows or len(rows) == 0:
                    continue
                md_rows = []
                md_rows.append("| " + " | ".join(str(c or '').replace('\n', ' ').strip() for c in rows[0]) + " |")
                md_rows.append("| " + " | ".join("---" for _ in rows[0]) + " |")
                for r in rows[1:]:
                    md_rows.append("| " + " | ".join(str(c or '').replace('\n', ' ').strip() for c in r) + " |")
                markdown_tables.append("\n".join(md_rows))
            # PyMuPDF table extraction can surface several backend-specific errors.
            except Exception as e:  # noqa: BLE001
                logger.error("Failed to parse table: %s", e)

        # Extract text spans
        page_dict = page.get_text("dict")
        blocks = page_dict.get("blocks", [])
        blocks = sorted(blocks, key=lambda x: (x.get("bbox", [0, 0, 0, 0])[1], x.get("bbox", [0, 0, 0, 0])[0]))

        for b in blocks:
            if "lines" not in b:
                continue

            bbox = b.get("bbox", [0, 0, 0, 0])
            y0, y1 = bbox[1], bbox[3]

            # Filter out running headers and footers
            if y0 < top_margin or y1 > bottom_margin:
                continue

            # Check if this block falls inside any table bbox
            in_table = False
            for t_bbox in table_bboxes:
                if (bbox[0] >= t_bbox[0] - 5 and bbox[1] >= t_bbox[1] - 5 and
                    bbox[2] <= t_bbox[2] + 5 and bbox[3] <= t_bbox[3] + 5):
                    in_table = True
                    break
            if in_table:
                continue

            block_text_lines = []
            block_is_heading = False
            
            for l in b["lines"]:
                line_spans = l.get("spans", [])
                line_text = "".join(s.get("text", "") for s in line_spans).strip()
                if not line_text:
                    continue

                # Skip header/footer residue matching the regex
                if _PDF_FOOTER_RE.match(line_text):
                    continue

                for s in line_spans:
                    font = s.get("font", "").lower()
                    size = s.get("size", 10.0)
                    is_bold = "bold" in font or "heavy" in font or "black" in font or "semibold" in font or s.get("flags", 0) & 16
                    is_large = size >= body_size + 1.5 or (body_size >= 11.5 and size >= body_size)
                    
                    if is_large and is_bold and len(line_text) < 150:
                        block_is_heading = True
                        break

                block_text_lines.append(line_text)

            block_text = " ".join(block_text_lines).strip()
            if not block_text:
                continue

            if block_is_heading:
                if current_text_parts:
                    sections.append({
                        "heading": current_heading,
                        "text": "\n".join(current_text_parts)
                    })
                current_heading = block_text
                current_text_parts = []
            else:
                current_text_parts.append(block_text)
            
            full_text_parts.append(block_text)

        for md_table in markdown_tables:
            current_text_parts.append("\n" + md_table + "\n")
            full_text_parts.append("\n" + md_table + "\n")

    if current_text_parts or current_heading:
        sections.append({
            "heading": current_heading,
            "text": "\n".join(current_text_parts)
        })

    doc.close()
    full_text = "\n".join(full_text_parts)
    return full_text, sections


def _parse_docx(path: Path) -> tuple[str, list[dict]]:
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(str(path))
    sections: list[dict] = []
    current_heading = ""
    current_body: list[str] = []
    full_text_parts: list[str] = []

    for child in doc.element.body:
        if child.tag.endswith("p"):
            para = Paragraph(child, doc)
            text = para.text.strip()
            if not text:
                continue
            full_text_parts.append(text)

            style = para.style.name if para.style else ""
            if style and style.startswith("Heading"):
                if current_body:
                    sections.append({"heading": current_heading, "text": "\n".join(current_body)})
                current_heading = text
                current_body = []
            else:
                current_body.append(text)
        elif child.tag.endswith("tbl"):
            table = Table(child, doc)
            table_rows = []
            for row in table.rows:
                cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                if any(cells):
                    table_rows.append(" | ".join(cells))
            if table_rows:
                table_text = "\n".join(table_rows)
                current_body.append(table_text)
                full_text_parts.append(table_text)

    if current_body:
        sections.append({"heading": current_heading, "text": "\n".join(current_body)})

    full_text = "\n".join(full_text_parts)
    return full_text, sections


def _parse_xlsx(path: Path) -> tuple[str, list[dict]]:
    import openpyxl
    wb = openpyxl.load_workbook(str(path), read_only=True, data_only=True)
    try:
        parts: list[str] = []
        sections: list[dict] = []
        for sheet in wb.worksheets:
            rows: list[str] = []
            for row in sheet.iter_rows(values_only=True):
                cells = [str(c) if c is not None else "" for c in row]
                if any(c.strip() for c in cells):
                    rows.append("\t".join(cells))
            if rows:
                body = "\n".join(rows)
                parts.append(f"## {sheet.title}\n{body}")
                sections.append({"heading": sheet.title, "text": body})
        return "\n\n".join(parts), sections
    finally:
        wb.close()


def _parse_txt(path: Path) -> tuple[str, list[dict]]:
    text = path.read_text(encoding="utf-8", errors="replace")
    return text, []


_PARSERS = {
    ".pdf": _parse_pdf,
    ".docx": _parse_docx,
    ".xlsx": _parse_xlsx,
    ".txt": _parse_txt,
    ".md": _parse_txt,
}


def parse_document(path: Path) -> dict:
    suffix = path.suffix.lower()
    parser = _PARSERS.get(suffix)
    if parser is None:
        raise ValueError(f"unsupported file type: {suffix}")

    text, sections = parser(path)
    lang = _detect_lang(text)
    std_code = _extract_standard_code(path.name, text)

    return {
        "source_path": str(path),
        "filename": path.name,
        "lang": lang,
        "standard_code": std_code,
        "text": text,
        "sections": sections,
    }


def process_directory(input_dir: Path, output_dir: Path, force: bool = False) -> int:
    output_dir.mkdir(parents=True, exist_ok=True)
    processed = 0
    errors = 0

    extensions = set(_PARSERS.keys())
    files = [f for f in input_dir.rglob("*") if f.suffix.lower() in extensions]
    logger.info("found %d documents in %s", len(files), input_dir)

    for fp in files:
        rel_path = fp.relative_to(input_dir)
        out_path = output_dir / rel_path.with_suffix(".json")
        
        if out_path.exists() and not force:
            logger.debug("skip (already parsed): %s", rel_path)
            continue
            
        try:
            out_path.parent.mkdir(parents=True, exist_ok=True)
            result = parse_document(fp)
            out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
            logger.info("parsed: %s → %s (%d chars)", rel_path, out_path.relative_to(output_dir), len(result["text"]))
            processed += 1
        # Keep processing the corpus; the aggregate error count drives a nonzero exit.
        except Exception as exc:  # noqa: BLE001
            logger.error("FAILED %s: %s", rel_path, exc)
            errors += 1

    print(f"\nDone: {processed} parsed, {errors} errors")
    return errors


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Parse documents to JSON")
    parser.add_argument("--input", required=True, help="Input directory with PDF/DOCX/XLSX/TXT")
    parser.add_argument("--output", required=True, help="Output directory for JSON files")
    parser.add_argument("--file", default=None, help="Parse single file instead of directory")
    parser.add_argument("--force", action="store_true", help="Force overwrite existing parsed JSON files")
    args = parser.parse_args()

    if args.file:
        result = parse_document(Path(args.file))
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return

    errors = process_directory(Path(args.input), Path(args.output), force=args.force)
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()

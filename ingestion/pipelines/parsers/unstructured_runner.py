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
    r"\b(VAS|IAS|IFRS|VFRS)[\s\-]?(\d+[A-Z]?)\b", re.IGNORECASE
)


def _detect_lang(text: str) -> str:
    vi_chars = sum(1 for c in text.lower() if c in "àáảãạăắằẵặẳâấầẫậẩđèéẻẽẹêếềễệểìíỉĩịòóỏõọôốồỗộổơớờỡợởùúủũụưứừữựửỳýỷỹỵ")
    if vi_chars / max(len(text), 1) > 0.02:
        return "vi"
    return "en"


def _extract_standard_code(filename: str, text: str) -> str | None:
    m = _STANDARD_CODE_RE.search(filename) or _STANDARD_CODE_RE.search(text[:2000])
    if m:
        prefix = m.group(1).upper()
        num = m.group(2)
        return f"{prefix}-{num}"
    return None


def _parse_pdf(path: Path) -> tuple[str, list[dict]]:
    # pyrefly: ignore [missing-import]
    import fitz  # pymupdf
    doc = fitz.open(str(path))
    pages: list[str] = []
    for page in doc:
        pages.append(page.get_text("text"))
    doc.close()
    full_text = "\n".join(pages)
    return full_text, []


def _parse_docx(path: Path) -> tuple[str, list[dict]]:
    from docx import Document
    from docx.text.paragraph import Paragraph
    from docx.table import Table

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
    ".doc": _parse_docx,
    ".xlsx": _parse_xlsx,
    ".xls": _parse_xlsx,
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
        except Exception as exc:
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

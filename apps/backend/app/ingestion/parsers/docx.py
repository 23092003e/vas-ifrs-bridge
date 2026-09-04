"""DOCX parser using python-docx with standard library XML fallback."""

from __future__ import annotations


def parse_docx(path: str) -> str:
    """Extract text from a DOCX file, with fallback to standard library XML parsing."""
    try:
        import docx
        doc = docx.Document(path)
        texts = []
        for p in doc.paragraphs:
            text = p.text.strip()
            if not text:
                continue
            
            # Check style name for headings (e.g., "Heading 1", "Heading 2")
            style_name = p.style.name if p.style else ""
            if style_name.startswith("Heading"):
                try:
                    level = int(style_name.split()[-1])
                    level = min(max(level, 1), 6) # Clamp to 1-6
                    text = f"{'#' * level} {text}"
                except ValueError:
                    pass
            texts.append(text)
        return "\n\n".join(texts)
    except ImportError:
        # Simple zipfile parsing fallback for .docx files (which are zip archives of xml files)
        import xml.etree.ElementTree as ET
        import zipfile
        try:
            with zipfile.ZipFile(path) as docx_zip:
                xml_content = docx_zip.read('word/document.xml')
                root = ET.fromstring(xml_content)
                namespaces = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
                texts = []
                for p in root.findall('.//w:p', namespaces):
                    p_text = "".join(node.text for node in p.findall('.//w:t', namespaces) if node.text).strip()
                    if p_text:
                        # Attempt to check style for fallback
                        p_style = p.find('.//w:pStyle', namespaces)
                        if p_style is not None:
                            val = p_style.get('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val')
                            if val and val.startswith('Heading'):
                                try:
                                    level = int(val.replace('Heading', ''))
                                    level = min(max(level, 1), 6)
                                    p_text = f"{'#' * level} {p_text}"
                                except ValueError:
                                    pass
                        texts.append(p_text)
                return "\n\n".join(texts)
        except Exception as exc:
            raise ImportError(f"docx module is required for .docx files (fallback zip parser failed: {exc})") from exc

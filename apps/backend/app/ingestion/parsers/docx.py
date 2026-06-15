"""DOCX parser using python-docx with standard library XML fallback."""

from __future__ import annotations


def parse_docx(path: str) -> str:
    """Extract text from a DOCX file, with fallback to standard library XML parsing."""
    try:
        import docx
        doc = docx.Document(path)
        return "\n\n".join(p.text for p in doc.paragraphs)
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
                    p_text = "".join(node.text for node in p.findall('.//w:t', namespaces) if node.text)
                    if p_text:
                        texts.append(p_text)
                return "\n\n".join(texts)
        except Exception as exc:
            raise ImportError(f"docx module is required for .docx files (fallback zip parser failed: {exc})") from exc

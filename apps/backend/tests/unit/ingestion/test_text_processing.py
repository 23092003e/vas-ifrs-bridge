from app.ingestion.normalizer import normalize
from app.ingestion.parsers.html import parse_html


def test_normalize_preserves_paragraphs_and_cleans_invisible_whitespace() -> None:
    raw = "\ufeff  Chuẩn\u00a0mực   kế toán \r\n\r\n\r\n  Báo\u200bcáo   tài chính  "

    assert normalize(raw) == "Chuẩn mực kế toán\n\nBáo cáo tài chính"


def test_normalize_uses_canonical_unicode() -> None:
    assert normalize("Ba\u0301o ca\u0301o") == "Báo cáo"


def test_parse_html_extracts_visible_block_text() -> None:
    content = """
    <html><head><title>Hidden title</title><style>.x { color: red }</style></head>
    <body><h1>VAS &amp; IFRS</h1><p>Khoản <strong>mục</strong> thứ nhất.</p>
    <script>alert('hidden')</script><ul><li>Một</li><li>Hai</li></ul></body></html>
    """

    assert parse_html(content) == "VAS & IFRS\n\nKhoản mục thứ nhất.\n\nMột\n\nHai"


def test_parse_html_handles_empty_input() -> None:
    assert parse_html("") == ""

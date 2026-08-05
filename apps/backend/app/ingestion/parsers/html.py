"""HTML parser using BeautifulSoup."""

from __future__ import annotations

from html.parser import HTMLParser

from app.ingestion.normalizer import normalize

_BLOCK_TAGS = {
    "address",
    "article",
    "aside",
    "blockquote",
    "br",
    "div",
    "footer",
    "h1",
    "h2",
    "h3",
    "h4",
    "h5",
    "h6",
    "header",
    "hr",
    "li",
    "main",
    "nav",
    "p",
    "section",
    "table",
    "tr",
}
_HIDDEN_TAGS = {"head", "noscript", "script", "style", "svg", "template"}


class _VisibleTextParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.hidden_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        del attrs
        if tag in _HIDDEN_TAGS:
            self.hidden_depth += 1
        elif not self.hidden_depth and tag in _BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_endtag(self, tag: str) -> None:
        if tag in _HIDDEN_TAGS:
            self.hidden_depth = max(0, self.hidden_depth - 1)
        elif not self.hidden_depth and tag in _BLOCK_TAGS:
            self.parts.append("\n\n")

    def handle_data(self, data: str) -> None:
        if not self.hidden_depth:
            self.parts.append(data)


def parse_html(content: str) -> str:
    """Extract clean text from HTML content."""
    if not content:
        return ""

    parser = _VisibleTextParser()
    parser.feed(content)
    parser.close()
    return normalize("".join(parser.parts))

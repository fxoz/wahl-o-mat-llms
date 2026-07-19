"""A tiny Markdown renderer to HTML.

This is intentionally small (no external dependencies) but covers the
subset used in ``assets/*.md``: headings (``#``–``######``), paragraphs,
horizontal rules (``---`` / ``***`` / ``___``), blockquotes (``>``),
unordered and ordered lists, and inline ``**bold**`` / ``*italic*`` /
``__bold__`` / ``_italic_`` / ``code`` / ``[link](url)``.

Everything is HTML-escaped before markup is applied, so arbitrary
markdown text cannot inject raw HTML.
"""

from __future__ import annotations

import re
from html import escape

_CODE_PLACEHOLDER = "\x00C{}\x00"


def _stash_code_spans(text: str) -> tuple[str, list[str]]:
    """Pull ``code`` spans out of ``text`` so their content is not mangled.

    Returns the masked text and the list of already-rendered ``<code>``
    fragments (in insertion order).
    """
    stashed: list[str] = []

    def _stash(match: re.Match[str]) -> str:
        rendered = "<code>" + escape(match.group(1)) + "</code>"
        stashed.append(rendered)
        return _CODE_PLACEHOLDER.format(len(stashed) - 1)

    masked = re.sub(r"`([^`]+)`", _stash, text)
    return masked, stashed


def _restore_code_spans(text: str, stashed: list[str]) -> str:
    return re.sub(
        _CODE_PLACEHOLDER.replace("{}", r"(\d+)"),
        lambda m: stashed[int(m.group(1))],
        text,
    )


def _link_replacement(match: re.Match[str]) -> str:
    label = match.group(1)
    url = match.group(2)
    return f'<a href="{url}" target="_blank" rel="noopener noreferrer">{label}</a>'


def render_inline(text: str) -> str:
    """Render inline Markdown (links, bold, italic, code) to HTML."""
    masked, stashed = _stash_code_spans(text)
    escaped = escape(masked)
    # Inline links: [label](url)  (optional "title" ignored for simplicity)
    escaped = re.sub(
        r"\[([^\]]+)\]\(([^\s)]+)(?:\s+\"[^\"]*\")?\)",
        _link_replacement,
        escaped,
    )
    # Bold before italic so ** wins over *.
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"__(.+?)__", r"<strong>\1</strong>", escaped)
    escaped = re.sub(r"\*(.+?)\*", r"<em>\1</em>", escaped)
    escaped = re.sub(r"(?<!\w)_(.+?)_(?!\w)", r"<em>\1</em>", escaped)
    escaped = _restore_code_spans(escaped, stashed)
    return escaped


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.*)$")
_HR_RE = re.compile(r"^(\*{3,}|-{3,}|_{3,})$")
_UL_RE = re.compile(r"^\s*[-*+]\s+(.*)$")
_OL_RE = re.compile(r"^\s*\d+\.\s+(.*)$")


def render_markdown(md: str) -> str:
    """Render a small subset of Markdown to HTML.

    Supports paragraphs, headings, horizontal rules, blockquotes, and
    unordered / ordered lists alongside :func:`render_inline`.
    """
    lines = md.replace("\r\n", "\n").split("\n")
    html: list[str] = []
    paragraph: list[str] = []
    blockquote: list[str] = []
    list_items: list[tuple[str, str]] = []

    def flush_paragraph() -> None:
        if paragraph:
            html.append("<p>" + render_inline(" ".join(paragraph)) + "</p>")
            paragraph.clear()

    def flush_blockquote() -> None:
        if blockquote:
            html.append(
                "<blockquote><p>" + render_inline(" ".join(blockquote)) + "</p></blockquote>"
            )
            blockquote.clear()

    def flush_list() -> None:
        if not list_items:
            return
        ordered = all(kind == "ol" for kind, _ in list_items)
        tag = "ol" if ordered else "ul"
        items = "".join(f"<li>{render_inline(text)}</li>" for _, text in list_items)
        html.append(f"<{tag}>{items}</{tag}>")
        list_items.clear()

    def flush_all() -> None:
        flush_paragraph()
        flush_blockquote()
        flush_list()

    for raw in lines:
        line = raw.strip()

        if not line:
            flush_all()
            continue

        hr = _HR_RE.fullmatch(line)
        if hr:
            flush_all()
            html.append("<hr>")
            continue

        heading = _HEADING_RE.match(line)
        if heading:
            flush_all()
            level = len(heading.group(1))
            html.append(f"<h{level}>{render_inline(heading.group(2).strip())}</h{level}>")
            continue

        ul = _UL_RE.match(line)
        if ul:
            flush_paragraph()
            flush_blockquote()
            list_items.append(("ul", ul.group(1).strip()))
            continue

        ol = _OL_RE.match(line)
        if ol:
            flush_paragraph()
            flush_blockquote()
            list_items.append(("ol", ol.group(1).strip()))
            continue

        if line.startswith(">"):
            flush_paragraph()
            flush_list()
            blockquote.append(line.lstrip("> ").rstrip())
            continue

        # default: paragraph line
        flush_blockquote()
        flush_list()
        paragraph.append(line)

    flush_all()
    return "\n".join(html)

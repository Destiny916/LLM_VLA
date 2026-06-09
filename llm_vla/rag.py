"""Lightweight Markdown RAG helpers for harness knowledge files."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re


HEADING_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")
ASCII_TOKEN_RE = re.compile(r"[A-Za-z0-9_]+")
CJK_RE = re.compile(r"[\u4e00-\u9fff]+")


@dataclass(frozen=True)
class RagDocument:
    """A searchable Markdown chunk."""

    path: str
    title: str
    content: str
    summary: str


@dataclass(frozen=True)
class RagHit:
    """A ranked retrieval result."""

    path: str
    title: str
    content: str
    summary: str
    snippet: str
    score: int


def load_rag_documents(root: Path) -> list[RagDocument]:
    """Load Markdown files under root and split them by headings."""
    root = Path(root)
    documents: list[RagDocument] = []
    for path in sorted(root.rglob("*.md")):
        if not path.is_file():
            continue
        relative_path = path.relative_to(root).as_posix()
        documents.extend(_split_markdown(relative_path, path.read_text(encoding="utf-8")))
    return documents


def retrieve_context(query: str, documents: list[RagDocument], top_k: int = 5) -> list[RagHit]:
    """Return the highest scoring RAG chunks for a query."""
    terms = _query_terms(query)
    if not terms or top_k <= 0:
        return []

    hits: list[RagHit] = []
    for document in documents:
        score = _score_document(terms, document)
        if score <= 0:
            continue
        hits.append(
            RagHit(
                path=document.path,
                title=document.title,
                content=document.content,
                summary=document.summary,
                snippet=_snippet(document.content, terms),
                score=score,
            )
        )

    hits.sort(key=lambda hit: (-hit.score, hit.path, hit.title))
    return hits[:top_k]


def _split_markdown(relative_path: str, text: str) -> list[RagDocument]:
    chunks: list[tuple[str, list[str]]] = []
    current_title = Path(relative_path).stem
    current_lines: list[str] = []

    for line in text.splitlines():
        match = HEADING_RE.match(line)
        if match:
            if any(existing_line.strip() for existing_line in current_lines):
                chunks.append((current_title, current_lines))
            current_title = match.group(2).strip()
            current_lines = []
            continue
        current_lines.append(line)

    chunks.append((current_title, current_lines))

    documents: list[RagDocument] = []
    for title, lines in chunks:
        content = "\n".join(lines).strip()
        if not title and not content:
            continue
        summary = _summary(content)
        documents.append(RagDocument(path=relative_path, title=title, content=content, summary=summary))
    return documents


def _query_terms(query: str) -> list[str]:
    terms: set[str] = set()
    for token in ASCII_TOKEN_RE.findall(query.lower()):
        terms.add(token)
    for cjk_group in CJK_RE.findall(query):
        terms.add(cjk_group)
        for size in (2, 3, 4):
            for start in range(0, max(0, len(cjk_group) - size + 1)):
                terms.add(cjk_group[start : start + size])
    return sorted(terms, key=lambda term: (-len(term), term))


def _score_document(terms: list[str], document: RagDocument) -> int:
    title = document.title.lower()
    path = document.path.lower()
    content = document.content.lower()
    score = 0
    for term in terms:
        normalized = term.lower()
        if normalized == title:
            score += 24
        elif normalized in title:
            score += 8
        if normalized in path:
            score += 4
        if normalized in content:
            score += 2
            score += min(content.count(normalized), 3)
    return score


def _snippet(content: str, terms: list[str], width: int = 120) -> str:
    compact = " ".join(content.split())
    if len(compact) <= width:
        return compact

    lowered = compact.lower()
    best_index = -1
    for term in terms:
        index = lowered.find(term.lower())
        if index >= 0 and (best_index < 0 or index < best_index):
            best_index = index

    if best_index < 0:
        return compact[:width].rstrip()

    start = max(0, best_index - width // 3)
    end = min(len(compact), start + width)
    return compact[start:end].strip()


def _summary(content: str, width: int = 80) -> str:
    compact = " ".join(content.split())
    if len(compact) <= width:
        return compact
    return compact[:width].rstrip()

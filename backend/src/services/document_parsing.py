"""Local document text extraction for the MVP ingestion pipeline."""

from __future__ import annotations

import re
from pathlib import Path


class DocumentParseError(ValueError):
    """Raised when uploaded content cannot be converted to searchable text."""


SUPPORTED_EXTENSIONS = {".txt", ".md", ".markdown", ".pdf"}


def extract_text(path: Path) -> str:
    extension = path.suffix.lower()
    if extension in {".txt", ".md", ".markdown"}:
        return _normalize_text(path.read_text(encoding="utf-8-sig"))
    if extension == ".pdf":
        return _extract_pdf_text(path)
    raise DocumentParseError("不支持的文件类型")


def validate_supported_filename(filename: str) -> None:
    if Path(filename).suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise DocumentParseError("不支持的文件类型")


def _extract_pdf_text(path: Path) -> str:
    try:
        from pypdf import PdfReader
    except ImportError:
        return _extract_simple_pdf_text(path.read_bytes())

    try:
        reader = PdfReader(str(path))
        text = "\n".join(page.extract_text() or "" for page in reader.pages)
    except Exception as exc:
        raise DocumentParseError("PDF 文本抽取失败") from exc

    normalized = _normalize_text(text)
    if normalized:
        return normalized

    fallback = _extract_simple_pdf_text(path.read_bytes())
    if fallback:
        return fallback
    raise DocumentParseError("PDF 未包含可抽取文本")


def _extract_simple_pdf_text(content: bytes) -> str:
    try:
        raw_text = content.decode("latin-1")
    except UnicodeDecodeError as exc:
        raise DocumentParseError("PDF 文本抽取失败") from exc

    literals = re.findall(r"\(([^()]*)\)\s*Tj", raw_text)
    decoded_parts = [_decode_pdf_literal(value) for value in literals]
    normalized = _normalize_text("\n".join(decoded_parts))
    if not normalized:
        raise DocumentParseError("PDF 未包含可抽取文本")
    return normalized


def _decode_pdf_literal(value: str) -> str:
    return (
        value.replace(r"\(", "(")
        .replace(r"\)", ")")
        .replace(r"\\", "\\")
        .encode("latin-1", errors="ignore")
        .decode("utf-8", errors="ignore")
    )


def _normalize_text(value: str) -> str:
    return "\n".join(line.strip() for line in value.splitlines() if line.strip()).strip()

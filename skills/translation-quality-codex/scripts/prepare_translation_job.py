#!/usr/bin/env python3
"""Create a deterministic translation workspace from Markdown or plain text."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path


TEXT_EXTENSIONS = {".txt", ".md", ".markdown", ".rst"}
EXTRACTION_REQUIRED = {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}


def read_text(path: Path) -> str:
    for encoding in ("utf-8-sig", "utf-8"):
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue
    return path.read_text(encoding="cp1252")


def block_type(text: str) -> str:
    stripped = text.strip()
    if stripped.startswith("#"):
        return "heading"
    if stripped.startswith("|") and stripped.endswith("|"):
        return "table"
    if re.match(r"^(\s*[-*+]\s+|\s*\d+[.)]\s+)", stripped):
        return "list"
    if stripped.startswith("```"):
        return "code"
    return "paragraph"


def chunk_long_text(text: str, max_chars: int) -> list[str]:
    if len(text) <= max_chars or max_chars <= 0:
        return [text]
    sentences = re.split(r"(?<=[.!?。！？])\s+", text)
    chunks: list[str] = []
    current = ""
    for sentence in sentences:
        if not sentence:
            continue
        if len(sentence) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            for start in range(0, len(sentence), max_chars):
                chunks.append(sentence[start : start + max_chars].strip())
            continue
        candidate = f"{current} {sentence}".strip()
        if current and len(candidate) > max_chars:
            chunks.append(current.strip())
            current = sentence
        else:
            current = candidate
    if current:
        chunks.append(current.strip())
    return [chunk for chunk in chunks if chunk]


def split_blocks(text: str, max_chars: int) -> list[dict[str, str]]:
    raw_chunks = [chunk.strip() for chunk in re.split(r"\n\s*\n", text) if chunk.strip()]
    blocks: list[dict[str, str]] = []
    for chunk in raw_chunks:
        kind = block_type(chunk)
        subchunks = [chunk] if kind in {"heading", "table", "code"} else chunk_long_text(chunk, max_chars)
        for subchunk in subchunks:
            blocks.append({"id": f"S{len(blocks) + 1:04d}", "type": kind, "text": subchunk})
    return blocks


def write_json(path: Path, data: object) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def create_extraction_notice(source: Path, out_dir: Path, target_lang: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    notice = f"""# Extraction Required

Source: `{source}`
Target language: `{target_lang}`

This file type must be extracted before translation.

- PDF or scanned PDF: use the `pdf` skill/tool, then run this script on the extracted Markdown/text.
- DOCX: use the `documents` skill/tool, then run this script on the extracted Markdown/text.
- Full scientific paper needing bilingual anchors, figures, and tables: use `nature-reader` first, then polish selected blocks with this skill.
"""
    (out_dir / "INGESTION_REQUIRED.md").write_text(notice, encoding="utf-8")
    write_json(
        out_dir / "job_manifest.json",
        {
            "status": "extraction_required",
            "source": str(source),
            "target_language": target_lang,
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def create_workspace(source: Path, out_dir: Path, source_lang: str, target_lang: str, max_block_chars: int) -> None:
    text = read_text(source)
    blocks = split_blocks(text, max_block_chars)
    out_dir.mkdir(parents=True, exist_ok=True)

    write_json(
        out_dir / "source_blocks.json",
        {
            "source": str(source),
            "source_language": source_lang,
            "target_language": target_lang,
            "max_block_chars": max_block_chars,
            "block_count": len(blocks),
            "blocks": blocks,
        },
    )
    write_json(out_dir / "terminology-glossary.json", {"terms": []})

    translation_lines = [
        "# Aligned Translation",
        "",
        f"Source: `{source}`",
        f"Target language: `{target_lang}`",
        "",
    ]
    for block in blocks:
        translation_lines.extend([f"## {block['id']}", "", "<translation pending>", ""])
    (out_dir / "translation_aligned.md").write_text("\n".join(translation_lines), encoding="utf-8")

    (out_dir / "translation.md").write_text(
        "# Translation\n\n"
        "Human-readable translation pending. Finalize `translation_aligned.md`, then run "
        "`scripts/build_readable_output.py` to generate this file.\n",
        encoding="utf-8",
    )

    (out_dir / "review-feedback.md").write_text(
        "# Review Feedback\n\nNo review has been performed yet.\n",
        encoding="utf-8",
    )
    (out_dir / "translation_notes.md").write_text(
        "# Translation Notes\n\n"
        "- Multi-role workflow status: pending.\n"
        "- Extraction notes: source was Markdown/plain text.\n",
        encoding="utf-8",
    )
    write_json(
        out_dir / "job_manifest.json",
        {
            "status": "ready_for_translation",
            "source": str(source),
            "source_language": source_lang,
            "target_language": target_lang,
            "max_block_chars": max_block_chars,
            "block_count": len(blocks),
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("--out-dir", type=Path, required=True)
    parser.add_argument("--source-lang", default="auto")
    parser.add_argument("--target-lang", default="zh-CN")
    parser.add_argument("--max-block-chars", type=int, default=1800)
    args = parser.parse_args()

    source = args.source.resolve()
    out_dir = args.out_dir.resolve()
    if not source.exists():
        parser.error(f"source does not exist: {source}")

    suffix = source.suffix.lower()
    if suffix in EXTRACTION_REQUIRED:
        create_extraction_notice(source, out_dir, args.target_lang)
        print(f"extraction_required: {out_dir}")
        return 2
    if suffix not in TEXT_EXTENSIONS:
        parser.error(f"unsupported source extension: {suffix or '<none>'}")

    create_workspace(source, out_dir, args.source_lang, args.target_lang, args.max_block_chars)
    print(f"ready_for_translation: {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

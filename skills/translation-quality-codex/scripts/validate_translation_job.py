#!/usr/bin/env python3
"""Validate a translation-quality-codex output package."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_FILES = [
    "source_blocks.json",
    "terminology-glossary.json",
    "review-feedback.md",
    "translation_notes.md",
]


def load_json(path: Path) -> object:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("out_dir", type=Path)
    args = parser.parse_args()

    out_dir = args.out_dir.resolve()
    errors: list[str] = []

    if not out_dir.exists():
        parser.error(f"output directory does not exist: {out_dir}")

    for filename in REQUIRED_FILES:
        if not (out_dir / filename).exists():
            errors.append(f"missing required file: {filename}")

    source_blocks_path = out_dir / "source_blocks.json"
    glossary_path = out_dir / "terminology-glossary.json"
    aligned_path = out_dir / "translation_aligned.md"
    legacy_translation_path = out_dir / "translation.md"
    readable_translation_path = out_dir / "translation.md"

    if not aligned_path.exists() and not legacy_translation_path.exists():
        errors.append("missing required file: translation_aligned.md or legacy translation.md")

    blocks = []
    if source_blocks_path.exists():
        try:
            source_data = load_json(source_blocks_path)
            blocks = source_data.get("blocks", []) if isinstance(source_data, dict) else []
            if not blocks:
                errors.append("source_blocks.json has no blocks")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"source_blocks.json is invalid JSON: {exc}")

    if glossary_path.exists():
        try:
            glossary = load_json(glossary_path)
            if not isinstance(glossary, dict):
                errors.append("terminology-glossary.json must be a JSON object")
        except Exception as exc:  # noqa: BLE001
            errors.append(f"terminology-glossary.json is invalid JSON: {exc}")

    aligned_text = ""
    aligned_label = "translation_aligned.md"
    if aligned_path.exists():
        aligned_text = aligned_path.read_text(encoding="utf-8")
    elif legacy_translation_path.exists():
        aligned_text = legacy_translation_path.read_text(encoding="utf-8")
        aligned_label = "translation.md"

    missing_ids = [
        block.get("id", "<missing-id>")
        for block in blocks
        if isinstance(block, dict) and block.get("id") not in aligned_text
    ]
    if missing_ids:
        errors.append(f"{aligned_label} is missing source block IDs: " + ", ".join(missing_ids[:20]))

    if "<translation pending>" in aligned_text:
        errors.append(f"{aligned_label} still contains '<translation pending>' placeholders")

    if aligned_path.exists() and readable_translation_path.exists():
        readable_text = readable_translation_path.read_text(encoding="utf-8")
        if "Human-readable translation pending" in readable_text:
            errors.append("translation.md has not been generated as a human-readable deliverable")
        if "## S0001" in readable_text or "\n## S" in readable_text:
            errors.append("translation.md still appears to expose internal source block headings")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"VALID: {out_dir} ({len(blocks)} blocks)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

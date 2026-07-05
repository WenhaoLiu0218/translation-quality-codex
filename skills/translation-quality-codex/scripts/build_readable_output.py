#!/usr/bin/env python3
"""Build clean Markdown and optional PDF from an aligned translation package."""

from __future__ import annotations

import argparse
import html
import json
import os
import mimetypes
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen


BLOCK_RE = re.compile(r"^##\s+(S\d{4,})\s*$", re.MULTILINE)
CJK = r"\u4e00-\u9fff"
IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".tif", ".tiff"}
SOURCE_LABEL_RE = re.compile(
    r"(?:source\s+pdf|source\s+file|original\s+source|source)\s*:\s*`([^`]+)`",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class Figure:
    block_id: str
    path: Path
    label: str
    caption: str = ""


def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def optional_fix_text(text: str) -> str:
    try:
        from ftfy import fix_text  # type: ignore
    except Exception:  # noqa: BLE001
        return text
    return fix_text(text)


def polish_cjk_punctuation(text: str) -> str:
    """Repair common ASCII punctuation artifacts between CJK characters."""

    def polish_line(line: str) -> str:
        prefix = ""
        for marker in ("### ", "## ", "# ", "- "):
            if line.startswith(marker):
                prefix = marker
                line = line[len(marker) :]
                break
        line = re.sub(rf"(?<=[{CJK}])\s*,\s*(?=[{CJK}])", "\uff0c", line)
        line = re.sub(rf"(?<=[{CJK}])\s*;\s*(?=[{CJK}])", "\uff1b", line)
        line = re.sub(rf"(?<=[{CJK}])\s*:\s*(?=[{CJK}])", "\uff1a", line)
        line = re.sub(rf"(?<=[{CJK}])\s*\(\s*(?=[{CJK}])", "\uff08", line)
        line = re.sub(rf"(?<=[{CJK}])\s*\)\s*(?=[{CJK}])", "\uff09", line)
        line = re.sub(rf"(?<=[{CJK}])\s*\)\s*$", "\uff09", line)
        return prefix + line

    return "\n".join(polish_line(line) for line in text.splitlines())


def parse_aligned_translation(text: str) -> list[tuple[str, str]]:
    matches = list(BLOCK_RE.finditer(text))
    blocks: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        block_id = match.group(1)
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        body = text[start:end].strip()
        if not body or body == "<translation pending>":
            continue
        body = polish_cjk_punctuation(optional_fix_text(body)).strip()
        blocks.append((block_id, body))
    return blocks


def choose_aligned_path(job_dir: Path, explicit: Path | None) -> Path:
    if explicit:
        return explicit.resolve()
    preferred = job_dir / "translation_aligned.md"
    if preferred.exists():
        return preferred
    legacy = job_dir / "translation.md"
    if legacy.exists():
        return legacy
    raise FileNotFoundError(f"no aligned translation found in {job_dir}")


def load_json(path: Path) -> dict[str, object]:
    if not path.exists():
        return {}
    data = json.loads(path.read_text(encoding="utf-8"))
    return data if isinstance(data, dict) else {}


def source_from_blocks(source_blocks: dict[str, object]) -> str:
    for block in source_blocks.get("blocks", [])[:30] if isinstance(source_blocks.get("blocks"), list) else []:
        if not isinstance(block, dict):
            continue
        text = str(block.get("text") or "")
        match = SOURCE_LABEL_RE.search(text)
        if match:
            return match.group(1).strip()
    return str(source_blocks.get("source") or "").strip()


def job_metadata(job_dir: Path, explicit_title: str) -> dict[str, object]:
    source_blocks = load_json(job_dir / "source_blocks.json")
    manifest = load_json(job_dir / "job_manifest.json")
    source = source_from_blocks(source_blocks) or str(manifest.get("source") or "").strip()
    target_language = str(source_blocks.get("target_language") or manifest.get("target_language") or "target").strip()
    source_language = str(source_blocks.get("source_language") or manifest.get("source_language") or "auto").strip()
    block_count = int(source_blocks.get("block_count") or manifest.get("block_count") or 0)
    return {
        "source": source,
        "source_language": source_language,
        "target_language": target_language,
        "block_count": block_count,
        "title": explicit_title,
    }


def stem_from_source(source: str) -> str:
    if not source:
        return "translation"
    if is_url(source):
        parsed = urlparse(source)
        name = Path(parsed.path).stem
        if name:
            return name
        return parsed.netloc or "translation"
    return Path(source).stem or "translation"


def safe_slug(value: str, default: str = "translation", max_length: int = 96) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "-", value).strip(".-_")
    value = re.sub(r"-{2,}", "-", value)
    if not value:
        value = default
    return value[:max_length].strip(".-_") or default


def readable_output_base(metadata: dict[str, object], override: str | None) -> str:
    if override:
        return safe_slug(override, default="translation")
    source_stem = safe_slug(stem_from_source(str(metadata.get("source") or "")), default="translation")
    target_lang = safe_slug(str(metadata.get("target_language") or "target"), default="target", max_length=24)
    return f"{source_stem}.{target_lang}.readable"


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"}


def suffix_from_url(url: str) -> str:
    parsed = urlparse(url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix in IMAGE_EXTENSIONS:
        return suffix
    guessed = mimetypes.guess_extension(mimetypes.guess_type(url)[0] or "")
    return guessed if guessed in IMAGE_EXTENSIONS else ".png"


def download_file(url: str, dest: Path) -> None:
    request = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urlopen(request, timeout=90) as response:
        dest.write_bytes(response.read())


def stable_destination(directory: Path, preferred_name: str, used_names: set[str]) -> Path:
    stem = Path(preferred_name).stem or "figure"
    suffix = Path(preferred_name).suffix.lower() or ".png"
    name = f"{stem}{suffix}"
    candidate = directory / name
    counter = 2
    while name.lower() in used_names:
        name = f"{stem}-{counter}{suffix}"
        candidate = directory / name
        counter += 1
    used_names.add(name.lower())
    return candidate


def materialize_figure(source: str, manifest_dir: Path, figures_dir: Path, label: str, used_names: set[str]) -> Path:
    figures_dir.mkdir(parents=True, exist_ok=True)
    if is_url(source):
        parsed_name = Path(urlparse(source).path).name or f"{label}{suffix_from_url(source)}"
        dest = stable_destination(figures_dir, parsed_name, used_names)
        download_file(source, dest)
        return dest

    source_path = Path(source)
    if not source_path.is_absolute():
        source_path = manifest_dir / source_path
    source_path = source_path.resolve()
    if not source_path.exists():
        raise FileNotFoundError(f"figure not found: {source_path}")
    dest = stable_destination(figures_dir, source_path.name, used_names)
    if source_path.resolve() != dest.resolve():
        shutil.copy2(source_path, dest)
    return dest


def normalize_figure_items(data: object) -> list[dict[str, object]]:
    if isinstance(data, list):
        return [item for item in data if isinstance(item, dict)]
    if isinstance(data, dict) and isinstance(data.get("figures"), list):
        return [item for item in data["figures"] if isinstance(item, dict)]
    if isinstance(data, dict):
        items: list[dict[str, object]] = []
        for block_id, value in data.items():
            values = value if isinstance(value, list) else [value]
            for entry in values:
                if isinstance(entry, str):
                    items.append({"block_id": block_id, "path": entry})
                elif isinstance(entry, dict):
                    merged = dict(entry)
                    merged.setdefault("block_id", block_id)
                    items.append(merged)
        return items
    raise ValueError("figure manifest must be a list, an object with figures, or a block-id mapping")


def load_figures(manifest_path: Path | None, figures_dir: Path) -> dict[str, list[Figure]]:
    if not manifest_path:
        return {}
    manifest_path = manifest_path.resolve()
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    figures: dict[str, list[Figure]] = {}
    used_names: set[str] = set()
    for index, item in enumerate(normalize_figure_items(data), start=1):
        block_id = str(item.get("block_id") or "").strip()
        source = str(item.get("path") or item.get("source") or item.get("url") or "").strip()
        if not block_id or not source:
            raise ValueError(f"figure item {index} needs block_id and path/source/url")
        label = str(item.get("label") or f"Figure {index}").strip()
        caption = str(item.get("caption") or "").strip()
        path = materialize_figure(source, manifest_path.parent, figures_dir, label, used_names)
        figures.setdefault(block_id, []).append(Figure(block_id=block_id, path=path, label=label, caption=caption))
    return figures


def markdown_image(figure: Figure, out_dir: Path) -> str:
    rel = Path(os.path.relpath(figure.path, out_dir)).as_posix()
    caption = figure.caption or f"Original figure: {figure.label}"
    return f"![{figure.label}]({rel})\n\n*{caption}*"


def delivery_note(metadata: dict[str, object], figure_count: int) -> str:
    source = str(metadata.get("source") or "unknown")
    source_language = str(metadata.get("source_language") or "auto")
    target_language = str(metadata.get("target_language") or "target")
    block_count = metadata.get("block_count") or "unknown"
    return "\n".join(
        [
            "## \u4ea4\u4ed8\u8bf4\u660e",
            "",
            "- \u8fd9\u662f\u9762\u5411\u9605\u8bfb\u7684\u8bd1\u6587\u7248\uff0c\u5df2\u79fb\u9664 `S0001` \u7b49\u5185\u90e8\u5ba1\u6821\u951a\u70b9\uff1b\u5982\u9700\u9010\u6bb5\u6838\u5bf9\uff0c\u8bf7\u4f7f\u7528 `translation_aligned.md` \u548c `source_blocks.json`\u3002",
            f"- \u539f\u59cb\u6765\u6e90\uff1a`{source}`",
            f"- \u8bed\u8a00\u8def\u7531\uff1a`{source_language}` -> `{target_language}`\uff1b\u5bf9\u9f50\u6e90\u5757\u6570\uff1a`{block_count}`\uff1b\u5d4c\u5165\u539f\u56fe\u6570\uff1a`{figure_count}`\u3002",
            "- \u672c\u7248\u4fdd\u7559\u539f\u6587\u7684\u6570\u5b57\u3001\u5f15\u7528\u3001\u5355\u4f4d\u3001\u672f\u8bed\u548c\u56fe\u8868\u6307\u79f0\uff1b\u4e0d\u5c06\u8bd1\u6587\u4f5c\u4e3a\u539f\u6587\u51fa\u7248\u7269\u7684\u66ff\u4ee3\u5f15\u7528\u7248\u672c\u3002",
            "",
            "## \u6b63\u6587",
        ]
    )


def build_markdown(
    blocks: list[tuple[str, str]],
    figures: dict[str, list[Figure]],
    out_dir: Path,
    metadata: dict[str, object],
) -> str:
    figure_count = sum(len(value) for value in figures.values())
    lines = [
        delivery_note(metadata, figure_count),
        "",
    ]
    for block_id, body in blocks:
        for figure in figures.get(block_id, []):
            lines.extend([markdown_image(figure, out_dir), ""])
        lines.extend([body.strip(), ""])
    return "\n".join(lines).strip() + "\n"


def remove_markdown_inline(text: str) -> str:
    text = text.replace("`", "")
    text = re.sub(r"!\[[^\]]*\]\([^)]+\)", "", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    text = re.sub(r"\*([^*]+)\*", r"\1", text)
    text = text.replace("\\(", "(").replace("\\)", ")")
    return re.sub(r"\s+", " ", text).strip()


def choose_pdf_font():
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.cidfonts import UnicodeCIDFont
    from reportlab.pdfbase.ttfonts import TTFont

    for name, font_path in [
        ("MicrosoftYaHei", Path(r"C:\Windows\Fonts\msyh.ttc")),
        ("SimSun", Path(r"C:\Windows\Fonts\simsun.ttc")),
        ("SimHei", Path(r"C:\Windows\Fonts\simhei.ttf")),
    ]:
        if font_path.exists():
            try:
                pdfmetrics.registerFont(TTFont(name, str(font_path)))
                return name
            except Exception:  # noqa: BLE001
                continue
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("STSong-Light"))
        return "STSong-Light"
    except Exception:  # noqa: BLE001
        return "Helvetica"


def pdf_styles(font_name: str):
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_JUSTIFY, TA_LEFT
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet

    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "ReadableTitle",
            parent=base["Title"],
            fontName=font_name,
            fontSize=20,
            leading=26,
            alignment=TA_LEFT,
            spaceAfter=14,
            wordWrap="CJK",
        ),
        "h1": ParagraphStyle(
            "ReadableH1",
            parent=base["Heading1"],
            fontName=font_name,
            fontSize=16,
            leading=22,
            textColor=colors.HexColor("#1F2933"),
            spaceBefore=14,
            spaceAfter=8,
            wordWrap="CJK",
        ),
        "h2": ParagraphStyle(
            "ReadableH2",
            parent=base["Heading2"],
            fontName=font_name,
            fontSize=13,
            leading=18,
            textColor=colors.HexColor("#334E68"),
            spaceBefore=10,
            spaceAfter=6,
            wordWrap="CJK",
        ),
        "body": ParagraphStyle(
            "ReadableBody",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=10.2,
            leading=16,
            firstLineIndent=18,
            alignment=TA_JUSTIFY,
            spaceAfter=7,
            wordWrap="CJK",
        ),
        "list": ParagraphStyle(
            "ReadableList",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=10.2,
            leading=16,
            leftIndent=14,
            firstLineIndent=-10,
            alignment=TA_LEFT,
            spaceAfter=5,
            wordWrap="CJK",
        ),
        "caption": ParagraphStyle(
            "ReadableCaption",
            parent=base["BodyText"],
            fontName=font_name,
            fontSize=8.8,
            leading=12,
            textColor=colors.HexColor("#52606D"),
            spaceBefore=4,
            spaceAfter=8,
            wordWrap="CJK",
        ),
        "mono": ParagraphStyle(
            "ReadableMono",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.5,
            leading=10,
            leftIndent=4,
            spaceAfter=6,
        ),
    }


def clean_pdf_text(text: str) -> str:
    return html.escape(remove_markdown_inline(text))


def add_pdf_block(story: list, body: str, styles: dict) -> None:
    from reportlab.platypus import Paragraph, Preformatted, Spacer

    body = body.strip()
    if not body:
        return
    if body.startswith("# "):
        story.append(Paragraph(clean_pdf_text(body[2:]), styles["title"]))
        story.append(Spacer(1, 8))
        return
    if body.startswith("## "):
        story.append(Paragraph(clean_pdf_text(body[3:]), styles["h1"]))
        return
    if body.startswith("### "):
        story.append(Paragraph(clean_pdf_text(body[4:]), styles["h2"]))
        return
    if "\n|" in body or body.startswith("|"):
        story.append(Preformatted(remove_markdown_inline(body), styles["mono"]))
        return
    for paragraph in re.split(r"\n\s*\n", body):
        paragraph = paragraph.strip()
        if not paragraph:
            continue
        if paragraph.startswith("- "):
            story.append(Paragraph(clean_pdf_text("- " + paragraph[2:]), styles["list"]))
        else:
            story.append(Paragraph(clean_pdf_text(paragraph), styles["body"]))


def image_flowable(path: Path, max_width: float, max_height: float):
    from reportlab.platypus import Image

    image = Image(str(path))
    width = float(image.imageWidth)
    height = float(image.imageHeight)
    scale = min(max_width / width, max_height / height, 1.0)
    image.drawWidth = width * scale
    image.drawHeight = height * scale
    return image


def draw_page_number(canvas, doc) -> None:
    from reportlab.lib.pagesizes import A4

    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(A4[0] / 2, 24, str(doc.page))
    canvas.restoreState()


def add_pdf_delivery_note(story: list, styles: dict, metadata: dict[str, object], figure_count: int) -> None:
    from reportlab.platypus import Paragraph

    for line in delivery_note(metadata, figure_count).splitlines():
        line = line.strip()
        if not line:
            continue
        if line.startswith("## "):
            story.append(Paragraph(clean_pdf_text(line[3:]), styles["h1"]))
        elif line.startswith("- "):
            story.append(Paragraph(clean_pdf_text("- " + line[2:]), styles["list"]))


def build_pdf(
    blocks: list[tuple[str, str]],
    figures: dict[str, list[Figure]],
    pdf_path: Path,
    title: str,
    metadata: dict[str, object],
) -> None:
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError("PDF output requires reportlab") from exc

    font_name = choose_pdf_font()
    styles = pdf_styles(font_name)
    doc = SimpleDocTemplate(
        str(pdf_path),
        pagesize=A4,
        leftMargin=1.7 * cm,
        rightMargin=1.7 * cm,
        topMargin=1.65 * cm,
        bottomMargin=1.55 * cm,
        title=title,
        author="translation-quality-codex",
    )
    story: list = []
    max_width = A4[0] - doc.leftMargin - doc.rightMargin
    max_height = 17.0 * cm
    add_pdf_delivery_note(story, styles, metadata, sum(len(value) for value in figures.values()))
    for block_id, body in blocks:
        for figure in figures.get(block_id, []):
            story.append(Spacer(1, 6))
            story.append(image_flowable(figure.path, max_width, max_height))
            story.append(Paragraph(clean_pdf_text(figure.caption or f"Original figure: {figure.label}"), styles["caption"]))
            story.append(Spacer(1, 6))
        add_pdf_block(story, body, styles)
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    doc.build(story, onFirstPage=draw_page_number, onLaterPages=draw_page_number)


def validate_clean_markdown(markdown: str) -> list[str]:
    errors: list[str] = []
    if "\n## S" in markdown or markdown.startswith("## S"):
        errors.append("readable markdown still exposes internal source block headings")
    if "<translation pending>" in markdown:
        errors.append("readable markdown still contains translation placeholders")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-dir", type=Path, required=True)
    parser.add_argument("--aligned", type=Path)
    parser.add_argument("--out-dir", type=Path)
    parser.add_argument("--figure-manifest", type=Path)
    parser.add_argument("--pdf", action="store_true")
    parser.add_argument("--output-stem", help="Override source-derived readable output stem")
    parser.add_argument("--title", default="Readable Translation")
    args = parser.parse_args()

    job_dir = args.job_dir.resolve()
    out_dir = (args.out_dir or (job_dir / "readable")).resolve()
    figures_dir = out_dir / "assets" / "figures"
    aligned_path = choose_aligned_path(job_dir, args.aligned)
    metadata = job_metadata(job_dir, args.title)
    output_base = readable_output_base(metadata, args.output_stem)

    blocks = parse_aligned_translation(read_text(aligned_path))
    if not blocks:
        print(f"ERROR: no translated blocks found in {aligned_path}", file=sys.stderr)
        return 1

    figures = load_figures(args.figure_manifest, figures_dir)
    readable_markdown = build_markdown(blocks, figures, out_dir, metadata)
    root_markdown = build_markdown(blocks, figures, job_dir, metadata)
    errors = validate_clean_markdown(readable_markdown) + validate_clean_markdown(root_markdown)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    readable_md = out_dir / f"{output_base}.md"
    write_text(readable_md, readable_markdown)
    write_text(job_dir / "translation.md", root_markdown)

    outputs = [f"readable_md={readable_md}", f"translation_md={job_dir / 'translation.md'}"]
    if args.pdf:
        pdf_path = out_dir / f"{output_base}.pdf"
        try:
            build_pdf(blocks, figures, pdf_path, args.title, metadata)
        except Exception as exc:  # noqa: BLE001
            print(f"ERROR: failed to build PDF: {exc}", file=sys.stderr)
            return 1
        outputs.append(f"readable_pdf={pdf_path}")

    outputs.append(f"blocks={len(blocks)}")
    outputs.append(f"figures={sum(len(value) for value in figures.values())}")
    print("\n".join(outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

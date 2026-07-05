# Translation Quality Codex

`translation-quality-codex` is a Codex skill for rigorous Chinese-English and multilingual document translation, with a workflow tuned for scientific papers, grants, reports, formal documents, terminology-heavy text, and PDF/DOCX-derived sources.

It is adapted from the workflow ideas in `senshinji/claude-translation-skill`, but redesigned for Codex. It does not depend on Claude Code Agent Teams, Claude model names, or Claude-specific environment variables.

## What It Does

- Routes PDF, scanned PDF, DOCX, and full-paper sources through extraction before translation.
- Uses a mandatory multi-role workflow for long-form work: terminologist, translator, reviewer, and lead reviser.
- Builds and verifies a terminology glossary before final revision.
- Preserves structure, claims, numbers, units, citations, equations, tables, and figure references.
- Keeps an aligned audit translation with `S0001`-style source block IDs for QA.
- Produces clean human-readable Markdown without internal block IDs.
- Generates source-named readable PDFs when PDF output is requested or figure-aware source assets are available.
- Adds a delivery note to readable Markdown/PDF outputs with source identity, language route, block count, figure count, and audit-file references.

## Repository Layout

```text
.
+-- README.md
`-- skills/
    `-- translation-quality-codex/
        +-- SKILL.md
        +-- agents/
        |   `-- openai.yaml
        +-- references/
        `-- scripts/
```

The installable Codex skill is:

```text
skills/translation-quality-codex
```

## Installation

From another computer with Codex installed, use the built-in skill installer:

```powershell
python "$env:USERPROFILE\.codex\skills\.system\skill-installer\scripts\install-skill-from-github.py" `
  --repo WenhaoLiu0218/translation-quality-codex `
  --path skills/translation-quality-codex
```

If the repository is private, make sure that computer has GitHub access through Codex, `git`, or `GITHUB_TOKEN` / `GH_TOKEN`.

After installation, restart Codex so the skill is discovered.

## Usage

Invoke the skill in Codex:

```text
[$translation-quality-codex] 翻译这个 PDF，保留术语一致性，输出可读 Markdown 和 PDF。
```

For full scientific papers with figures and source-aware reading, a strong workflow is:

```text
用 $translation-quality-codex 翻译这个 PDF，先做抽取路由、术语验证、四角色审校，再输出源文件命名的可读 Markdown/PDF，并在能获取原图时嵌入原图。
```

The skill defaults to the full workflow for file-based, long-form, scientific, legal, grant, report, or publication-facing translation. Ask for quick mode only when you explicitly do not want subagents, review, or package validation.

## Output Contract

For long-form file-based work, the skill creates a package with files such as:

```text
source_blocks.json
translation_aligned.md
translation.md
terminology-glossary.json
review-feedback.md
translation_notes.md
readable/<source-stem>.<target-lang>.readable.md
readable/<source-stem>.<target-lang>.readable.pdf
readable/assets/figures/
```

Key distinction:

- `translation_aligned.md` is the audit file with `S0001`-style source block IDs.
- `translation.md` is the clean human-readable translation.
- `readable/*.pdf` is the reader-facing PDF, named from the original source file when possible.

Example output name:

```text
s41586-020-03171-x.zh-CN.readable.pdf
```

## PDF and DOCX Sources

This skill does not pretend that raw PDFs or DOCX files are plain text. It expects extraction first:

- PDF or scanned PDF: use Codex's `pdf` workflow/tool for OCR and layout-aware extraction.
- DOCX: use Codex's `documents` workflow/tool for structured extraction.
- Full scientific papers that need source anchors, figures, and later Q&A: use `nature-reader` first, then polish with this skill.

## Validation

The skill includes scripts for repeatable package creation and validation:

```powershell
python scripts/prepare_translation_job.py <source.md> --out-dir <job-dir>
python scripts/build_readable_output.py --job-dir <job-dir> --pdf
python scripts/validate_translation_job.py <job-dir>
```

Validation checks include:

- required files exist
- source block IDs are preserved in the aligned translation
- placeholders are removed
- readable Markdown does not expose internal `S0001` block headings
- JSON files are valid

## Notes

- Keep the `skills/translation-quality-codex/` folder as the installable skill path.
- Keep this README at the repository root for humans; it is not required inside the skill folder.
- For private repositories, every machine that installs the skill must have access to the repository.

---
name: translation-quality-codex
description: >
  Professional document and scientific translation workflow for Codex with default full-pipeline translation: ingestion/extraction routing, mandatory four-role execution, terminology verification, structure preservation, anti-fabrication review, final revision, clean human-readable deliverables, optional figure-aware PDF output, and package validation. Use for Chinese-English or multilingual translation where accuracy matters, including papers, abstracts, grants, reports, formal documents, technical docs, tables, captions, terminology-heavy passages, PDF/DOCX-derived text, or when the user asks for high-quality translation, term checking, translation review, bilingual comparison, or a rigorous alternative to a normal translation. Prefer nature-reader for full-paper bilingual readers with source maps and figure placement; use this skill for polished translation quality, terminology control, independent review, and automated translation-package validation.
---

# Translation Quality Codex

Use this skill to produce a controlled professional translation, not a casual paraphrase. The workflow is adapted from `senshinji/claude-translation-skill` for Codex: keep the terminology/review discipline, but do not rely on Claude Code Agent Teams, model names, or Claude-only environment variables.

## Default Invocation Policy

Treat any explicit invocation of `$translation-quality-codex` for file-based, long-form, scientific, legal, grant, report, or publication-facing translation as a request for the full pipeline by default:

1. route or extract the source
2. prepare `source_blocks.json`
3. run the four-role translation workflow
4. verify terminology and structure
5. perform independent review
6. finalize the aligned/audit translation
7. build a clean human-readable deliverable and validate the package

The user does not need to repeat "use mandatory multi-role subagents, extraction routing, terminology verification, review, and final validation." Use a reduced quick mode only when the user explicitly asks for quick translation, no review, no subagents, or chat-only output.

## Output Contract

For file-based or long-form work, create an output folder beside the source or under the working directory containing:

- `source_blocks.json` - normalized source blocks with stable IDs.
- `translation_aligned.md` - aligned/audit translation with every `S0001`-style source block ID preserved for review and validation.
- `translation.md` - clean human-readable final translation with source block IDs removed.
- `terminology-glossary.json` - verified recurring terms and confidence.
- `review-feedback.md` - omissions, hallucinations, terminology drift, and structure issues found before revision.
- `translation_notes.md` - scope, assumptions, uncertain terms, inaccessible sources, and skipped content.
- `readable/<source-stem>.<target-lang>.readable.md` - long-form reader copy when the job has many sections, figures, or formal formatting needs.
- `readable/<source-stem>.<target-lang>.readable.pdf` - PDF reader copy when the user asks for PDF or figure/layout-aware source assets are available.
- `readable/assets/figures/` - copied or extracted original figures when figure assets are available.

`S0001`-style IDs are internal QA anchors only. Do not make the anchor-heavy aligned file the main human deliverable unless the user explicitly asks for an audit transcript.

Readable file names should follow the original source identity, not a generic `translation_readable.pdf` name. Prefer the original PDF/DOCX basename when it is recorded in source blocks (for example `Source PDF: ...`); otherwise use `source_blocks.json` or `job_manifest.json`. Keep names filesystem-safe, for example `s41586-020-03171-x.zh-CN.readable.pdf`. Add a short delivery note at the start of readable Markdown/PDF outputs describing the source, language route, block count, figure count, and audit files.

For short excerpts in chat, return a compact terminology table, the final translation, and a brief review note. Do not expose long intermediate drafts unless the user asks.

## Automation Entry Point

For Markdown or plain-text sources, run `scripts/prepare_translation_job.py <source> --out-dir <output_dir>` before translation. It creates `source_blocks.json`, an aligned translation scaffold, glossary/review/note templates, and a manifest.

For PDF, scanned PDF, DOCX, or full-paper HTML, perform extraction first and then run the script on the extracted Markdown/text:

- PDF or scanned PDF: use the `pdf` skill/tool for OCR, text extraction, and layout-aware Markdown when visual layout matters.
- DOCX: use the `documents` skill/tool to extract text, comments, tables, and structure before translation.
- Scientific full paper needing bilingual source anchors, figure/table placement, or later paper Q&A: use `nature-reader` first, then polish selected blocks with this skill.

After producing and reviewing `translation_aligned.md`, run `scripts/build_readable_output.py --job-dir <output_dir> --pdf` when a readable package is needed. The script derives readable output names from the original source file; use `--output-stem <stem>` only when the user requests a specific naming convention. If original figures are available, pass a figure manifest with `--figure-manifest <json>`. Then run `scripts/validate_translation_job.py <output_dir>`. Fix missing block IDs in the aligned file, invalid JSON, unreadable deliverables, or missing required outputs before responding.

## Workflow

1. **Classify the source**
   - Identify source language, target language, domain, document type, length, and whether tables, captions, formulas, references, or figures must be preserved.
   - Enforce the ingestion gate above before translating PDFs, DOCX, scanned files, or full papers.
   - If the user wants a full-paper reader with source anchors and figure/table placement, run `nature-reader` before this skill rather than using this skill alone.

2. **Build a terminology ledger first**
   - Extract domain terms, abbreviations, named methods, datasets, genes/proteins, metrics, equations, organizations, people, places, and recurring concepts.
   - For high-value terms, verify official or field-standard translations with web/primary sources when available.
   - Save using `references/glossary-schema.md` when producing a file artifact.
   - Keep technical identifiers, formulas, gene/protein names, statistical notation, URLs, citations, and numeric values unchanged unless a standard translation is required.

3. **Translate with structure preservation**
   - Translate paragraph by paragraph or table cell by table cell.
   - Preserve headings, lists, tables, captions, code blocks, references, citation markers, units, and numbering.
   - Keep hedging and evidential strength intact: do not turn "may", "suggests", or "is associated with" into stronger causal claims.
   - Mark unclear source text rather than guessing.

4. **Review independently before finalizing**
   - Check against `references/anti-fabrication-checklist.md`.
   - Use `references/review-feedback-schema.md` for file artifacts.
   - Prioritize issues in this order: fabrication, omission, mistranslation, terminology inconsistency, structure loss, register/style.
   - Compare source and translation block by block. Count tables/rows/captions/lists where relevant.

5. **Revise and polish**
   - Apply glossary decisions and review fixes.
   - Make the target-language prose natural without adding content.
   - For Chinese academic translation, avoid translationese while preserving technical precision.
   - For English scientific translation, prefer concise, publication-appropriate English and keep claims bounded by the source.

6. **Build the reader deliverable**
   - Keep `translation_aligned.md` as the audit file with block IDs.
   - Generate a clean `translation.md` without `S0001`-style IDs.
   - For long papers, PDF/DOCX-derived sources, or figure-bearing scientific articles, create source-named readable outputs such as `readable/<source-stem>.<target-lang>.readable.md` and, when feasible, `readable/<source-stem>.<target-lang>.readable.pdf`.
   - Place original figures near the most relevant translated section when source figure assets are available.
   - Start readable Markdown/PDF outputs with a concise delivery note that explains source identity, language route, block count, figure count, and where the audit files live.
   - Do not expose internal chunking artifacts, placeholder IDs, or routing notes in the human-facing deliverable.

7. **Validate**
   - Confirm no source blocks were skipped.
   - Confirm every glossary term is used consistently.
   - Confirm tables, captions, numbers, citations, equations, and units survived unchanged.
   - Confirm the human-readable Markdown has no `S0001`-style section scaffolding.
   - For PDF output, render-check representative first, figure-heavy, and final pages with PyMuPDF or the available PDF tool.
   - Record remaining uncertainty in `translation_notes.md`.

## Mandatory Multi-Role Execution

For file-based, long-form, scientific, legal, grant, report, or publication-facing translation, use four roles. Start real Codex subagents when the user has explicitly requested subagents or the runtime allows the skill invocation to count as that request. If subagents are unavailable or policy blocks delegation, run the same roles serially in the main thread and record the fallback in `translation_notes.md`.

- Terminologist: extract and verify glossary terms before translation.
- Translator: produce the first structure-preserving translation against `source_blocks.json` as `translation_aligned.md`.
- Reviewer: audit source-to-target coverage, fabrication, omission, terminology, claim strength, tables, numbers, citations, equations, and units.
- Lead/reviser: merge terminology and review feedback into the final aligned translation, then build the clean reader deliverable.

Do not skip the four-role sequence for long-form work. For short chat excerpts, compress the roles into a compact internal pass and return only the final translation plus brief review note.

Recommended subagent prompts:

- Terminologist: "Use the source blocks and create/verify `terminology-glossary.json`. Do not translate the document."
- Translator: "Use `source_blocks.json` and the glossary to draft `translation.md` with every block ID preserved."
- Reviewer: "Audit `translation.md` against `source_blocks.json` and write `review-feedback.md`; prioritize hallucination, omission, mistranslation, terminology drift, and structure loss."
- Lead/reviser: "Apply the glossary and review feedback to finalize `translation.md`, then update `translation_notes.md`."

## Scaling Rules

Read `references/scaling-guidelines.md` when the source is longer than about 10 pages, has more than 50 important terms, or needs chunking. Keep chunks aligned to section boundaries and never split inside tables.

## Typesetting

Read `references/typesetting-rules.md` when the user asks for DOCX/PDF-style output, when the source is PDF/DOCX, or when the article includes figures/tables that should be shown in a reader copy. For ordinary short comparison tasks, Markdown is preferred.

## Comparison With Nature Reader

Use `nature-reader` when the deliverable is a paper companion: source anchors, page/block IDs, figures/tables near first mention, and full-paper bilingual reading.

Use this skill when the deliverable is a polished translation with explicit terminology verification and quality review.

For fair comparisons, translate the same excerpt with both workflows and score:

- terminology consistency
- faithfulness and claim strength
- readability in Chinese/English
- preservation of structure and citations
- auditability of source alignment

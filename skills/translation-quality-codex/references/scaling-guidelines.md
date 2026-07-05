# Scaling Guidelines — Chunked Translation for Long Documents

## Trigger Condition

Single translator handles ≤10 pages safely. Threshold estimates:
- ~350 paragraphs in HTML ≈ 10 pages
- ~5000 Chinese characters ≈ 10 pages
- ~35 paragraphs ≈ 1 page

If the source exceeds 10 pages, the Lead MUST chunk before spawning agents.

## Chapter Boundary Detection

Scan the HTML source and identify boundaries using these strategies (in priority order):

1. **HTML heading tags**: `<h1>`, `<h2>` — most reliable when present
2. **Word bold headings**: `<p>` with `<b>` or `font-weight:bold` and larger `font-size` — Word's heading style after `textutil -convert html`
3. **Chinese section numbering**: paragraphs starting with "一、" "二、" "三、" or "第一章" "第二章" etc.

Rules:
- NEVER split inside a `<table>...</table>` block
- NEVER split inside a paragraph
- Keep each chunk ≤10 pages
- If no clear boundaries exist, split at the nearest paragraph break after every ~350 paragraphs

## chunk-manifest.md Format

```markdown
# Chunk Manifest

Source: [filename] ([N] pages estimated, [N] paragraphs)
Chunks: [N]

| Chunk | File | Sections | Pages (est.) |
|-------|------|----------|-------------|
| 1 | chunks/chunk-1.html | 一、开幕式 — 三、主旨报告 | ~8 |
| 2 | chunks/chunk-2.html | 四、分组讨论 — 六、闭幕式 | ~7 |
| 3 | chunks/chunk-3.html | 附录A — 附录C | ~5 |
```

## Merge Protocol (Phase 3.5)

After all chunk translators complete:

1. **Concatenate** in order: `first-pass-chunk-1.md` + `first-pass-chunk-2.md` + ... → `first-pass.md`
2. **Seam check**: scan each join point for:
   - Duplicate headings (same heading at end of chunk N and start of chunk N+1)
   - Broken numbering (e.g., list restarting at 1 instead of continuing)
   - Orphaned references (e.g., "see above" pointing across chunk boundary)
3. Fix any seam issues before passing to reviewer

## Scaling Table

| Document Size | Est. Terms | Chunks | Translators | term-researchers | Reviewers |
|--------------|-----------|--------|-------------|-----------------|-----------|
| ≤5 pages | ≤40 | 1 (no split) | 1 | 1 | 1 |
| 6-10 pages | 50-100 | 1 (no split) | 1 | 1-2 (if >50) | 1 |
| 11-20 pages | 90-200 | 2 | 2 (parallel) | 2 (fast+deep) | 1 |
| 21-30 pages | 170-300 | 3 | 3 (parallel) | 2 (fast+deep) | 1 |
| 31-50 pages | 250-500 | 4-5 | 4-5 (parallel) | 2 (fast+deep) | 1 |
| >50 pages | 400+ | 5+ | 5+ (parallel) | 2 (fast+deep) | 2 |

## Architecture: Why Global Agents

**term-researcher is global** (1 instance, reads full source):
- Produces a single unified terminology glossary
- All translators read the same glossary → consistent terminology across chunks
- No risk of chunk-A translating "协会" differently from chunk-B

**reviewer is global** (1 instance, reads merged first-pass.md):
- Reviews the complete document as a whole
- Can catch cross-chunk inconsistencies (tone shifts, repeated content, missing transitions)
- Produces one unified review-feedback.md

**revision is single** (translator-1 applies all fixes):
- One agent reads the full review feedback and applies corrections consistently
- Avoids conflicting fixes from multiple revisers

## Multi-Terminology Documents (>50 terms)

### Estimation Method
Scan the source document; expect ~8-10 proper nouns per page. A 10-page document typically yields 80-100 terms. If estimated total exceeds 50, spawn 2 term-researchers.

### Split Strategy: By Search Complexity (not by category)

The old category-based split (orgs+places vs persons+technical) created severe workload imbalance (30 vs 67 terms in testing). Instead, split by **search complexity**:

**term-researcher-fast** (Sonnet):
- Person names → Pinyin transliteration + quick verification (Google Scholar, ResearchGate)
- Place names, venue names, product names → generally straightforward
- Output: `/tmp/translation-workspace/glossary-fast.json`
- Expected: ~40 terms, lighter search load per term

**term-researcher-deep** (Sonnet):
- Organization names → need official website lookups, government databases
- Technical/specialized terms → need academic literature, industry standards
- Event/conference names → need industry association websites
- Output: `/tmp/translation-workspace/glossary-deep.json`
- Expected: ~47 terms, heavier search load per term (2-3 searches each)

### Lead Merge Protocol (Phase 1.5)

After both researchers complete:
1. Read `glossary-fast.json` and `glossary-deep.json`
2. Merge `terms` arrays, deduplicate by `original` field
3. Recalculate metadata totals (total_terms, high/medium/low counts)
4. Save merged result to `terminology-glossary.json`
5. Reviewer and translator-revision both read the merged file

**File conflict prevention**: Each researcher writes to its OWN file. Only the Lead writes `terminology-glossary.json`. No concurrent writes.

## Style-Sensitive Documents

Add 1 additional reviewer focused on readability and naturalness.
Original reviewer focuses on accuracy. Both write to `review-feedback.md` (separate sections).

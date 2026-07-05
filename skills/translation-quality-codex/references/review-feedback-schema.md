# Review Feedback Format

## Template

```markdown
## Review Feedback for [DOCUMENT_NAME]

**Source**: [source file path]
**Translation**: [translation file path]
**Glossary**: [glossary file path]
**Reviewer**: [reviewer agent name]
**Date**: [date]

---

### Critical Issues (MUST fix before release)

These are errors that make the translation incorrect or unreliable.

1. [Location: Section X, Para Y / Table Z, Row N]
   **TYPE**: "problematic text in translation"
   — Source says: "对应原文"
   — Fix: "corrected translation"

### Major Issues (SHOULD fix)

These are errors that reduce quality but don't make the translation wrong.

1. [Location: Section X, Para Y]
   **TYPE**: "problematic text"
   — Issue: description of the problem
   — Fix: "suggested correction"

### Minor Issues (CONSIDER fixing)

These are style or register suggestions that would improve polish.

1. [Location: Section X, Para Y]
   **TYPE**: "current text"
   — Suggestion: "improved alternative"

---

### Statistics

| Metric | Value |
|--------|-------|
| Critical issues | N |
| Major issues | N |
| Minor issues | N |
| Fabricated content found | yes/no |
| Omitted content found | yes/no |
| Terminology compliance | N/M terms correct (X%) |
| Structure compliance | [N]/[N] tables match, [N] boundary violations |
| Overall assessment | pass / pass with fixes / fail |

---

### Issue Type Reference

Priority order (highest to lowest):

| Type | Severity | Description |
|------|----------|-------------|
| FABRICATION | Critical | Content in translation not present in source |
| OMISSION | Critical | Source content missing from translation |
| TERMINOLOGY | Major | Term doesn't match verified glossary |
| ACCURACY | Major | Numbers, dates, names don't match source |
| STRUCTURE | Critical | Layout deviates from source structure |
| REGISTER | Minor | Style/tone inappropriate for document type |
```

## Structure Comparison Table

The reviewer MUST include a Structure Comparison Table in every review. This table independently verifies the translator's structure-report.md against the lead's structure-manifest.md.

```markdown
### Structure Comparison Table

| Element | Source | Translation | Match? |
|---------|--------|-------------|--------|
| Table 1 rows | 5 | 5 | YES |
| Table 1 cols | 3 | 3 | YES |
| Table 2 rows | 8 | 8 | YES |
| Table 3 cell R2 (multi-item) | 10 items inside | 10 items inside | YES |
| Table 3 cell R2 (multi-item) | 10 items inside | 3 inside, 7 outside | NO |
| Free text "Dining" section | free text | converted to table | NO |

Any "NO" entry is a **CRITICAL** issue and must appear in the Critical Issues section.
```

## Example

```markdown
## Review Feedback for 第六届蜂王浆大会指南

**Source**: /tmp/translation-workspace/source.doc
**Translation**: /tmp/translation-workspace/first-pass.md
**Glossary**: /tmp/translation-workspace/terminology-glossary.json
**Reviewer**: reviewer
**Date**: 2026-03-11

---

### Critical Issues (MUST fix before release)

1. [Location: Page 2, Schedule Table, Row 5]
   **FABRICATION**: "The expo attracted over 500 exhibitors from 30 countries"
   — Source says: "近百家参展商参展" (nearly 100 exhibitors)
   — Fix: "Nearly 100 exhibitors participated in the exhibition"

2. [Location: Page 3, Para 2]
   **OMISSION**: Source paragraph about registration fees is missing entirely
   — Source says: "注册费用：正式代表1200元/人，学生代表600元/人"
   — Fix: Add "Registration fee: 1,200 RMB per regular delegate, 600 RMB per student delegate"

### Major Issues (SHOULD fix)

1. [Location: Page 1, Header]
   **TERMINOLOGY**: "China Bee Product Committee"
   — Glossary specifies: "China Bee Products Association (CBPA)" (high confidence)
   — Fix: Replace with glossary term

2. [Location: Page 2, Schedule Table, Row 3]
   **ACCURACY**: "March 16, 2025"
   — Source says: "2025年3月15日"
   — Fix: "March 15, 2025"

3. [Location: Throughout]
   **STRUCTURE**: Schedule table has 12 rows but source has 14 rows — 2 meal break rows were extracted as free text below the table
   — Fix: Move meal break rows back into the table

### Minor Issues (CONSIDER fixing)

1. [Location: Page 1, Welcome section]
   **REGISTER**: "Hey everyone, welcome to the conference!"
   — Suggestion: "Distinguished guests and delegates, welcome to the Sixth Royal Jelly Conference"

---

### Statistics

| Metric | Value |
|--------|-------|
| Critical issues | 2 |
| Major issues | 3 |
| Minor issues | 1 |
| Fabricated content found | yes |
| Omitted content found | yes |
| Terminology compliance | 8/12 terms correct (67%) |
| Structure compliance | no (table row mismatch) |
| Overall assessment | pass with fixes |
```

# Anti-Fabrication Checklist

Fabrication — adding content that doesn't exist in the source — is the #1 quality risk in AI translation. This checklist provides systematic methods to prevent and detect it.

## Prevention Techniques (for translator)

### Before Translating

- [ ] Read the ENTIRE source document first, noting its scope and boundaries
- [ ] Identify the document type and expected content patterns
- [ ] Note any areas that are unclear or hard to read — mark these early

### During Translation

- [ ] Translate paragraph by paragraph, maintaining 1:1 correspondence
- [ ] For each paragraph: re-read the source, then write the translation
- [ ] If you're unsure about a term, mark it: `[?原文?]`
- [ ] If content is unclear in the source, mark it: `[unclear in original]`
- [ ] NEVER add explanatory content not present in the source
- [ ] NEVER "round up" or "round down" numbers — copy exactly
- [ ] NEVER substitute a generic description for specific content

### Specific High-Risk Areas

| Risk Area | Wrong Approach | Correct Approach |
|-----------|---------------|------------------|
| Numbers | "approximately 500" when source says "近百" | "nearly 100" |
| Person names | Inventing "John Smith" for 张伟 | "Zhang Wei" (transliterate) |
| Organization names | Guessing the English name | Search for official English name, or transliterate |
| Venue names | Translating 美泉宫厅 as "Schönbrunn Palace" | "Meiquangong Hall" (it's a room name) |
| Missing content | Making up plausible content to fill a gap | "[content unclear in original]" |
| Statistics | Adding percentages or comparisons not in source | Only translate what's stated |
| Quotes | Paraphrasing or embellishing a quote | Translate the exact quote |
| Dates | Converting to a different date | Preserve the exact date, just change format |

## Detection Techniques (for reviewer)

### Systematic Comparison Method

1. **Forward pass** (translation → source):
   - For each paragraph in the translation, locate the corresponding source paragraph
   - Flag any translation paragraph that has no source correspondent
   - Flag any content within a paragraph that exceeds what the source says

2. **Backward pass** (source → translation):
   - For each paragraph in the source, locate the corresponding translation paragraph
   - Flag any source paragraph that has no translation correspondent (omission)

3. **Numerical verification**:
   - List every number in the source: dates, quantities, percentages, phone numbers, booth numbers
   - Verify each number appears identically in the translation
   - Flag any number in the translation not present in the source

4. **Proper noun verification**:
   - Cross-reference every proper noun against the terminology glossary
   - Flag any proper noun in the translation that doesn't match the glossary or source

### Red Flags for Fabrication

Watch for these patterns that often indicate fabricated content:

- **Suspiciously specific details**: "500 exhibitors from 30 countries" when the source is vague
- **Evaluative language not in source**: "warmly received", "groundbreaking research", "highly successful"
- **Contextual additions**: Adding "the largest of its kind in Asia" when source doesn't say this
- **Logical inferences presented as facts**: Source says "many attended" → translation says "over 2,000 participants"
- **Embellished quotes**: Source has a simple statement → translation adds emotional language
- **Extra rows/columns in tables**: Translation table has more data than source table
- **Additional bullet points**: Translation list has more items than source list

### Severity Classification

| Fabrication Type | Severity | Example |
|-----------------|----------|---------|
| Invented facts/numbers | Critical | Adding attendee count not in source |
| Invented names/organizations | Critical | Adding sponsors not in source |
| Content padding (evaluative) | Major | Adding "highly successful" |
| Minor embellishment | Minor | "said" → "enthusiastically remarked" |
| Structural addition | Major | Adding a table row not in source |

## Post-Review Verification

After the translator applies review corrections:

- [ ] Re-check all items that were flagged as FABRICATION — are they fixed?
- [ ] Re-check all items that were flagged as OMISSION — are they restored?
- [ ] Spot-check 5 random paragraphs one more time
- [ ] Verify total page/section count matches between source and final translation

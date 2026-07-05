# Professional Typesetting Rules

These rules produce clean, formal document output suitable for conference proceedings, government reports, academic papers, and professional business documents.

## Font Specification

| Context | Font | Fallback |
|---------|------|----------|
| English text (all elements) | Times New Roman | serif |
| Chinese text (all elements) | SimSun (宋体) | STSong, Songti SC |

## Size and Weight Hierarchy

| Element | Size (pt) | Weight | Additional |
|---------|-----------|--------|------------|
| Document Title | 22 | Bold | Centered, 24pt space after |
| Section Heading (H1) | 16 | Bold | 18pt space before, 12pt after |
| Subsection Heading (H2) | 14 | Bold | 14pt space before, 8pt after |
| Sub-subsection (H3) | 12 | Bold | 10pt space before, 6pt after |
| Body Text | 12 | Regular | 1.25x line spacing, 6pt after |
| Table Header | 11 | Bold | Centered |
| Table Body | 10.5 | Regular | Left-aligned by default |
| Caption / Footnote | 9 | Regular | Italic for English |
| Page Header / Footer | 9 | Regular | Gray (#666666) |

## Page Layout (A4)

| Property | Value |
|----------|-------|
| Page Size | A4 (210mm × 297mm) / 11906 × 16838 DXA |
| All Margins | 1 inch (2.54cm) / 1440 DXA |
| Content Width | 9026 DXA |

For US Letter: 12240 × 15840 DXA, content width 9360 DXA.

## Table Design — "Structured Minimalism"

- Borders: thin single (#999999, size 1) for all cell borders
- Header row: light gray background (#E8E8E8), bold text, centered
- Body rows: white background, left-aligned text by default
- Alternating rows: optional very subtle gray (#F5F5F5) for long tables (>8 rows)
- Cell padding: top/bottom 80 DXA, left/right 120 DXA
- Column alignment: numbers right-aligned, text left-aligned, short labels centered
- Table width: always full content width
- No decorative elements: no colored borders, heavy rules, or shadows

## Paragraph Spacing

- Between paragraphs: 6pt (120 DXA) after
- Before H1: 18pt (360 DXA)
- Before H2: 14pt (280 DXA)
- Line spacing: 1.25x (300 twips for 12pt text)
- First-line indent: optional, 480 DXA (1/3 inch) for body paragraphs
- List items: 3pt (60 DXA) after each item; 6pt before first item

## Page Numbers

- Bottom center, 9pt, Times New Roman
- Format: "— 1 —" or simply "1"

## Headers/Footers

- Header: document title or section title, 9pt gray (#666666), thin bottom border
- Footer: page number centered, optional organization name left-aligned 9pt gray

## DOCX Implementation (docx-js)

```javascript
const styles = {
  default: {
    document: {
      run: { font: "Times New Roman", size: 24 } // 12pt
    }
  },
  paragraphStyles: [
    {
      id: "Heading1", name: "Heading 1",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 32, bold: true, font: "Times New Roman" },
      paragraph: { spacing: { before: 360, after: 240 }, outlineLevel: 0 }
    },
    {
      id: "Heading2", name: "Heading 2",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 28, bold: true, font: "Times New Roman" },
      paragraph: { spacing: { before: 280, after: 160 }, outlineLevel: 1 }
    },
    {
      id: "Heading3", name: "Heading 3",
      basedOn: "Normal", next: "Normal", quickFormat: true,
      run: { size: 24, bold: true, font: "Times New Roman" },
      paragraph: { spacing: { before: 200, after: 120 }, outlineLevel: 2 }
    }
  ]
};

// Body paragraph spacing
// spacing: { after: 120, line: 300 } // 6pt after, 1.25x line height

// Table border standard
const border = { style: BorderStyle.SINGLE, size: 1, color: "999999" };
const borders = { top: border, bottom: border, left: border, right: border };

// Header cell shading
// shading: { fill: "E8E8E8", type: ShadingType.CLEAR }
```

## PDF Implementation (reportlab)

```python
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY

styles = {
    'Title': ParagraphStyle(
        'Title', fontName='Times-Roman', fontSize=22,
        leading=28, alignment=TA_CENTER, spaceAfter=24,
    ),
    'Heading1': ParagraphStyle(
        'Heading1', fontName='Times-Bold', fontSize=16,
        leading=20, alignment=TA_LEFT, spaceBefore=18, spaceAfter=12,
    ),
    'Heading2': ParagraphStyle(
        'Heading2', fontName='Times-Bold', fontSize=14,
        leading=18, alignment=TA_LEFT, spaceBefore=14, spaceAfter=8,
    ),
    'Body': ParagraphStyle(
        'Body', fontName='Times-Roman', fontSize=12,
        leading=15, alignment=TA_JUSTIFY, spaceAfter=6, firstLineIndent=24,
    ),
    'TableHeader': ParagraphStyle(
        'TableHeader', fontName='Times-Bold', fontSize=11,
        leading=14, alignment=TA_CENTER,
    ),
    'TableBody': ParagraphStyle(
        'TableBody', fontName='Times-Roman', fontSize=10.5,
        leading=13, alignment=TA_LEFT,
    ),
}
```

## Quality Checklist

- [ ] All English in Times New Roman, all Chinese in SimSun/宋体
- [ ] Heading hierarchy visually distinguishable (title → section → subsection → body)
- [ ] Consistent spacing rhythm between same-level elements
- [ ] Table headers bold, centered, gray background; numbers right-aligned
- [ ] Page numbers present and correctly formatted
- [ ] Margins uniform on all sides
- [ ] No orphan headings (heading at bottom of page with no content after it)
- [ ] No decorative excess — calm, authoritative, easy to read

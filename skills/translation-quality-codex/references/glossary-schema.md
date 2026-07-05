# Terminology Glossary JSON Schema

## Full Schema

```json
{
  "metadata": {
    "source_language": "string — e.g., 'Chinese', 'English'",
    "target_language": "string — e.g., 'English', 'Chinese'",
    "document_type": "string — e.g., 'conference agenda', 'contract', 'report'",
    "total_terms": "number",
    "high_confidence": "number",
    "medium_confidence": "number",
    "low_confidence": "number",
    "start_time": "string — ISO 8601 timestamp when researcher started",
    "end_time": "string — ISO 8601 timestamp when researcher finished",
    "web_search_failures": "number — count of terms where web search was unavailable"
  },
  "terms": [
    {
      "original": "string — the term as it appears in the source document",
      "category": "string — one of: organization, person, place, venue, title, technical, product, event",
      "context": "string — the sentence in the source where this term appears",
      "translation": "string — the verified translation",
      "confidence": "string — one of: high, medium, low",
      "sources": ["string — URLs of sources used to verify this translation"],
      "notes": "string — any relevant notes (why this translation was chosen, alternatives considered, etc.)"
    }
  ]
}
```

## Confidence Levels

| Level | Criteria | Action |
|-------|----------|--------|
| `high` | 2+ independent sources agree on the same translation | Use directly |
| `medium` | 1 reliable source found | Use but flag for reviewer |
| `low` | No authoritative source; best judgment used | Reviewer must validate |

## Categories

| Category | Examples | Search Strategy |
|----------|----------|-----------------|
| `organization` | 协会, 委员会, 公司 | Search official website for English name |
| `person` | Speaker names, author names | Search published papers/profiles for English name |
| `place` | City names, country names | Standard geographic translation |
| `venue` | Conference rooms, hotel names | Check hotel/venue website; transliterate if proper noun |
| `title` | Job titles, honorifics | Search organization for official English titles |
| `technical` | Domain-specific terms | Search industry glossaries and standards |
| `product` | Brand names, product names | Search manufacturer website |
| `event` | Conference names, exhibition names | Search event official website |

## Example

```json
{
  "metadata": {
    "source_language": "Chinese",
    "target_language": "English",
    "document_type": "conference agenda",
    "total_terms": 3,
    "high_confidence": 2,
    "medium_confidence": 1,
    "low_confidence": 0,
    "start_time": "2026-03-12T14:30:00Z",
    "end_time": "2026-03-12T14:35:22Z",
    "web_search_failures": 0
  },
  "terms": [
    {
      "original": "中国蜂产品协会",
      "category": "organization",
      "context": "中国蜂产品协会蜂王浆专业委员会主办",
      "translation": "China Bee Products Association (CBPA)",
      "confidence": "high",
      "sources": [
        "https://www.cbpa.org.cn/english/",
        "https://en.wikipedia.org/wiki/China_Bee_Products_Association"
      ],
      "notes": "Official English name found on CBPA's own English-language page"
    },
    {
      "original": "蜂王浆专业委员会",
      "category": "organization",
      "context": "中国蜂产品协会蜂王浆专业委员会主办",
      "translation": "Royal Jelly Professional Committee",
      "confidence": "high",
      "sources": [
        "https://www.cbpa.org.cn/committees/royal-jelly/"
      ],
      "notes": "Sub-committee of CBPA; name found on CBPA committee listing page"
    },
    {
      "original": "美泉宫厅",
      "category": "venue",
      "context": "会议地点：北京国际饭店美泉宫厅",
      "translation": "Meiquangong Hall",
      "confidence": "medium",
      "sources": [
        "https://www.bih.com.cn/facilities/"
      ],
      "notes": "Conference room name within Beijing International Hotel. Transliterated rather than translated as 'Schönbrunn Palace' — it's a room name, not the Austrian palace."
    }
  ]
}
```

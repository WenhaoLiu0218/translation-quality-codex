#!/bin/bash
# test-skill-integrity.sh — Verify SKILL.md and references are consistent
# Usage: bash test-skill-integrity.sh

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_MD="$SKILL_DIR/SKILL.md"
REF_DIR="$SKILL_DIR/references"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

PASS=0
FAIL=0
WARN=0

pass() { echo -e "${GREEN}[PASS]${NC} $1"; PASS=$((PASS+1)); }
fail() { echo -e "${RED}[FAIL]${NC} $1"; FAIL=$((FAIL+1)); }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; WARN=$((WARN+1)); }

echo "=== Translation Quality Skill Integrity Test ==="
echo "SKILL.md: $SKILL_MD"
echo ""

# --- Test 1: SKILL.md exists and ≤500 lines ---
if [[ -f "$SKILL_MD" ]]; then
    LINES=$(wc -l < "$SKILL_MD")
    if [[ "$LINES" -le 500 ]]; then
        pass "SKILL.md line count: $LINES (≤500)"
    else
        fail "SKILL.md line count: $LINES (>500 limit)"
    fi
else
    fail "SKILL.md not found"
    exit 1
fi

# --- Test 2: All referenced files exist ---
for REF_FILE in glossary-schema.md review-feedback-schema.md typesetting-rules.md \
                anti-fabrication-checklist.md scaling-guidelines.md; do
    if [[ -f "$REF_DIR/$REF_FILE" ]]; then
        pass "Reference file exists: $REF_FILE"
    else
        fail "Reference file missing: $REF_FILE"
    fi
done

# --- Test 3: SKILL.md contains all required phases ---
for PHASE in "Phase 0" "Phase 1" "Phase 1.5" "Phase 2" "Phase 3" "Phase 4"; do
    if grep -q "$PHASE" "$SKILL_MD"; then
        pass "Phase found: $PHASE"
    else
        fail "Phase missing: $PHASE"
    fi
done

# --- Test 4: Split mode prompts exist ---
for PROMPT in "term-researcher-fast" "term-researcher-deep"; do
    if grep -q "$PROMPT" "$SKILL_MD"; then
        pass "Split prompt found: $PROMPT"
    else
        fail "Split prompt missing: $PROMPT"
    fi
done

# --- Test 5: Workspace paths include split glossary files ---
for FILE in "glossary-fast.json" "glossary-deep.json" "terminology-glossary.json"; do
    if grep -q "$FILE" "$SKILL_MD"; then
        pass "Workspace path includes: $FILE"
    else
        fail "Workspace path missing: $FILE"
    fi
done

# --- Test 6: Conditional branching exists (>50 terms) ---
if grep -q ">50 terms" "$SKILL_MD"; then
    pass "Conditional branching for >50 terms found"
else
    fail "Conditional branching for >50 terms missing"
fi

if grep -q "≤50 terms" "$SKILL_MD" || grep -q "<=50 terms" "$SKILL_MD"; then
    pass "Conditional branching for ≤50 terms found"
else
    fail "Conditional branching for ≤50 terms missing"
fi

# --- Test 7: Web search fallback strategy exists ---
if grep -q "WEB SEARCH FALLBACK" "$SKILL_MD"; then
    pass "Web search fallback strategy found"
else
    fail "Web search fallback strategy missing"
fi

# --- Test 8: Reviewer pre-check exists ---
if grep -q "PRE-CHECK" "$SKILL_MD"; then
    pass "Reviewer glossary pre-check found"
else
    fail "Reviewer glossary pre-check missing"
fi

# --- Test 9: Timing metadata in glossary schema ---
if grep -q "start_time" "$REF_DIR/glossary-schema.md" && grep -q "end_time" "$REF_DIR/glossary-schema.md"; then
    pass "Timing metadata in glossary schema"
else
    fail "Timing metadata missing from glossary schema"
fi

if grep -q "web_search_failures" "$REF_DIR/glossary-schema.md"; then
    pass "Web search failure count in glossary schema"
else
    fail "Web search failure count missing from glossary schema"
fi

# --- Test 10: Model assignments include split researchers ---
if grep -q "term-researcher-fast.*Sonnet\|term-researcher-fast.*sonnet" "$SKILL_MD"; then
    pass "Model assignment for term-researcher-fast"
else
    fail "Model assignment missing for term-researcher-fast"
fi

if grep -q "term-researcher-deep.*Sonnet\|term-researcher-deep.*sonnet" "$SKILL_MD"; then
    pass "Model assignment for term-researcher-deep"
else
    fail "Model assignment missing for term-researcher-deep"
fi

# --- Test 11: Scaling guidelines updated ---
SCALE_FILE="$REF_DIR/scaling-guidelines.md"
if grep -q "Search Complexity" "$SCALE_FILE"; then
    pass "Scaling guidelines: split by search complexity"
else
    fail "Scaling guidelines: old category-based split still present"
fi

if grep -q "Lead Merge Protocol" "$SCALE_FILE"; then
    pass "Scaling guidelines: merge protocol documented"
else
    fail "Scaling guidelines: merge protocol missing"
fi

if grep -q "Est. Terms" "$SCALE_FILE"; then
    pass "Scaling table includes term count column"
else
    fail "Scaling table missing term count column"
fi

# --- Test 12: Architecture diagram shows split mode ---
if grep -q "term-fast\|term-deep\|fast.*deep" "$SKILL_MD"; then
    pass "Architecture diagram shows split mode"
else
    fail "Architecture diagram does not show split mode"
fi

# --- Test 13: Phase 1.5 merge comes before reviewer ---
PHASE15_LINE=$(grep -n "Phase 1.5" "$SKILL_MD" | head -1 | cut -d: -f1)
PHASE2_LINE=$(grep -n "Phases 2-3\|Phase 2:" "$SKILL_MD" | head -1 | cut -d: -f1)
if [[ -n "$PHASE15_LINE" && -n "$PHASE2_LINE" && "$PHASE15_LINE" -lt "$PHASE2_LINE" ]]; then
    pass "Phase 1.5 (merge) comes before Phase 2 (review)"
else
    fail "Phase 1.5 does not precede Phase 2"
fi

# --- Test 14: Term estimation heuristic ---
if grep -q "协会.*委员会.*公司\|org suffixes" "$SKILL_MD"; then
    pass "Concrete term estimation heuristic found"
else
    fail "Concrete term estimation heuristic missing"
fi

# --- Test 15: Glossary JSON schema is valid (basic structure check) ---
if python3 -c "
import json, re
with open('$REF_DIR/glossary-schema.md') as f:
    content = f.read()
# Extract JSON blocks
blocks = re.findall(r'\`\`\`json\n(.*?)\n\`\`\`', content, re.DOTALL)
for block in blocks:
    # Replace string type descriptions with actual strings for validation
    cleaned = re.sub(r'\"string — [^\"]*\"', '\"placeholder\"', block)
    cleaned = re.sub(r'\"number\"', '0', cleaned)
    cleaned = re.sub(r'\[\"string — [^\"]*\"\]', '[\"url\"]', cleaned)
    data = json.loads(cleaned)
    assert 'metadata' in data
    assert 'terms' in data
    meta = data['metadata']
    assert 'start_time' in meta
    assert 'end_time' in meta
    assert 'web_search_failures' in meta
print('valid')
" 2>/dev/null | grep -q "valid"; then
    pass "Glossary schema JSON is parseable and contains timing fields"
else
    fail "Glossary schema JSON parse error or missing timing fields"
fi

# --- Summary ---
echo ""
echo "=== Summary: $PASS passed, $FAIL failed, $WARN warning(s) ==="

if [[ $FAIL -gt 0 ]]; then
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi

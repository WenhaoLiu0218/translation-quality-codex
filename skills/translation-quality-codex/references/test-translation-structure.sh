#!/bin/bash
# test-translation-structure.sh — Verify translation structure matches source
# Usage: bash test-translation-structure.sh <source.doc|source.html> <translation.md>

set -euo pipefail

SOURCE="$1"
TRANSLATION="$2"
PASS=0
FAIL=0
WARN=0

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
NC='\033[0m'

echo "=== Translation Structure Test ==="
echo "Source: $SOURCE"
echo "Translation: $TRANSLATION"
echo ""

# --- Step 1: Get HTML version of source ---
HTML_SOURCE=""
if [[ "$SOURCE" == *.html ]]; then
    HTML_SOURCE="$SOURCE"
elif [[ "$SOURCE" == *.doc || "$SOURCE" == *.docx ]]; then
    HTML_SOURCE="/tmp/test-structure-source.html"
    textutil -convert html -output "$HTML_SOURCE" "$SOURCE" 2>/dev/null
    if [[ $? -ne 0 ]]; then
        echo -e "${RED}[ERROR] Failed to convert $SOURCE to HTML${NC}"
        exit 1
    fi
else
    echo -e "${RED}[ERROR] Source must be .doc, .docx, or .html${NC}"
    exit 1
fi

# --- Step 2: Count tables in HTML source ---
# Extract table stats: table count, rows per table, cols per table
# Parse HTML tables handling inline tags (multiple tags per line)
SOURCE_TABLES_INFO=$(awk '
BEGIN { IGNORECASE=1; t=0; in_table=0 }
{
    line = $0
    while(length(line) > 0) {
        if(in_table == 0) {
            if(match(line, /<table[^>]*>/)) {
                t++; in_table=1; rows=0; max_cols=0; row_cols=0
                line = substr(line, RSTART + RLENGTH)
            } else break
        } else {
            # Find the next relevant tag
            best = 0; best_tag = ""
            if(match(line, /<tr[^>]*>/))     { if(best==0 || RSTART<best) { best=RSTART; best_len=RLENGTH; best_tag="tr" } }
            if(match(line, /<t[dh][^>]*>/))  { if(best==0 || RSTART<best) { best=RSTART; best_len=RLENGTH; best_tag="cell" } }
            if(match(line, /<\/tr[^>]*>/))   { if(best==0 || RSTART<best) { best=RSTART; best_len=RLENGTH; best_tag="endtr" } }
            if(match(line, /<\/table[^>]*>/)){ if(best==0 || RSTART<best) { best=RSTART; best_len=RLENGTH; best_tag="endtable" } }

            if(best == 0) break

            if(best_tag == "tr") {
                rows++; row_cols=0
            } else if(best_tag == "cell") {
                row_cols++
                if(row_cols > max_cols) max_cols = row_cols
            } else if(best_tag == "endtr") {
                # row ended
            } else if(best_tag == "endtable") {
                print t ":" rows ":" max_cols
                in_table = 0
            }
            line = substr(line, best + best_len)
        }
    }
}
' "$HTML_SOURCE")

SOURCE_TABLE_COUNT=$(echo "$SOURCE_TABLES_INFO" | grep -c '.' 2>/dev/null || echo "0")

# --- Step 3: Count tables in Markdown translation ---
# Markdown table detection: line matching |...|...| with at least one |---|
MD_TABLES_INFO=$(awk '
BEGIN { in_table=0; t=0; rows=0; cols=0 }
{
    # Check if line looks like a markdown table row
    if(/^\|.*\|[[:space:]]*$/) {
        if(!in_table) {
            in_table = 1
            t++
            rows = 0
            cols = 0
        }
        # Count if this is a separator row (|---|---|)
        if(/^\|[-: |]+\|[[:space:]]*$/ && /---/) {
            # separator row — do not count as data row
        } else {
            rows++
            # Count columns by counting | minus 1
            line = $0
            c = 0
            for(i=1; i<=length(line); i++) {
                if(substr(line,i,1) == "|") c++
            }
            c = c - 1  # pipes = cols + 1
            if(c > cols) cols = c
        }
    } else {
        if(in_table) {
            print t ":" rows ":" cols
            in_table = 0
        }
    }
}
END {
    if(in_table) {
        print t ":" rows ":" cols
    }
}
' "$TRANSLATION")

MD_TABLE_COUNT=$(echo "$MD_TABLES_INFO" | grep -c '.' 2>/dev/null || echo "0")

# --- Step 4: Compare table counts ---
TOTAL_SOURCE_ROWS=0

if [[ "$SOURCE_TABLE_COUNT" -eq "$MD_TABLE_COUNT" ]]; then
    echo -e "${GREEN}[PASS]${NC} Table count: source=$SOURCE_TABLE_COUNT, translation=$MD_TABLE_COUNT"
    ((PASS++))
else
    echo -e "${RED}[FAIL]${NC} Table count: source=$SOURCE_TABLE_COUNT, translation=$MD_TABLE_COUNT"
    ((FAIL++))
fi

# --- Step 5: Per-table comparison ---
# Build arrays from source and markdown info
IFS=$'\n'
SOURCE_ARRAY=($SOURCE_TABLES_INFO)
MD_ARRAY=($MD_TABLES_INFO)
unset IFS

MAX_TABLES=$SOURCE_TABLE_COUNT
if [[ "$MD_TABLE_COUNT" -gt "$MAX_TABLES" ]]; then
    MAX_TABLES=$MD_TABLE_COUNT
fi

for ((i=0; i<MAX_TABLES; i++)); do
    S_INFO="${SOURCE_ARRAY[$i]:-}"
    M_INFO="${MD_ARRAY[$i]:-}"

    if [[ -z "$S_INFO" ]]; then
        echo -e "${RED}[FAIL]${NC} Table $((i+1)): missing in source (extra table in translation)"
        ((FAIL++))
        continue
    fi
    if [[ -z "$M_INFO" ]]; then
        echo -e "${RED}[FAIL]${NC} Table $((i+1)): missing in translation"
        ((FAIL++))
        continue
    fi

    S_ROWS=$(echo "$S_INFO" | cut -d: -f2)
    S_COLS=$(echo "$S_INFO" | cut -d: -f3)
    M_ROWS=$(echo "$M_INFO" | cut -d: -f2)
    M_COLS=$(echo "$M_INFO" | cut -d: -f3)

    TOTAL_SOURCE_ROWS=$((TOTAL_SOURCE_ROWS + S_ROWS))

    ROW_MATCH="yes"
    COL_MATCH="yes"
    if [[ "$S_ROWS" -ne "$M_ROWS" ]]; then ROW_MATCH="no"; fi
    if [[ "$S_COLS" -ne "$M_COLS" ]]; then COL_MATCH="no"; fi

    if [[ "$ROW_MATCH" == "yes" && "$COL_MATCH" == "yes" ]]; then
        echo -e "${GREEN}[PASS]${NC} Table $((i+1)): source=${S_ROWS} rows x ${S_COLS} cols, translation=${M_ROWS} rows x ${M_COLS} cols"
        ((PASS++))
    else
        DETAIL=""
        if [[ "$ROW_MATCH" == "no" ]]; then
            DIFF=$((S_ROWS - M_ROWS))
            if [[ $DIFF -gt 0 ]]; then
                DETAIL="$DIFF row(s) missing"
            else
                DETAIL="$((-DIFF)) extra row(s)"
            fi
        fi
        if [[ "$COL_MATCH" == "no" ]]; then
            CDIFF=$((S_COLS - M_COLS))
            if [[ -n "$DETAIL" ]]; then DETAIL="$DETAIL, "; fi
            if [[ $CDIFF -gt 0 ]]; then
                DETAIL="${DETAIL}$CDIFF col(s) missing"
            else
                DETAIL="${DETAIL}$((-CDIFF)) extra col(s)"
            fi
        fi
        echo -e "${RED}[FAIL]${NC} Table $((i+1)): source=${S_ROWS} rows x ${S_COLS} cols, translation=${M_ROWS} rows x ${M_COLS} cols ($DETAIL)"
        ((FAIL++))
    fi
done

# --- Step 6: Check for colspan/rowspan (warn only) ---
MERGE_COUNT=$(awk 'BEGIN{IGNORECASE=1; c=0} /colspan|rowspan/{c++} END{print c}' "$HTML_SOURCE")
if [[ "$MERGE_COUNT" -gt 0 ]]; then
    echo -e "${YELLOW}[WARN]${NC} Source has $MERGE_COUNT merged cells (colspan/rowspan) — manual verification recommended"
    ((WARN++))
fi

# --- Step 7: Check for boundary violations ---
# Look for content that might have been pulled out of tables:
# Heuristic: if source has N tables but translation has list items or headers
# immediately after a table that don't exist in source's non-table content

# Check if any free-text sections in source were converted to tables in translation
# (reverse boundary violation)
# Simple heuristic: if translation has more tables than source
if [[ "$MD_TABLE_COUNT" -gt "$SOURCE_TABLE_COUNT" ]]; then
    EXTRA=$((MD_TABLE_COUNT - SOURCE_TABLE_COUNT))
    echo -e "${YELLOW}[WARN]${NC} Translation has $EXTRA more table(s) than source — possible free-text-to-table conversion"
    ((WARN++))
fi

# --- Summary ---
echo ""
echo "=== Summary: $PASS passed, $FAIL failed, $WARN warning(s) ==="
echo "Source tables: $SOURCE_TABLE_COUNT (total ~$TOTAL_SOURCE_ROWS rows)"

if [[ $FAIL -gt 0 ]]; then
    exit 1
else
    exit 0
fi

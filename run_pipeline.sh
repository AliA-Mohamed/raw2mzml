#!/bin/bash
set -euo pipefail

# ── Configuration ──────────────────────────────────────────────────────────────
PARSER="/opt/ThermoRawFileParser/ThermoRawFileParser"
SPLITTER="/opt/pipeline/split_polarity.py"
RAW_DIR="${RAW_DIR:-/data/raw}"
MZML_DIR="${MZML_DIR:-/data/raw/mzML}"
SPLIT_DIR="$MZML_DIR/split"

# ── Colours (suppressed if not a terminal) ─────────────────────────────────────
if [ -t 1 ]; then
    GREEN='\033[0;32m'; YELLOW='\033[1;33m'; RED='\033[0;31m'; NC='\033[0m'
else
    GREEN=''; YELLOW=''; NC=''; RED=''
fi

info()    { echo -e "${GREEN}[INFO]${NC}  $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*" >&2; exit 1; }
divider() { echo "──────────────────────────────────────────────────"; }

divider
echo "  raw2mzml — Thermo .raw to polarity-split .mzML"
echo "  ThermoRawFileParser v2.0.0 (.NET 8) + polarity splitter"
divider

# ── Validate input ─────────────────────────────────────────────────────────────
[ -d "$RAW_DIR" ] || error "Input directory not found: $RAW_DIR
  Mount your .raw folder with: -v /your/folder:/data/raw"

RAW_COUNT=$(find "$RAW_DIR" -maxdepth 1 \( -name "*.raw" -o -name "*.RAW" \) 2>/dev/null | wc -l | tr -d ' ')
[ "$RAW_COUNT" -gt 0 ] || error "No .raw files found in $RAW_DIR
  Make sure you mounted the correct folder containing your Thermo .raw files."

info "Found $RAW_COUNT .raw file(s) in $RAW_DIR"

# ── UID/GID passthrough ────────────────────────────────────────────────────────
# Output files are owned by the same user who owns the input directory,
# preventing permission issues on the host. Override with -e HOST_UID=1000 etc.
HOST_UID="${HOST_UID:-$(stat -c '%u' "$RAW_DIR" 2>/dev/null || echo 0)}"
HOST_GID="${HOST_GID:-$(stat -c '%g' "$RAW_DIR" 2>/dev/null || echo 0)}"

# ── Step 1: .raw → indexed mzML ───────────────────────────────────────────────
divider
info "Step 1/2 — Converting .raw → indexed mzML"
info "  Input : $RAW_DIR"
info "  Output: $MZML_DIR"
divider

mkdir -p "$MZML_DIR"

"$PARSER" \
    -d "$RAW_DIR" \
    -o "$MZML_DIR" \
    -f 2 \
    -m 1 \
    -l 2 2>&1 \
  | grep -E "^20|INFO|ERROR|WARN|Processing completed" \
  | sed 's/^/  /' || true

MZML_COUNT=$(find "$MZML_DIR" -maxdepth 1 -name "*.mzML" 2>/dev/null | wc -l | tr -d ' ')
[ "$MZML_COUNT" -gt 0 ] || error "Conversion produced no mzML files. Check that your .raw files are valid Thermo files."

info "Converted $MZML_COUNT / $RAW_COUNT file(s)"

# ── Step 2: Split by polarity ──────────────────────────────────────────────────
divider
info "Step 2/2 — Splitting by polarity (pos/neg)"
info "  Input : $MZML_DIR/*.mzML"
info "  Output: $SPLIT_DIR/"
divider

mkdir -p "$SPLIT_DIR"

# Override the default paths used by split_polarity.py
MZML_DIR="$MZML_DIR" python3 "$SPLITTER" 2>&1 | sed 's/^/  /'

POS_COUNT=$(find "$SPLIT_DIR" -name "*_pos.mzML" 2>/dev/null | wc -l | tr -d ' ')
NEG_COUNT=$(find "$SPLIT_DIR" -name "*_neg.mzML" 2>/dev/null | wc -l | tr -d ' ')
SPLIT_COUNT=$((POS_COUNT + NEG_COUNT))

# ── Fix ownership ──────────────────────────────────────────────────────────────
if [ "$HOST_UID" != "0" ]; then
    chown -R "${HOST_UID}:${HOST_GID}" "$MZML_DIR" 2>/dev/null || true
fi

# ── Summary ────────────────────────────────────────────────────────────────────
divider
echo ""
echo -e "  ${GREEN}✓ Pipeline complete${NC}"
echo ""
echo "  Raw files      : $RAW_COUNT"
echo "  mzML (combined): $MZML_COUNT"
echo "  mzML (split)   : $SPLIT_COUNT  ($POS_COUNT pos + $NEG_COUNT neg)"
echo ""
echo "  Results written to:"
echo "    $MZML_DIR/"
echo "    $SPLIT_DIR/"
echo ""
divider

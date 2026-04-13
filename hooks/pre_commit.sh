#!/usr/bin/env bash
# Hook: pre-commit drift check
#
# Scans staged files for drift before allowing a commit.
# Blocks the commit if any SHOUT-level drift is found.
#
# Install:
#   cp hooks/pre_commit.sh .git/hooks/pre-commit
#   chmod +x .git/hooks/pre-commit

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

# Get list of staged Python files
STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -z "$STAGED_FILES" ]; then
    exit 0
fi

echo "🔍 Drift check: scanning staged files..."

FOUND_SHOUTS=0

for file in $STAGED_FILES; do
    if [ -f "$file" ]; then
        OUTPUT=$(cd "$SCRIPT_DIR" && python -c "
import sys
sys.path.insert(0, '.')
from outpost.server import scan_file
result = scan_file('$file')
if '📢' in result:
    print(result)
    sys.exit(1)
" 2>/dev/null) || FOUND_SHOUTS=1
        if [ -n "$OUTPUT" ]; then
            echo "$OUTPUT"
        fi
    fi
done

if [ "$FOUND_SHOUTS" -ne 0 ]; then
    echo ""
    echo "⛔ Commit blocked: SHOUT-level drift detected in staged files."
    echo "   Fix the issues above or use --no-verify to skip."
    exit 1
fi

echo "✅ No critical drift found."

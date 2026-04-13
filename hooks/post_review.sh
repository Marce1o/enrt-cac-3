#!/usr/bin/env bash
# Hook: post-review drift scan
#
# After a PR is reviewed, scan the changed files and add a
# drift summary as a PR comment. Designed for CI integration.
#
# Usage in GitHub Actions:
#   - name: Drift scan
#     run: bash hooks/post_review.sh ${{ github.event.pull_request.base.sha }}

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BASE_SHA="${1:-HEAD~1}"

# Get changed files
CHANGED_FILES=$(git diff --name-only "$BASE_SHA" HEAD | grep '\.py$' || true)

if [ -z "$CHANGED_FILES" ]; then
    echo "No Python files changed."
    exit 0
fi

echo "# Drift Scan — PR Review"
echo ""

cd "$SCRIPT_DIR"

for file in $CHANGED_FILES; do
    if [ -f "$file" ]; then
        python -c "
import sys
sys.path.insert(0, '.')
from outpost.server import scan_file
print(scan_file('$file'))
" 2>/dev/null || true
    fi
done

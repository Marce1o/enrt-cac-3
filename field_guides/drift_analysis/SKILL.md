---
applyTo: "**/*"
---

# Drift Analysis Skill

You have access to the `drift` MCP tools. Use them to analyze codebases for honesty.

## Available tools

- **drift_scan**: Full scan of a directory. Returns a markdown or JSON report of all drift found.
- **drift_scan_file**: Scan a single file for drift signals.
- **drift_staleness**: Temporal analysis using git blame. Shows how old the drift is.

## When to use drift analysis

- Before a code review: scan the changed files to see if the PR introduces new drift
- During onboarding: scan the repo to find misleading documentation
- Before a refactor: find all the comments and docs that will break
- Sprint planning: use staleness report to prioritize documentation debt

## How to interpret results

### Severity levels
- 📢 **Shout**: Fix immediately. These actively mislead developers.
- 🗣️ **Murmur**: Fix when convenient. These waste people's time.
- 🤫 **Whisper**: Fix if you're bored. These confuse newcomers.

### Drift types
- `readme_vs_reality`: README promises things that don't exist
- `comment_vs_code`: Comments describe code that has changed
- `test_name_vs_assertion`: Test names don't match what's tested
- `docstring_vs_signature`: Docstrings document wrong parameters
- `todo_abandoned`: TODOs that nobody will ever do

## Workflow

1. Start with `drift_scan` on the whole repo to get the big picture
2. Focus on shouts first — these are the dangerous lies
3. Use `drift_staleness` to understand if drift is getting better or worse
4. For specific files, use `drift_scan_file` for detailed analysis

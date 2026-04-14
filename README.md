# Drift

**A coding assistant that finds where your codebase lies about itself.**

---

## The Problem

Every codebase accumulates a specific kind of debt that no linter catches: **drift**.

Drift is the gap between what code *claims* to do and what it *actually* does. It lives in:

- **READMEs** that describe features from two versions ago
- **Comments** that explain code that has since been rewritten
- **Test names** like `test_handles_timeout` that never simulate a timeout
- **Docstrings** that document parameters the function no longer accepts
- **TODOs** from 2022 that nobody will ever do

This isn't a style problem. It's a **trust problem**. When developers can't trust the documentation that lives alongside the code, they stop reading it. When they stop reading it, it drifts further. The cycle continues until the only reliable documentation is the code itself — and even that has misleading variable names.

## Who It's For

Any development team that has ever:
- Wasted an afternoon because a comment lied
- Onboarded someone who was confused by a README
- Found a test that wasn't actually testing anything
- Discovered a TODO comment older than some team members' tenure

## How It Works

Drift treats your codebase as an **archaeological site**. Every file has layers:

| Layer | What it contains |
|-------|-----------------|
| Code | What the program actually does |
| Comments | What someone thought it did |
| Docstrings | What the API contract promises |
| Test names | What's allegedly verified |
| README | What the project aspires to be |
| Git history | When each layer was last touched |

**Lenses** compare these layers. Where they disagree, Drift reports an **artifact** — a specific, located instance of dishonesty with a severity rating.

### Severity Levels

| Level | Icon | Meaning |
|-------|------|---------|
| Shout | 📢 | Dangerous. Will cause a production incident or mask a bug. |
| Murmur | 🗣️ | Misleading. Will cost someone an afternoon. |
| Whisper | 🤫 | Cosmetic. Will confuse newcomers. |

## Architecture

```
the_dig/          Excavation engine: strata, artifacts, field notes
lenses/           Detection: 5 lenses, each comparing different layers
cartography/      Reporting: markdown, JSON, temporal analysis
outpost/          MCP server: expose drift tools to AI assistants
expeditions/      Prompts: guide agents through drift workflows
field_guides/     Skills: teach the archaeology methodology
hooks/            Automation: pre-commit, post-review CI hooks
```

This structure is **intentionally unconventional**. It's organized around the metaphor, not around `src/lib/utils`. The metaphor *is* the architecture: you excavate strata, examine them through lenses, and map what you find.

## Usage

### CLI

```bash
# Install
pip install -e .

# Scan a whole repo
drift scan /path/to/repo

# Scan with JSON output (for CI)
drift scan /path/to/repo --format=json

# Scan a single file
drift file /path/to/suspicious_module.py

# Temporal analysis (how old is the drift?)
drift staleness /path/to/repo
```

### As an MCP Server (for Claude Code / Codex)

```bash
drift serve
```

Or add to your assistant config:

```json
{
  "mcpServers": {
    "drift": {
      "command": "python",
      "args": ["-m", "outpost.server"],
      "cwd": "/path/to/drift"
    }
  }
}
```

Then ask your assistant: *"Scan this repo for drift"* — and it will use the `drift_scan`, `drift_scan_file`, and `drift_staleness` tools.

### As a Git Hook

```bash
# Pre-commit: block commits with dangerous drift
cp hooks/pre_commit.sh .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit

# Post-review: add drift report to PRs (GitHub Actions)
# See hooks/post_review.sh for CI integration
```

## The Five Lenses

| Lens | Compares | Finds |
|------|----------|-------|
| **ReadmeLens** | README vs code | Phantom features, wrong install commands, missing functions |
| **CommentLens** | Comments vs code | Stale references, commented-out code, wrong return claims |
| **TestLens** | Test names vs bodies | Theater tests (no assertions), name/body mismatch, exception suppression |
| **DocstringLens** | Docstrings vs signatures | Phantom parameters, undocumented params |
| **TodoLens** | TODOs vs time | Abandoned TODOs (>6mo), HACK/XXX markers |

## Example Output

```
🗺️ Drift Report

> Found 7 drifts across 12 files: 📢 2 shouts, 🗣️ 3 murmurs, 🤫 2 whispers

## 📢 Shouts (fix these)

### `tests/test_auth.py:45` 🪦 STALE
**Claims:** `test_validates_token` is a test
**Reality:** Contains zero assertions. This is theater.

### `tests/test_api.py:112`
**Claims:** `test_handles_timeout` handles errors
**Reality:** Catches exceptions and swallows them silently

## 🗣️ Murmurs (address when nearby)

### `utils/parser.py:23`
**Claims:** Comment references `validate_schema`
**Reality:** `validate_schema` not found as identifier in this file

### `README.md:67`
**Claims:** README references function `migrate_database()`
**Reality:** No function named `migrate_database` found in codebase
```

## Demo

### Running Drift against itself

```bash
cd 3/
python cli.py scan .
```

Drift is designed to be honest about its own code. If you find drift in this repo, that's a bug — and also proof the tool works.

### Running Drift against assignments 1 and 2

```bash
python cli.py scan ../1/
python cli.py scan ../2/
```

---

## Assistant Setup

| Component | Location | Purpose |
|-----------|----------|---------|
| **Skills** | `field_guides/drift_analysis/SKILL.md` | Teaches assistants how to interpret drift reports |
| **Skills** | `field_guides/archaeology/SKILL.md` | Teaches the layer-comparison methodology |
| **Hooks** | `hooks/pre_commit.sh` | Blocks commits with SHOUT-level drift |
| **Hooks** | `hooks/post_review.sh` | Adds drift reports to PR reviews |
| **MCP Server** | `outpost/server.py` | 3 tools: scan, scan_file, staleness |
| **Prompts** | `expeditions/detect.md` | How to find drift |
| **Prompts** | `expeditions/excavate.md` | How to trace drift through git history |
| **Prompts** | `expeditions/report.md` | How to write a drift report |
| **Agents** | `AGENTS.md` | Archaeologist (scan), Cartographer (report), Sentinel (CI) |
| **Guidance** | `CLAUDE.md` | Project conventions and structure |

## Reflection

### What worked

- **The metaphor carries weight.** Organizing the code around "archaeological excavation" isn't just cute — it actually clarifies the architecture. Strata, lenses, artifacts, and field notes are better names than `FileContent`, `Analyzer`, `Finding`, and `Results`. They communicate *intent*, not just structure.
- **Zero dependencies.** The whole thing runs on stdlib Python. No pip install dance, no version conflicts. This matters for a tool that's supposed to run in any repo's CI.
- **The severity model.** Whisper/murmur/shout is more useful than low/medium/high because it describes *impact on humans*, not abstract risk levels.
- **MCP integration is surprisingly clean.** Exposing the scanner as tools means any AI assistant can become a drift detector without custom integration.

### What didn't

- **The README lens is noisy.** Feature-list detection has too many false positives. English is ambiguous; distinguishing "planned feature" from "existing feature" in a bullet point is genuinely hard without semantic understanding.
- **Git blame is slow.** The TODO lens does a `git blame` per line, which is O(n) subprocess calls. For large repos this would need batching or a libgit2 binding.
- **No incremental scanning.** Every run scans everything. For CI, you'd want to diff against the previous scan and only report *new* drift.

### How a team could use this

1. **Weekly drift reports** — Scheduled CI job runs `drift scan` and posts the report to Slack. Track drift count over time like you track test coverage.
2. **Pre-commit gate** — Block commits that introduce SHOUT-level drift. Developers fix lies before they merge.
3. **Onboarding tool** — New team members run `drift scan` to find the README lies before they waste time believing them.
4. **Refactoring prep** — Before touching a module, scan it for drift. Fix the comments and docstrings *first* so the refactor doesn't inherit stale documentation.
5. **PR review augmentation** — AI assistant uses the MCP tools during review to flag: "This PR changes `validate_input()` but the comment on line 45 still describes the old behavior."

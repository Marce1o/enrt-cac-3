# CLAUDE.md — Instructions for working with this project

## What this is

**Drift** is a coding assistant that finds where codebases lie about themselves. It detects gaps between what code *claims* to do (via comments, docstrings, READMEs, test names) and what it *actually* does.

## Project structure (non-standard, intentional)

This project is organized around an archaeological metaphor. Don't "fix" it into src/lib/utils.

```
the_dig/          Core engine. Strata (file layers), Artifacts (findings), FieldNotes (accumulator).
lenses/           Detection modules. Each lens compares two layers of truth.
cartography/      Reporting. Turns raw artifacts into human-readable maps.
outpost/          MCP server. Exposes drift detection as tools for AI assistants.
expeditions/      Prompts. Markdown files that guide how agents should use drift.
field_guides/     Skills. Teach assistants the archaeology methodology.
hooks/            Git hooks. Automate drift checks in CI/CD.
tests/            pytest suite covering engine, lenses, and reporting.
```

## Key concepts

- **Stratum**: A snapshot of a file's content at one layer (code, comments, readme, git_log)
- **Lens**: A module that compares strata and finds drift
- **Artifact**: A single instance of drift (with type, severity, evidence)
- **FieldNotes**: In-memory accumulator for artifacts during a scan
- **DriftMap**: Renderer that turns FieldNotes into reports

## Running

```bash
# Install
pip install -e .

# CLI
drift scan .                    # Full repo scan
drift scan . --format=json      # JSON output
drift file path/to/file.py     # Single file
drift staleness .               # Git-blame age analysis
drift serve                     # Start MCP server

# Tests
pytest tests/ -v
```

## MCP integration

Add to your Claude Code or VS Code settings:

```json
{
  "mcpServers": {
    "drift": {
      "command": "python",
      "args": ["-m", "outpost.server"],
      "cwd": "/path/to/3"
    }
  }
}
```

## Code style

- Python 3.10+
- No external dependencies beyond stdlib (by design — this needs to run anywhere)
- Type hints on public interfaces, not on internals
- Docstrings are written as prose, not javadoc
- Module-level docstrings explain *why*, not *what*

## When editing

- Run `pytest tests/ -v` after changes
- If adding a new lens, add it to `lenses/__init__.py` ALL_LENSES
- If adding a new drift type, add it to `the_dig/artifacts.py` DriftType enum
- If adding a new MCP tool, add it to `outpost/server.py` TOOLS list and handler

## Philosophy

This project asks one question: **Is the codebase honest with itself?**

Not "is it clean" or "is it fast" or "is it secure." Just: when it makes a claim — in a comment, a test name, a README — is that claim true?

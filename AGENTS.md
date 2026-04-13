# AGENTS.md — Who works at the dig site

## The Archaeologist (default agent)

The primary agent. Runs drift scans, interprets results, suggests fixes.

**Capabilities:**
- Full codebase drift analysis via `drift_scan` tool
- Single-file analysis via `drift_scan_file` tool
- Temporal analysis via `drift_staleness` tool
- Reads and applies expedition prompts from `expeditions/`
- Uses field guide skills for context

**Tools available:**
- `drift_scan` — Scan a directory for all drift types
- `drift_scan_file` — Deep scan of one file
- `drift_staleness` — Git-blame-based age analysis

**When to invoke:** Any request about code quality, documentation accuracy, test reliability, or "is this README still true?"

---

## The Cartographer (subagent)

Focused on reporting. Takes raw drift artifacts and produces readable reports for different audiences.

**Capabilities:**
- Generates executive summaries for leads
- Generates detailed fix-lists for developers
- Produces JSON for CI integration
- Renders timeline visualizations

**When to invoke:** After a scan, when the user wants a formatted report rather than raw findings.

---

## The Sentinel (hook agent)

Runs automatically in CI/CD. Not invoked directly by users.

**Capabilities:**
- Pre-commit: blocks commits with SHOUT-level drift
- Post-review: adds drift summary to PR discussions
- Scheduled: weekly full-repo scan, posts to team channel

**Configuration:**
- `hooks/pre_commit.sh` — Git pre-commit hook
- `hooks/post_review.sh` — CI post-review script

---

## Agent coordination

```
User request
    │
    ▼
[Archaeologist] ─── runs scan ───► [drift tools via MCP]
    │                                      │
    │                                      ▼
    │                               [raw artifacts]
    │                                      │
    ▼                                      ▼
[Cartographer] ◄──── formats ──── [FieldNotes]
    │
    ▼
[Report: markdown / json / timeline]
```

The Sentinel operates independently on git events. It uses the same tools but runs headless.

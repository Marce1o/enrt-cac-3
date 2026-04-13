"""
Drift Map — the final report.

This is what you show to your team. A summary of everywhere the
codebase is lying to itself, organized by severity and type,
with actionable recommendations.
"""

from __future__ import annotations

import json
from io import StringIO
from typing import Optional

from the_dig.artifacts import DriftType, Severity
from the_dig.fieldnotes import FieldNotes


class DriftMap:
    """Renders FieldNotes into human-readable reports."""

    def __init__(self, notes: FieldNotes):
        self.notes = notes

    def render_markdown(self, title: Optional[str] = None) -> str:
        """Generate the full drift report as Markdown."""
        buf = StringIO()
        title = title or "Drift Report"

        buf.write(f"# 🗺️ {title}\n\n")

        # Summary bar
        buf.write(f"> {self.notes.summary_line()}\n\n")

        if self.notes.total == 0:
            buf.write("Nothing to report. The codebase and its documentation agree.\n")
            buf.write("(This is either very good or very suspicious.)\n")
            return buf.getvalue()

        # Stats table
        buf.write("## Overview\n\n")
        buf.write(f"| Metric | Value |\n")
        buf.write(f"|--------|-------|\n")
        buf.write(f"| Files scanned | {self.notes.files_scanned} |\n")
        buf.write(f"| Strata examined | {self.notes.strata_examined} |\n")
        buf.write(f"| Total drifts | {self.notes.total} |\n")
        buf.write(f"| Stale (>6mo) | {len(self.notes.stale_artifacts)} |\n\n")

        # Severity breakdown
        if self.notes.shouts:
            buf.write("## 📢 Shouts (fix these)\n\n")
            buf.write("These are dangerous lies. Someone will get burned.\n\n")
            for a in self.notes.shouts:
                buf.write(self._render_artifact(a))

        if self.notes.murmurs:
            buf.write("## 🗣️ Murmurs (address when nearby)\n\n")
            buf.write("Misleading, but not dangerous. Fix them if you're already in the file.\n\n")
            for a in self.notes.murmurs:
                buf.write(self._render_artifact(a))

        if self.notes.whispers:
            buf.write("## 🤫 Whispers (for the meticulous)\n\n")
            buf.write("Cosmetic drift. Will confuse newcomers.\n\n")
            for a in self.notes.whispers:
                buf.write(self._render_artifact(a))

        # Hotspots
        by_file = self.notes.by_file()
        if len(by_file) > 1:
            buf.write("## 🔥 Hotspots\n\n")
            buf.write("Files with the most drift:\n\n")
            sorted_files = sorted(by_file.items(), key=lambda x: len(x[1]), reverse=True)
            for filepath, artifacts in sorted_files[:10]:
                severities = [a.severity.value for a in artifacts]
                shout_count = severities.count("shout")
                buf.write(f"- **{filepath}** — {len(artifacts)} drifts")
                if shout_count:
                    buf.write(f" ({shout_count} 📢)")
                buf.write("\n")
            buf.write("\n")

        return buf.getvalue()

    def render_json(self) -> str:
        """Generate the drift report as JSON."""
        return json.dumps(self.notes.to_dict(), indent=2)

    def _render_artifact(self, artifact) -> str:
        """Render a single artifact as a Markdown block."""
        stale_badge = " 🪦 **STALE**" if artifact.stale else ""
        return (
            f"### `{artifact.file_path}:{artifact.line_start}`{stale_badge}\n"
            f"**Claims:** {artifact.claim}\\\n"
            f"**Reality:** {artifact.reality}\n\n"
            f"```\n{artifact.evidence[:300]}\n```\n\n"
            f"---\n\n"
        )

"""
Timeline — temporal analysis of drift.

When did the lies start? Are they getting worse?
This module provides tools to understand drift over git history.
"""

from __future__ import annotations

from collections import Counter
from io import StringIO

from the_dig.fieldnotes import FieldNotes


class DriftTimeline:
    """Analyze drift patterns over time using git blame data."""

    def __init__(self, notes: FieldNotes):
        self.notes = notes

    def age_distribution(self) -> dict[str, int]:
        """Bucket artifacts by age."""
        buckets: Counter = Counter()
        for a in self.notes.artifacts:
            if a.git_blame_age_days is None:
                buckets["unknown"] += 1
            elif a.git_blame_age_days < 30:
                buckets["< 1 month"] += 1
            elif a.git_blame_age_days < 90:
                buckets["1-3 months"] += 1
            elif a.git_blame_age_days < 180:
                buckets["3-6 months"] += 1
            elif a.git_blame_age_days < 365:
                buckets["6-12 months"] += 1
            else:
                buckets["> 1 year"] += 1
        return dict(buckets)

    def render_ascii_histogram(self) -> str:
        """Render a simple ASCII histogram of drift age."""
        dist = self.age_distribution()
        if not dist:
            return "No temporal data available."

        buf = StringIO()
        buf.write("Drift Age Distribution\n")
        buf.write("=" * 40 + "\n")

        order = ["< 1 month", "1-3 months", "3-6 months", "6-12 months", "> 1 year", "unknown"]
        max_count = max(dist.values()) if dist else 1

        for label in order:
            count = dist.get(label, 0)
            if count == 0:
                continue
            bar_len = int((count / max_count) * 30)
            bar = "█" * bar_len
            buf.write(f"{label:>12s} | {bar} {count}\n")

        return buf.getvalue()

    def staleness_score(self) -> float:
        """
        0.0 = all drift is fresh (recently introduced)
        1.0 = all drift is ancient (> 1 year old)
        """
        if not self.notes.artifacts:
            return 0.0

        aged = [a for a in self.notes.artifacts if a.git_blame_age_days is not None]
        if not aged:
            return 0.0

        max_age = 365 * 2  # Cap at 2 years
        scores = [min(a.git_blame_age_days, max_age) / max_age for a in aged]
        return sum(scores) / len(scores)

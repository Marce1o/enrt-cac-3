"""
FieldNotes — the running log of a dig.

As lenses find artifacts, they get recorded here. FieldNotes is the
in-memory accumulator for a single excavation session. It knows how
to filter, sort, and summarize what was found.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from the_dig.artifacts import Artifact, DriftType, Severity


@dataclass
class FieldNotes:
    """Accumulator for drift artifacts found during an excavation."""

    artifacts: list[Artifact] = field(default_factory=list)
    files_scanned: int = 0
    strata_examined: int = 0

    def record(self, artifact: Artifact) -> None:
        # Deduplicate by fingerprint
        existing = {a.fingerprint for a in self.artifacts}
        if artifact.fingerprint not in existing:
            self.artifacts.append(artifact)

    def record_many(self, artifacts: list[Artifact]) -> None:
        for a in artifacts:
            self.record(a)

    @property
    def total(self) -> int:
        return len(self.artifacts)

    @property
    def shouts(self) -> list[Artifact]:
        return [a for a in self.artifacts if a.severity == Severity.SHOUT]

    @property
    def murmurs(self) -> list[Artifact]:
        return [a for a in self.artifacts if a.severity == Severity.MURMUR]

    @property
    def whispers(self) -> list[Artifact]:
        return [a for a in self.artifacts if a.severity == Severity.WHISPER]

    @property
    def stale_artifacts(self) -> list[Artifact]:
        return [a for a in self.artifacts if a.stale]

    def by_type(self) -> dict[DriftType, list[Artifact]]:
        result: dict[DriftType, list[Artifact]] = {}
        for a in self.artifacts:
            result.setdefault(a.drift_type, []).append(a)
        return result

    def by_file(self) -> dict[str, list[Artifact]]:
        result: dict[str, list[Artifact]] = {}
        for a in self.artifacts:
            key = str(a.file_path)
            result.setdefault(key, []).append(a)
        return result

    def severity_counts(self) -> dict[str, int]:
        c = Counter(a.severity.value for a in self.artifacts)
        return dict(c)

    def summary_line(self) -> str:
        sc = self.severity_counts()
        parts = []
        if sc.get("shout", 0):
            parts.append(f"📢 {sc['shout']} shouts")
        if sc.get("murmur", 0):
            parts.append(f"🗣️ {sc['murmur']} murmurs")
        if sc.get("whisper", 0):
            parts.append(f"🤫 {sc['whisper']} whispers")
        if not parts:
            return "✨ No drift detected. The codebase is honest today."
        return f"Found {self.total} drifts across {self.files_scanned} files: {', '.join(parts)}"

    def to_dict(self) -> dict:
        return {
            "summary": self.summary_line(),
            "total": self.total,
            "files_scanned": self.files_scanned,
            "strata_examined": self.strata_examined,
            "severity_counts": self.severity_counts(),
            "artifacts": [a.to_dict() for a in self.artifacts],
        }

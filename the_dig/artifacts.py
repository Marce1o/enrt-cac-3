"""
Artifacts — the things we find when we dig.

An Artifact is a single instance of drift: a place where the code
says one thing and does another. They are not bugs. They are not
style violations. They are *lies* — well-intentioned lies that
the codebase tells about itself.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional


class DriftType(Enum):
    """The species of lie."""

    README_VS_REALITY = "readme_vs_reality"
    COMMENT_VS_CODE = "comment_vs_code"
    TEST_NAME_VS_ASSERTION = "test_name_vs_assertion"
    DOCSTRING_VS_SIGNATURE = "docstring_vs_signature"
    TODO_ABANDONED = "todo_abandoned"
    DEAD_IMPORT = "dead_import"
    CONFIG_VS_USAGE = "config_vs_usage"


class Severity(Enum):
    """How loud the lie is."""

    WHISPER = "whisper"  # Cosmetic. Will confuse interns.
    MURMUR = "murmur"  # Misleading. Will cost someone an afternoon.
    SHOUT = "shout"  # Dangerous. Will cause a production incident.


@dataclass(frozen=True)
class Artifact:
    """A single discovered drift between intention and reality."""

    drift_type: DriftType
    severity: Severity
    file_path: Path
    line_start: int
    line_end: int
    claim: str  # What the code *says*
    reality: str  # What the code *does*
    evidence: str  # The raw text that proves the drift
    discovered_at: datetime = field(default_factory=datetime.now)
    git_blame_age_days: Optional[int] = None

    @property
    def fingerprint(self) -> str:
        """Stable identity for deduplication across runs."""
        raw = f"{self.drift_type.value}:{self.file_path}:{self.line_start}:{self.claim}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    @property
    def stale(self) -> bool:
        """Has this drift been sitting here for an embarrassingly long time?"""
        if self.git_blame_age_days is None:
            return False
        return self.git_blame_age_days > 180

    def to_dict(self) -> dict:
        return {
            "id": self.fingerprint,
            "type": self.drift_type.value,
            "severity": self.severity.value,
            "file": str(self.file_path),
            "lines": [self.line_start, self.line_end],
            "claim": self.claim,
            "reality": self.reality,
            "evidence": self.evidence,
            "stale": self.stale,
            "blame_age_days": self.git_blame_age_days,
        }

    def __str__(self) -> str:
        icon = {"whisper": "🤫", "murmur": "🗣️", "shout": "📢"}[self.severity.value]
        return (
            f"{icon} [{self.drift_type.value}] {self.file_path}:{self.line_start}\n"
            f"   Claims: {self.claim}\n"
            f"   Reality: {self.reality}"
        )

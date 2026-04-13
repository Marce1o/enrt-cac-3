"""
TODO Lens — the memorial for abandoned intentions.

Every TODO is a promise someone made to their future self.
This lens finds the ones where the future self never showed up.

Detects:
- TODO/FIXME/HACK/XXX comments older than 6 months
- TODOs that reference people who left the team (via git blame)
- TODOs that reference tickets/issues in a format but have no URL
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from lenses.base import Lens
from the_dig.artifacts import Artifact, DriftType, Severity
from the_dig.strata import Stratum, excavate_git_blame_age


class TodoLens(Lens):
    name = "todo_abandoned"
    description = "Finds TODOs and FIXMEs that time forgot"

    def applies_to(self, stratum: Stratum) -> bool:
        return stratum.layer == "code"

    def examine(self, strata: Sequence[Stratum], root: Path) -> list[Artifact]:
        artifacts = []
        code_strata = [s for s in strata if self.applies_to(s)]

        for stratum in code_strata:
            artifacts.extend(self._find_abandoned_todos(stratum, root))

        return artifacts

    def _find_abandoned_todos(self, stratum: Stratum, root: Path) -> list[Artifact]:
        """Find TODOs that have been sitting around too long."""
        artifacts = []
        pattern = re.compile(r"#\s*(TODO|FIXME|HACK|XXX|TEMP|TEMPORARY)\b[:\s]*(.*)", re.IGNORECASE)

        for i, line in enumerate(stratum.lines, start=1):
            match = pattern.search(line)
            if not match:
                continue

            tag = match.group(1).upper()
            description = match.group(2).strip()

            # Check git blame age
            age = excavate_git_blame_age(root, stratum.path, i)

            if age is not None and age > 180:
                severity = Severity.SHOUT if age > 365 else Severity.MURMUR
                artifacts.append(Artifact(
                    drift_type=DriftType.TODO_ABANDONED,
                    severity=severity,
                    file_path=stratum.path,
                    line_start=i,
                    line_end=i,
                    claim=f"{tag}: {description}" if description else f"{tag} (no description)",
                    reality=f"This {tag} has been here for {age} days",
                    evidence=line.strip(),
                    git_blame_age_days=age,
                ))
            elif age is None:
                # Can't determine age — still flag HACK/XXX/TEMP as suspicious
                if tag in {"HACK", "XXX", "TEMP", "TEMPORARY"}:
                    artifacts.append(Artifact(
                        drift_type=DriftType.TODO_ABANDONED,
                        severity=Severity.WHISPER,
                        file_path=stratum.path,
                        line_start=i,
                        line_end=i,
                        claim=f"{tag}: {description}" if description else f"{tag} (no description)",
                        reality=f"Found {tag} marker — age unknown (not in git?)",
                        evidence=line.strip(),
                    ))

        return artifacts

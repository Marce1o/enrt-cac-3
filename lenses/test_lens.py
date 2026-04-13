"""
Test Lens — the optimism checker.

Test names are promises. `test_handles_empty_input` promises that
someone verified the empty-input path. But test names outlive their
implementations. A rename here, a refactor there, and suddenly
`test_handles_empty_input` is actually testing a happy path.

This lens compares what test names *claim* to verify against what
the test body *actually* does.

Detects:
- Tests named "test_X" that never reference X in their body
- Tests with no assertions (theater tests)
- Tests that catch exceptions but don't assert on them (suppression tests)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from lenses.base import Lens
from the_dig.artifacts import Artifact, DriftType, Severity
from the_dig.strata import Stratum


class TestLens(Lens):
    name = "test_name_vs_assertion"
    description = "Checks if test names match what tests actually verify"

    def applies_to(self, stratum: Stratum) -> bool:
        return stratum.layer == "code" and "test" in str(stratum.path).lower()

    def examine(self, strata: Sequence[Stratum], root: Path) -> list[Artifact]:
        artifacts = []
        test_strata = [s for s in strata if self.applies_to(s)]

        for stratum in test_strata:
            artifacts.extend(self._check_name_vs_body(stratum))
            artifacts.extend(self._check_theater_tests(stratum))
            artifacts.extend(self._check_exception_suppression(stratum))

        return artifacts

    def _extract_test_functions(self, stratum: Stratum) -> list[tuple[int, int, str, str]]:
        """Extract (start_line, end_line, name, body) for each test function."""
        tests = []
        lines = stratum.lines
        i = 0
        while i < len(lines):
            match = re.match(r"(\s*)def\s+(test_\w+)\s*\(", lines[i])
            if match:
                indent = len(match.group(1))
                name = match.group(2)
                start = i + 1
                body_lines = []
                j = i + 1
                while j < len(lines):
                    if lines[j].strip() == "":
                        body_lines.append(lines[j])
                        j += 1
                        continue
                    line_indent = len(lines[j]) - len(lines[j].lstrip())
                    if line_indent <= indent and lines[j].strip():
                        break
                    body_lines.append(lines[j])
                    j += 1
                tests.append((start, j, name, "\n".join(body_lines)))
                i = j
            else:
                i += 1
        return tests

    def _check_name_vs_body(self, stratum: Stratum) -> list[Artifact]:
        """Does the test name reflect what it actually tests?"""
        artifacts = []
        tests = self._extract_test_functions(stratum)

        for start, end, name, body in tests:
            # Parse the test name into meaningful words
            parts = name.replace("test_", "").split("_")
            # Filter out short/common words
            keywords = [p for p in parts if len(p) > 2 and p not in {
                "the", "and", "for", "that", "with", "when", "should",
                "does", "can", "not", "has", "its", "this", "are", "was",
            }]

            if not keywords:
                continue

            # Check if any keyword appears in the body
            body_lower = body.lower()
            matches = sum(1 for k in keywords if k.lower() in body_lower)

            if matches == 0 and len(keywords) >= 2:
                artifacts.append(Artifact(
                    drift_type=DriftType.TEST_NAME_VS_ASSERTION,
                    severity=Severity.MURMUR,
                    file_path=stratum.path,
                    line_start=start,
                    line_end=end,
                    claim=f"Test `{name}` should verify: {', '.join(keywords)}",
                    reality=f"None of these keywords appear in the test body",
                    evidence=body[:200],
                ))

        return artifacts

    def _check_theater_tests(self, stratum: Stratum) -> list[Artifact]:
        """Find tests with no assertions — pure theater."""
        artifacts = []
        tests = self._extract_test_functions(stratum)

        assertion_patterns = [
            r"assert\s", r"assert_", r"\.assert", r"assertEqual",
            r"assertTrue", r"assertFalse", r"assertRaises", r"assertIn",
            r"pytest\.raises", r"expect\(", r"should\.",
        ]

        for start, end, name, body in tests:
            has_assertion = any(
                re.search(pat, body) for pat in assertion_patterns
            )
            if not has_assertion and len(body.strip()) > 0:
                artifacts.append(Artifact(
                    drift_type=DriftType.TEST_NAME_VS_ASSERTION,
                    severity=Severity.SHOUT,
                    file_path=stratum.path,
                    line_start=start,
                    line_end=end,
                    claim=f"`{name}` is a test",
                    reality="Contains zero assertions. This is theater.",
                    evidence=body[:200],
                ))

        return artifacts

    def _check_exception_suppression(self, stratum: Stratum) -> list[Artifact]:
        """Find try/except in tests that swallow errors without asserting."""
        artifacts = []
        tests = self._extract_test_functions(stratum)

        for start, end, name, body in tests:
            # Look for bare except or except Exception with pass/continue
            suppression = re.search(
                r"except\s+(\w+)?.*?:\s*\n\s*(pass|continue|\.\.\.)",
                body, re.DOTALL
            )
            if suppression:
                artifacts.append(Artifact(
                    drift_type=DriftType.TEST_NAME_VS_ASSERTION,
                    severity=Severity.SHOUT,
                    file_path=stratum.path,
                    line_start=start,
                    line_end=end,
                    claim=f"`{name}` handles errors",
                    reality="Catches exceptions and swallows them silently",
                    evidence=suppression.group(0),
                ))

        return artifacts

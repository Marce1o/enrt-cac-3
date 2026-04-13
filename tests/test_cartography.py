"""
Tests for cartography — report generation and timeline analysis.
"""

from pathlib import Path

import pytest

from the_dig.artifacts import Artifact, DriftType, Severity
from the_dig.fieldnotes import FieldNotes
from cartography.drift_map import DriftMap
from cartography.timeline import DriftTimeline


def _make_artifact(drift_type=DriftType.COMMENT_VS_CODE, severity=Severity.MURMUR,
                   file_path="app.py", line=10, age=None):
    return Artifact(
        drift_type=drift_type,
        severity=severity,
        file_path=Path(file_path),
        line_start=line,
        line_end=line,
        claim="It says X",
        reality="It does Y",
        evidence="# X\ndo_y()",
        git_blame_age_days=age,
    )


class TestFieldNotes:
    def test_deduplicates(self):
        notes = FieldNotes()
        a = _make_artifact()
        notes.record(a)
        notes.record(a)  # Same artifact
        assert notes.total == 1

    def test_severity_filtering(self):
        notes = FieldNotes()
        notes.record(_make_artifact(severity=Severity.SHOUT))
        notes.record(_make_artifact(severity=Severity.WHISPER, line=20))
        notes.record(_make_artifact(severity=Severity.MURMUR, line=30))
        assert len(notes.shouts) == 1
        assert len(notes.whispers) == 1
        assert len(notes.murmurs) == 1

    def test_summary_line_clean(self):
        notes = FieldNotes()
        assert "honest" in notes.summary_line().lower() or "no drift" in notes.summary_line().lower()

    def test_summary_line_with_findings(self):
        notes = FieldNotes()
        notes.record(_make_artifact(severity=Severity.SHOUT))
        line = notes.summary_line()
        assert "shout" in line.lower()


class TestDriftMap:
    def test_renders_empty_report(self):
        notes = FieldNotes(files_scanned=5, strata_examined=10)
        report = DriftMap(notes).render_markdown()
        assert "Nothing to report" in report

    def test_renders_report_with_findings(self):
        notes = FieldNotes(files_scanned=5, strata_examined=10)
        notes.record(_make_artifact(severity=Severity.SHOUT))
        notes.record(_make_artifact(severity=Severity.WHISPER, line=20))
        report = DriftMap(notes).render_markdown()
        assert "Shouts" in report
        assert "Whispers" in report
        assert "app.py" in report

    def test_json_output(self):
        import json
        notes = FieldNotes(files_scanned=1, strata_examined=1)
        notes.record(_make_artifact())
        raw = DriftMap(notes).render_json()
        data = json.loads(raw)
        assert data["total"] == 1
        assert len(data["artifacts"]) == 1


class TestDriftTimeline:
    def test_age_distribution(self):
        notes = FieldNotes()
        notes.record(_make_artifact(age=10, line=1))
        notes.record(_make_artifact(age=100, line=2))
        notes.record(_make_artifact(age=400, line=3))

        timeline = DriftTimeline(notes)
        dist = timeline.age_distribution()
        assert dist.get("< 1 month", 0) == 1
        assert dist.get("> 1 year", 0) == 1

    def test_staleness_score(self):
        notes = FieldNotes()
        notes.record(_make_artifact(age=730, line=1))  # 2 years = max
        timeline = DriftTimeline(notes)
        assert timeline.staleness_score() == pytest.approx(1.0, abs=0.01)

    def test_staleness_score_fresh(self):
        notes = FieldNotes()
        notes.record(_make_artifact(age=1, line=1))
        timeline = DriftTimeline(notes)
        assert timeline.staleness_score() < 0.01

    def test_ascii_histogram(self):
        notes = FieldNotes()
        notes.record(_make_artifact(age=50, line=1))
        timeline = DriftTimeline(notes)
        hist = timeline.render_ascii_histogram()
        assert "█" in hist

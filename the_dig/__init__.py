"""
the_dig — the excavation site.

This isn't a source directory. It's a dig site.
Every codebase accumulates layers of sediment: decisions made in haste,
comments written for a version that no longer exists, READMEs that describe
what someone *wished* the code did.

Drift happens when nobody's watching.
This package watches.
"""

from the_dig.artifacts import Artifact, DriftType, Severity
from the_dig.strata import Stratum, excavate
from the_dig.fieldnotes import FieldNotes

__all__ = ["Artifact", "DriftType", "Severity", "Stratum", "excavate", "FieldNotes"]

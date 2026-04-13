"""
Base lens — the protocol every lens must follow.

A lens takes strata and returns artifacts. That's the contract.
How it decides what counts as drift is its own business.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Sequence

from the_dig.artifacts import Artifact
from the_dig.strata import Stratum


class Lens(ABC):
    """Abstract base for all drift-detection lenses."""

    name: str = "unnamed"
    description: str = ""

    @abstractmethod
    def examine(self, strata: Sequence[Stratum], root: Path) -> list[Artifact]:
        """Look through this lens at the given strata. Return what you find."""
        ...

    def applies_to(self, stratum: Stratum) -> bool:
        """Can this lens see anything useful in this stratum?"""
        return True

    def __repr__(self) -> str:
        return f"<Lens:{self.name}>"

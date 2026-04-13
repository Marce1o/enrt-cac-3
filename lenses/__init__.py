"""
Lenses — ways of seeing drift.

A lens is not a linter. A linter checks if code follows rules.
A lens checks if a codebase is honest with itself.

Each lens compares two layers of truth and reports where they disagree.
"""

from lenses.base import Lens
from lenses.readme_lens import ReadmeLens
from lenses.comment_lens import CommentLens
from lenses.test_lens import TestLens
from lenses.docstring_lens import DocstringLens
from lenses.todo_lens import TodoLens

ALL_LENSES: list[type[Lens]] = [
    ReadmeLens,
    CommentLens,
    TestLens,
    DocstringLens,
    TodoLens,
]

__all__ = [
    "Lens",
    "ReadmeLens",
    "CommentLens",
    "TestLens",
    "DocstringLens",
    "TodoLens",
    "ALL_LENSES",
]

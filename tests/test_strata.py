"""
Tests for the core engine: strata extraction and excavation.
"""

import textwrap
from pathlib import Path

import pytest

from the_dig.strata import Stratum


class TestStratumCommentExtraction:
    def test_extracts_standalone_comments(self):
        code = textwrap.dedent("""\
            # This is a comment
            x = 1
            # Another comment
            y = 2
        """)
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        comments = s.extract_comments()
        assert len(comments) == 2
        assert comments[0] == (1, "This is a comment")
        assert comments[1] == (3, "Another comment")

    def test_extracts_inline_comments(self):
        code = "x = 1  # inline comment\n"
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        comments = s.extract_comments()
        assert len(comments) == 1
        assert "inline comment" in comments[0][1]

    def test_ignores_shebangs(self):
        code = "#!/usr/bin/env python\n# real comment\n"
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        comments = s.extract_comments()
        assert len(comments) == 1
        assert comments[0][1] == "real comment"


class TestStratumDocstringExtraction:
    def test_extracts_single_line_docstring(self):
        code = textwrap.dedent('''\
            def hello():
                """Say hello."""
                pass
        ''')
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        docstrings = s.extract_docstrings()
        assert len(docstrings) == 1
        assert "Say hello" in docstrings[0][2]

    def test_extracts_multiline_docstring(self):
        code = textwrap.dedent('''\
            def hello():
                """
                Say hello to the world.
                This is a longer description.
                """
                pass
        ''')
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        docstrings = s.extract_docstrings()
        assert len(docstrings) == 1
        assert "hello" in docstrings[0][2].lower()


class TestStratumSignatureExtraction:
    def test_extracts_simple_function(self):
        code = "def add(a, b):\n    return a + b\n"
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        sigs = s.extract_function_signatures()
        assert len(sigs) == 1
        assert sigs[0][1] == "add"
        assert sigs[0][2] == ["a", "b"]

    def test_excludes_self(self):
        code = "def method(self, x):\n    pass\n"
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        sigs = s.extract_function_signatures()
        assert sigs[0][2] == ["x"]

    def test_handles_type_annotations(self):
        code = "def greet(name: str, age: int = 0):\n    pass\n"
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        sigs = s.extract_function_signatures()
        assert sigs[0][2] == ["name", "age"]

    def test_handles_no_params(self):
        code = "def noop():\n    pass\n"
        s = Stratum(path=Path("test.py"), content=code, layer="code")
        sigs = s.extract_function_signatures()
        assert sigs[0][2] == []

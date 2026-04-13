"""
Tests for drift lenses — the core detection logic.
"""

import textwrap
from pathlib import Path

import pytest

from the_dig.strata import Stratum
from the_dig.artifacts import DriftType, Severity


class TestCommentLens:
    def setup_method(self):
        from lenses.comment_lens import CommentLens
        self.lens = CommentLens()

    def test_detects_commented_out_code(self):
        code = textwrap.dedent("""\
            x = 1
            # if something:
            #     do_thing()
            #     do_other_thing()
            #     return result
            y = 2
        """)
        stratum = Stratum(path=Path("app.py"), content=code, layer="code")
        artifacts = self.lens.examine([stratum], Path("."))
        commented_code = [a for a in artifacts if "commented-out code" in a.reality]
        assert len(commented_code) >= 1

    def test_ignores_prose_comments(self):
        code = textwrap.dedent("""\
            # This module handles user authentication.
            # It provides login and logout functionality.
            # See the README for more details.
            def login():
                pass
        """)
        stratum = Stratum(path=Path("auth.py"), content=code, layer="code")
        artifacts = self.lens.examine([stratum], Path("."))
        commented_code = [a for a in artifacts if "commented-out code" in a.reality]
        assert len(commented_code) == 0


class TestTestLens:
    def setup_method(self):
        from lenses.test_lens import TestLens
        self.lens = TestLens()

    def test_detects_theater_tests(self):
        code = textwrap.dedent("""\
            def test_validates_email():
                email = "user@example.com"
                result = validate(email)
                # Look ma, no assertion!
        """)
        stratum = Stratum(path=Path("tests/test_email.py"), content=code, layer="code")
        artifacts = self.lens.examine([stratum], Path("."))
        theater = [a for a in artifacts if "theater" in a.reality.lower()]
        assert len(theater) == 1
        assert theater[0].severity == Severity.SHOUT

    def test_accepts_tests_with_assertions(self):
        code = textwrap.dedent("""\
            def test_adds_numbers():
                result = add(2, 3)
                assert result == 5
        """)
        stratum = Stratum(path=Path("tests/test_math.py"), content=code, layer="code")
        artifacts = self.lens.examine([stratum], Path("."))
        theater = [a for a in artifacts if "theater" in a.reality.lower()]
        assert len(theater) == 0

    def test_detects_exception_suppression(self):
        code = textwrap.dedent("""\
            def test_handles_error():
                try:
                    risky_operation()
                except Exception:
                    pass
        """)
        stratum = Stratum(path=Path("tests/test_ops.py"), content=code, layer="code")
        artifacts = self.lens.examine([stratum], Path("."))
        suppression = [a for a in artifacts if "swallow" in a.reality.lower()]
        assert len(suppression) >= 1


class TestDocstringLens:
    def setup_method(self):
        from lenses.docstring_lens import DocstringLens
        self.lens = DocstringLens()

    def test_detects_phantom_param(self):
        code = textwrap.dedent('''\
            def connect(host, port):
                """
                Connect to the server.

                Args:
                    host: The hostname
                    port: The port number
                    timeout: Connection timeout in seconds
                """
                pass
        ''')
        stratum = Stratum(path=Path("client.py"), content=code, layer="code")
        artifacts = self.lens.examine([stratum], Path("."))
        phantom = [a for a in artifacts if "timeout" in a.claim]
        assert len(phantom) >= 1

    def test_clean_docstring_no_drift(self):
        code = textwrap.dedent('''\
            def greet(name):
                """
                Greet someone.

                Args:
                    name: Who to greet
                """
                return f"Hello, {name}"
        ''')
        stratum = Stratum(path=Path("hello.py"), content=code, layer="code")
        artifacts = self.lens.examine([stratum], Path("."))
        assert len(artifacts) == 0


class TestTodoLens:
    def setup_method(self):
        from lenses.todo_lens import TodoLens
        self.lens = TodoLens()

    def test_flags_hack_markers(self):
        code = textwrap.dedent("""\
            def process():
                # HACK: this is terrible but it works
                return 42
        """)
        stratum = Stratum(path=Path("proc.py"), content=code, layer="code")
        artifacts = self.lens.examine([stratum], Path("/nonexistent"))
        hack = [a for a in artifacts if "HACK" in a.claim]
        assert len(hack) >= 1

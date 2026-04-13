"""
Strata — the layers of a codebase.

A Stratum is a snapshot of a file at a point in time, carrying both its
content and its metadata. When you excavate a repository, you produce
strata. When you compare strata through different lenses, you find drift.

Think of it like this:
- Layer 0: what the code does right now
- Layer 1: what the comments say it does
- Layer 2: what the README says it does
- Layer 3: what the tests claim to verify
- Layer N: what someone said in a PR six months ago

Every layer is true in its own way. Drift lives in the gaps between them.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator, Optional


@dataclass
class Stratum:
    """One layer of truth about a file."""

    path: Path
    content: str
    layer: str  # "code", "comments", "readme", "tests", "docstrings", "git_log"
    metadata: dict = field(default_factory=dict)

    @property
    def lines(self) -> list[str]:
        return self.content.splitlines()

    @property
    def is_empty(self) -> bool:
        return len(self.content.strip()) == 0

    def extract_comments(self) -> list[tuple[int, str]]:
        """Pull inline comments from code. Returns (line_number, comment_text)."""
        results = []
        for i, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!"):
                results.append((i, stripped.lstrip("# ")))
            elif "  #" in line or "\t#" in line:
                idx = line.index("#")
                results.append((i, line[idx:].lstrip("# ")))
        return results

    def extract_docstrings(self) -> list[tuple[int, int, str]]:
        """Pull docstrings. Returns (start_line, end_line, docstring_text)."""
        results = []
        in_docstring = False
        start = 0
        buffer: list[str] = []
        for i, line in enumerate(self.lines, start=1):
            stripped = line.strip()
            if not in_docstring and (stripped.startswith('"""') or stripped.startswith("'''")):
                quote = stripped[:3]
                if stripped.count(quote) >= 2 and len(stripped) > 6:
                    # Single-line docstring
                    results.append((i, i, stripped.strip(quote[0]).strip()))
                else:
                    in_docstring = True
                    start = i
                    remainder = stripped[3:]
                    if remainder:
                        buffer.append(remainder)
            elif in_docstring:
                if '"""' in stripped or "'''" in stripped:
                    in_docstring = False
                    remainder = stripped.replace('"""', "").replace("'''", "").strip()
                    if remainder:
                        buffer.append(remainder)
                    results.append((start, i, "\n".join(buffer)))
                    buffer = []
                else:
                    buffer.append(stripped)
        return results

    def extract_function_signatures(self) -> list[tuple[int, str, list[str]]]:
        """Pull function signatures. Returns (line, name, param_names)."""
        import re

        results = []
        for i, line in enumerate(self.lines, start=1):
            match = re.match(r"\s*def\s+(\w+)\s*\(([^)]*)\)", line)
            if match:
                name = match.group(1)
                params_raw = match.group(2)
                params = [
                    p.strip().split(":")[0].split("=")[0].strip()
                    for p in params_raw.split(",")
                    if p.strip() and p.strip() != "self" and p.strip() != "cls"
                ]
                results.append((i, name, params))
        return results


def excavate(root: Path, extensions: Optional[set[str]] = None) -> Iterator[Stratum]:
    """
    Walk a directory and yield strata for every relevant file.
    This is the entry point for the dig.
    """
    if extensions is None:
        extensions = {".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".rb"}

    root = root.resolve()

    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if any(part.startswith(".") for part in path.parts):
            continue
        if "__pycache__" in path.parts or "node_modules" in path.parts:
            continue

        relative = path.relative_to(root)

        # README files get their own layer
        if path.name.lower().startswith("readme"):
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                yield Stratum(path=relative, content=content, layer="readme")
            except (OSError, UnicodeDecodeError):
                pass
            continue

        # Source files
        if path.suffix in extensions:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                yield Stratum(path=relative, content=content, layer="code")
            except (OSError, UnicodeDecodeError):
                pass
            continue

        # Config / TOML / YAML / JSON
        if path.suffix in {".toml", ".yaml", ".yml", ".json"}:
            try:
                content = path.read_text(encoding="utf-8", errors="replace")
                yield Stratum(
                    path=relative, content=content, layer="config",
                    metadata={"format": path.suffix.lstrip(".")}
                )
            except (OSError, UnicodeDecodeError):
                pass


def excavate_git_log(root: Path, file_path: Path, max_entries: int = 50) -> Optional[Stratum]:
    """Dig into git history for a specific file."""
    try:
        result = subprocess.run(
            ["git", "log", f"--max-count={max_entries}", "--format=%H|%ai|%s", "--", str(file_path)],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0 and result.stdout.strip():
            return Stratum(
                path=file_path,
                content=result.stdout.strip(),
                layer="git_log",
                metadata={"entries": len(result.stdout.strip().splitlines())},
            )
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    return None


def excavate_git_blame_age(root: Path, file_path: Path, line: int) -> Optional[int]:
    """How many days ago was this line last touched?"""
    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{line},{line}", "--porcelain", "--", str(file_path)],
            cwd=root, capture_output=True, text=True, timeout=10,
        )
        if result.returncode == 0:
            for blame_line in result.stdout.splitlines():
                if blame_line.startswith("committer-time"):
                    import time
                    ts = int(blame_line.split()[-1])
                    age = (time.time() - ts) / 86400
                    return int(age)
    except (subprocess.SubprocessError, FileNotFoundError, ValueError):
        pass
    return None

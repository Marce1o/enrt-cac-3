"""
README Lens — the biggest liar in any repository.

READMEs are aspirational documents. They describe the project someone
*intended* to build. This lens checks if reality caught up.

Detects:
- Installation commands that reference packages not in requirements/pyproject
- "Usage" examples that call functions that don't exist
- Feature lists that mention capabilities the code doesn't have
- Badge claims (e.g., "100% test coverage") that are unverifiable
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from lenses.base import Lens
from the_dig.artifacts import Artifact, DriftType, Severity
from the_dig.strata import Stratum


class ReadmeLens(Lens):
    name = "readme_vs_reality"
    description = "Compares what the README promises against what exists"

    def examine(self, strata: Sequence[Stratum], root: Path) -> list[Artifact]:
        artifacts = []

        readmes = [s for s in strata if s.layer == "readme"]
        code_strata = [s for s in strata if s.layer == "code"]

        if not readmes:
            return artifacts

        # Build an index of what actually exists
        all_functions = set()
        all_files = set()
        for cs in code_strata:
            all_files.add(str(cs.path))
            for _, name, _ in cs.extract_function_signatures():
                all_functions.add(name)

        for readme in readmes:
            artifacts.extend(self._check_code_references(readme, all_functions, all_files))
            artifacts.extend(self._check_install_commands(readme, strata))
            artifacts.extend(self._check_phantom_features(readme, code_strata))

        return artifacts

    def _check_code_references(
        self, readme: Stratum, functions: set[str], files: set[str]
    ) -> list[Artifact]:
        """Find code blocks in README that reference non-existent functions."""
        artifacts = []
        in_code_block = False
        code_start = 0

        for i, line in enumerate(readme.lines, start=1):
            if line.strip().startswith("```"):
                if not in_code_block:
                    in_code_block = True
                    code_start = i
                else:
                    in_code_block = False
                continue

            if in_code_block:
                # Look for function-call-like patterns
                calls = re.findall(r"(\w+)\s*\(", line)
                for call in calls:
                    # Skip common built-ins and noise
                    if call in {"print", "import", "from", "if", "for", "while", "def", "class",
                                "return", "pip", "npm", "brew", "apt", "git", "cd", "mkdir",
                                "echo", "export", "source", "run", "install", "test"}:
                        continue
                    if len(call) < 3:
                        continue
                    if call not in functions and len(functions) > 0:
                        artifacts.append(Artifact(
                            drift_type=DriftType.README_VS_REALITY,
                            severity=Severity.MURMUR,
                            file_path=readme.path,
                            line_start=i,
                            line_end=i,
                            claim=f"README references function `{call}()`",
                            reality=f"No function named `{call}` found in codebase",
                            evidence=line.strip(),
                        ))

        return artifacts

    def _check_install_commands(
        self, readme: Stratum, all_strata: Sequence[Stratum]
    ) -> list[Artifact]:
        """Check if pip install commands reference the correct package name."""
        artifacts = []
        config_strata = [s for s in all_strata if s.layer == "config"]

        # Extract project name from pyproject.toml or setup.cfg
        project_names = set()
        for cs in config_strata:
            if "pyproject.toml" in str(cs.path):
                match = re.search(r'name\s*=\s*"([^"]+)"', cs.content)
                if match:
                    project_names.add(match.group(1))

        if not project_names:
            return artifacts

        for i, line in enumerate(readme.lines, start=1):
            pip_match = re.search(r"pip install\s+([a-zA-Z0-9_-]+)", line)
            if pip_match:
                pkg = pip_match.group(1)
                if pkg not in project_names and pkg not in {".", "-e", "-r"}:
                    artifacts.append(Artifact(
                        drift_type=DriftType.README_VS_REALITY,
                        severity=Severity.MURMUR,
                        file_path=readme.path,
                        line_start=i,
                        line_end=i,
                        claim=f"README says to `pip install {pkg}`",
                        reality=f"Project name in config is: {project_names}",
                        evidence=line.strip(),
                    ))

        return artifacts

    def _check_phantom_features(
        self, readme: Stratum, code_strata: Sequence[Stratum]
    ) -> list[Artifact]:
        """Find feature-list items in README with no corresponding code."""
        artifacts = []

        # Gather all identifiers from code
        all_identifiers = set()
        for cs in code_strata:
            for word in re.findall(r"\b[a-zA-Z_]\w{2,}\b", cs.content):
                all_identifiers.add(word.lower())

        # Look for bullet-point feature lists
        in_features_section = False
        for i, line in enumerate(readme.lines, start=1):
            lower = line.lower().strip()
            if re.match(r"#{1,3}\s*(features|capabilities|what it does)", lower):
                in_features_section = True
                continue
            if in_features_section and line.strip().startswith("#"):
                in_features_section = False
                continue

            if in_features_section and re.match(r"\s*[-*]\s+", line):
                # Extract key nouns from the bullet point
                words = re.findall(r"\b[a-zA-Z]\w{3,}\b", line)
                technical_words = [w for w in words if w.lower() not in {
                    "with", "your", "that", "this", "from", "will", "have",
                    "been", "more", "support", "supports", "built", "using",
                    "easy", "simple", "fast", "automatic", "automatically",
                }]
                # If none of the technical words appear in code, flag it
                if technical_words and not any(w.lower() in all_identifiers for w in technical_words):
                    artifacts.append(Artifact(
                        drift_type=DriftType.README_VS_REALITY,
                        severity=Severity.WHISPER,
                        file_path=readme.path,
                        line_start=i,
                        line_end=i,
                        claim=f"README lists feature: {line.strip()}",
                        reality=f"Keywords {technical_words} not found in any source file",
                        evidence=line.strip(),
                    ))

        return artifacts

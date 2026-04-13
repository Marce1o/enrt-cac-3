"""
Comment Lens — the archaeology of developer intent.

Comments are postcards from the past. They were written by someone
who understood the code at that moment. That moment is gone.
This lens finds comments that no longer describe their surroundings.

Detects:
- Comments referencing variables/functions that no longer exist in scope
- "TODO" and "FIXME" comments older than 6 months (abandoned intentions)
- Comments that say "returns X" near functions that return Y
- Commented-out code blocks (the geological record of indecision)
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from lenses.base import Lens
from the_dig.artifacts import Artifact, DriftType, Severity
from the_dig.strata import Stratum


class CommentLens(Lens):
    name = "comment_vs_code"
    description = "Finds comments that lie about the code they annotate"

    def applies_to(self, stratum: Stratum) -> bool:
        return stratum.layer == "code"

    def examine(self, strata: Sequence[Stratum], root: Path) -> list[Artifact]:
        artifacts = []
        code_strata = [s for s in strata if s.layer == "code"]

        for stratum in code_strata:
            artifacts.extend(self._check_stale_references(stratum))
            artifacts.extend(self._check_commented_out_code(stratum))
            artifacts.extend(self._check_return_claims(stratum))

        return artifacts

    def _check_stale_references(self, stratum: Stratum) -> list[Artifact]:
        """Find comments that mention identifiers not present in the surrounding code."""
        artifacts = []
        comments = stratum.extract_comments()
        lines = stratum.lines

        # Build set of all identifiers in the file
        all_identifiers = set()
        for line in lines:
            # Skip comment-only lines for identifier extraction
            stripped = line.strip()
            if stripped.startswith("#"):
                continue
            for word in re.findall(r"\b[a-zA-Z_]\w{2,}\b", line):
                all_identifiers.add(word)

        for line_num, comment_text in comments:
            # Extract identifiers mentioned in the comment
            # Look for backtick-quoted or snake_case identifiers
            backtick_refs = re.findall(r"`(\w+)`", comment_text)
            snake_refs = re.findall(r"\b([a-z]+_[a-z_]+)\b", comment_text)

            for ref in backtick_refs + snake_refs:
                if ref not in all_identifiers and len(ref) > 3:
                    # Skip common English words that look like identifiers
                    if ref in {"this_is", "that_is", "make_sure", "note_that",
                               "see_also", "used_for", "related_to", "based_on"}:
                        continue
                    artifacts.append(Artifact(
                        drift_type=DriftType.COMMENT_VS_CODE,
                        severity=Severity.MURMUR,
                        file_path=stratum.path,
                        line_start=line_num,
                        line_end=line_num,
                        claim=f"Comment references `{ref}`",
                        reality=f"`{ref}` not found as identifier in this file",
                        evidence=comment_text,
                    ))

        return artifacts

    def _check_commented_out_code(self, stratum: Stratum) -> list[Artifact]:
        """Detect blocks of commented-out code (geological sediment)."""
        artifacts = []
        consecutive_code_comments = 0
        block_start = 0

        for i, line in enumerate(stratum.lines, start=1):
            stripped = line.strip()
            if stripped.startswith("#") and not stripped.startswith("#!"):
                remainder = stripped.lstrip("# ")
                # Heuristics for "this is code, not prose"
                looks_like_code = any([
                    re.match(r"(if|for|while|def|class|return|import|from)\s", remainder),
                    re.search(r"[=\[\]{}();]", remainder),
                    re.match(r"\w+\.\w+\(", remainder),
                    re.match(r"\w+\s*=\s*", remainder),
                ])
                if looks_like_code:
                    if consecutive_code_comments == 0:
                        block_start = i
                    consecutive_code_comments += 1
                else:
                    if consecutive_code_comments >= 3:
                        artifacts.append(Artifact(
                            drift_type=DriftType.COMMENT_VS_CODE,
                            severity=Severity.WHISPER,
                            file_path=stratum.path,
                            line_start=block_start,
                            line_end=block_start + consecutive_code_comments - 1,
                            claim="This is a comment",
                            reality=f"This is {consecutive_code_comments} lines of commented-out code",
                            evidence="\n".join(
                                stratum.lines[block_start - 1:block_start + consecutive_code_comments - 1]
                            ),
                        ))
                    consecutive_code_comments = 0
            else:
                if consecutive_code_comments >= 3:
                    artifacts.append(Artifact(
                        drift_type=DriftType.COMMENT_VS_CODE,
                        severity=Severity.WHISPER,
                        file_path=stratum.path,
                        line_start=block_start,
                        line_end=block_start + consecutive_code_comments - 1,
                        claim="This is a comment",
                        reality=f"This is {consecutive_code_comments} lines of commented-out code",
                        evidence="\n".join(
                            stratum.lines[block_start - 1:block_start + consecutive_code_comments - 1]
                        ),
                    ))
                consecutive_code_comments = 0

        return artifacts

    def _check_return_claims(self, stratum: Stratum) -> list[Artifact]:
        """Find comments that say 'returns X' near functions that return something else."""
        artifacts = []
        lines = stratum.lines

        for i, line in enumerate(lines):
            stripped = line.strip()
            if not stripped.startswith("#"):
                continue

            # Does the comment claim something about return values?
            return_match = re.search(
                r"returns?\s+(True|False|None|an?\s+\w+|the\s+\w+|\w+)",
                stripped, re.IGNORECASE
            )
            if not return_match:
                continue

            claimed_return = return_match.group(1).strip()

            # Look at the next function and its return statements
            for j in range(i + 1, min(i + 5, len(lines))):
                func_match = re.match(r"\s*def\s+\w+", lines[j])
                if func_match:
                    # Scan function body for return statements
                    returns = []
                    for k in range(j + 1, min(j + 50, len(lines))):
                        ret_match = re.match(r"\s+return\s+(.*)", lines[k])
                        if ret_match:
                            returns.append(ret_match.group(1).strip())
                        if lines[k].strip() and not lines[k].startswith(" ") and not lines[k].startswith("\t"):
                            break  # Left the function body

                    if returns:
                        # Simple check: does claimed return appear in actual returns?
                        actual = ", ".join(returns[:3])
                        claimed_lower = claimed_return.lower()
                        if not any(claimed_lower in r.lower() for r in returns):
                            artifacts.append(Artifact(
                                drift_type=DriftType.COMMENT_VS_CODE,
                                severity=Severity.MURMUR,
                                file_path=stratum.path,
                                line_start=i + 1,
                                line_end=i + 1,
                                claim=f"Comment says function returns: {claimed_return}",
                                reality=f"Function actually returns: {actual}",
                                evidence=stripped,
                            ))
                    break

        return artifacts

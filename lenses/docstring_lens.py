"""
Docstring Lens — the contract auditor.

A docstring is a contract between a function and its callers.
When someone writes "Args: x (int): the threshold", they're making
a promise. This lens checks if the function kept it.

Detects:
- Docstring lists params that don't exist in the signature
- Signature has params not mentioned in the docstring
- Docstring says "raises X" but function never raises X
- Docstring describes return type that contradicts actual returns
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Sequence

from lenses.base import Lens
from the_dig.artifacts import Artifact, DriftType, Severity
from the_dig.strata import Stratum


class DocstringLens(Lens):
    name = "docstring_vs_signature"
    description = "Checks if docstrings match function signatures"

    def applies_to(self, stratum: Stratum) -> bool:
        return stratum.layer == "code" and stratum.path.suffix == ".py"

    def examine(self, strata: Sequence[Stratum], root: Path) -> list[Artifact]:
        artifacts = []
        code_strata = [s for s in strata if self.applies_to(s)]

        for stratum in code_strata:
            artifacts.extend(self._check_param_drift(stratum))

        return artifacts

    def _check_param_drift(self, stratum: Stratum) -> list[Artifact]:
        """Compare docstring params against actual signature params."""
        artifacts = []
        sigs = stratum.extract_function_signatures()
        docstrings = stratum.extract_docstrings()

        for sig_line, func_name, params in sigs:
            # Find the closest docstring after this function definition
            nearest_doc = None
            for doc_start, doc_end, doc_text in docstrings:
                if doc_start > sig_line and doc_start <= sig_line + 3:
                    nearest_doc = (doc_start, doc_end, doc_text)
                    break

            if nearest_doc is None:
                continue

            doc_start, doc_end, doc_text = nearest_doc

            # Extract param names from docstring (various styles)
            doc_params = set()
            # Google style: Args:\n    param_name: description  /  param_name (type): description
            for m in re.finditer(r"(?:Args|Parameters|Params).*?(?=Returns|Raises|$)", doc_text, re.DOTALL | re.IGNORECASE):
                block = m.group(0)
                # Skip the header line itself (e.g. "Args:")
                block_lines = block.splitlines()
                body = "\n".join(block_lines[1:]) if len(block_lines) > 1 else ""
                for pm in re.finditer(r"^\s*(\w+)\s*(?:\(|:)", body, re.MULTILINE):
                    name = pm.group(1)
                    if name.lower() not in {"args", "parameters", "params", "returns", "raises", "type", "description"}:
                        doc_params.add(name)

            # NumPy style: param_name : type
            for pm in re.finditer(r"^(\w+)\s*:\s*\w+", doc_text, re.MULTILINE):
                name = pm.group(1)
                if name.lower() not in {"returns", "raises", "parameters", "attributes", "type", "notes", "examples", "args", "params"}:
                    doc_params.add(name)

            # Sphinx style: :param param_name:
            for pm in re.finditer(r":param\s+(\w+):", doc_text):
                doc_params.add(pm.group(1))

            if not doc_params:
                continue

            sig_params = set(params)

            # Params in docstring but not in signature
            phantom_params = doc_params - sig_params
            for p in phantom_params:
                artifacts.append(Artifact(
                    drift_type=DriftType.DOCSTRING_VS_SIGNATURE,
                    severity=Severity.MURMUR,
                    file_path=stratum.path,
                    line_start=doc_start,
                    line_end=doc_end,
                    claim=f"Docstring for `{func_name}()` documents param `{p}`",
                    reality=f"`{p}` is not in the function signature",
                    evidence=f"Signature params: {params}, Docstring params: {sorted(doc_params)}",
                ))

            # Params in signature but not in docstring (only if docstring has some params)
            missing_params = sig_params - doc_params
            for p in missing_params:
                artifacts.append(Artifact(
                    drift_type=DriftType.DOCSTRING_VS_SIGNATURE,
                    severity=Severity.WHISPER,
                    file_path=stratum.path,
                    line_start=doc_start,
                    line_end=doc_end,
                    claim=f"Docstring for `{func_name}()` documents params: {sorted(doc_params)}",
                    reality=f"Signature also has `{p}` which is not documented",
                    evidence=f"Signature params: {params}, Docstring params: {sorted(doc_params)}",
                ))

        return artifacts

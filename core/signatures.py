"""Static signature database used by the antivirus."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class Signature:
    """Simple representation of a signature."""

    identifier: str
    description: str
    sha256: Optional[str] = None
    filename_patterns: Optional[List[str]] = None


class SignatureDatabase:
    """In-memory signature database.

    The database can be extended by loading additional JSON files in future
    iterations.  For now, a small selection of educational signatures is
    provided to demonstrate how the scanning pipeline works.
    """

    def __init__(self) -> None:
        self._signatures: Dict[str, Signature] = {}
        for signature in self._default_signatures():
            self._signatures[signature.identifier] = signature

    @staticmethod
    def _default_signatures() -> Iterable[Signature]:
        return [
            Signature(
                identifier="demo-test-malware",
                description="Test signature that matches the EICAR demo hash",
                sha256=(
                    "275a021bbfb64843d0d600f1a114aa2b2c1b1b5f0985f07f"
                    "8b5b3b2010c56d4"
                ),
            ),
            Signature(
                identifier="suspicious-batch-naming",
                description="Matches batch files with names resembling installers",
                filename_patterns=["setup*.bat", "update*.bat"],
            ),
        ]

    def find_matches(
        self, *, sha256: Optional[str] = None, filename: Optional[str] = None
    ) -> List[Signature]:
        matches: List[Signature] = []
        for signature in self._signatures.values():
            if sha256 and signature.sha256 and sha256 == signature.sha256:
                matches.append(signature)
                continue
            if filename and signature.filename_patterns:
                for pattern in signature.filename_patterns:
                    if Path(filename).match(pattern):
                        matches.append(signature)
                        break
        return matches

    def add_signature(self, signature: Signature) -> None:
        self._signatures[signature.identifier] = signature

    def list_signatures(self) -> List[Signature]:
        return list(self._signatures.values())

"""Heuristic analysis utilities."""
from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

LOGGER = logging.getLogger(__name__)


@dataclass
class HeuristicResult:
    identifier: str
    description: str
    severity: str = "medium"


SUSPICIOUS_EXTENSIONS = {".exe", ".dll", ".bat", ".scr", ".js", ".vbs"}
LARGE_FILE_THRESHOLD = 50 * 1024 * 1024  # 50 MB


def analyse_file(path: Path) -> List[HeuristicResult]:
    results: List[HeuristicResult] = []
    extension = path.suffix.lower()
    if extension in SUSPICIOUS_EXTENSIONS:
        results.append(
            HeuristicResult(
                identifier="suspicious-extension",
                description=f"File extension {extension} often used by malware.",
            )
        )
    try:
        size = path.stat().st_size
        if size > LARGE_FILE_THRESHOLD and extension in {".exe", ".dll"}:
            results.append(
                HeuristicResult(
                    identifier="large-binary",
                    description=(
                        "Executable larger than 50 MB; consider verifying source"
                    ),
                    severity="low",
                )
            )
    except (FileNotFoundError, PermissionError) as exc:
        LOGGER.warning("Unable to inspect file %s: %s", path, exc)

    return results


def analyse_process(info: Dict[str, str]) -> List[HeuristicResult]:
    results: List[HeuristicResult] = []
    name = (info.get("name") or "").lower()
    path = (info.get("exe") or "").lower()

    if name.endswith(".tmp"):
        results.append(
            HeuristicResult(
                identifier="temp-process",
                description="Process name ends with .tmp which is unusual",
                severity="high",
            )
        )
    startup = info.get("startup")
    if startup:
        results.append(
            HeuristicResult(
                identifier="auto-start",
                description="Process configured to start automatically",
                severity="medium",
            )
        )
    if path and os.path.basename(path).startswith("~$"):
        results.append(
            HeuristicResult(
                identifier="tilde-prefixed",
                description="Executable path starts with ~$ which is suspicious",
                severity="medium",
            )
        )
    return results

"""Safe optimisation helpers."""
from __future__ import annotations

import logging
import os
import platform
import shutil
from pathlib import Path
from typing import Dict, List

LOGGER = logging.getLogger(__name__)


def get_temp_directories() -> List[Path]:
    system = platform.system().lower()
    candidates: List[Path] = []
    home = Path.home()
    if system == "windows":
        for name in ["TEMP", "TMP"]:
            temp = os.environ.get(name)
            if temp:
                candidates.append(Path(temp))
    else:
        candidates.append(Path("/tmp"))
    candidates.append(home / ".cache")
    return [path for path in candidates if path.exists()]


def estimate_cleanup(directories: List[Path]) -> Dict[str, int]:
    summary: Dict[str, int] = {}
    for directory in directories:
        total = 0
        for root, _, files in os.walk(directory):
            for name in files:
                try:
                    total += (Path(root) / name).stat().st_size
                except OSError:
                    continue
        summary[str(directory)] = total
    return summary


def cleanup(directories: List[Path], *, dry_run: bool = False) -> Dict[str, str]:
    results: Dict[str, str] = {}
    for directory in directories:
        if dry_run:
            results[str(directory)] = "simulated"
            continue
        try:
            for entry in directory.iterdir():
                if entry.is_dir():
                    shutil.rmtree(entry, ignore_errors=True)
                else:
                    try:
                        entry.unlink()
                    except FileNotFoundError:
                        continue
            results[str(directory)] = "success"
        except Exception as exc:
            LOGGER.warning("Failed to cleanup %s: %s", directory, exc)
            results[str(directory)] = f"failed: {exc}"
    return results

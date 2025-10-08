"""File system utilities for the intelligent antivirus project."""
from __future__ import annotations

import hashlib
import logging
import os
import platform
from pathlib import Path
from typing import Iterable, Iterator, List

LOGGER = logging.getLogger(__name__)

BLOCK_SIZE = 65536


def get_default_scan_paths() -> List[Path]:
    """Return a list of default directories to scan based on the OS."""

    system = platform.system().lower()
    home = Path.home()
    paths: List[Path] = []

    if system == "windows":
        paths.extend([
            home / "Downloads",
            home / "Documents",
            home / "Desktop",
            Path("C:/Program Files"),
            Path("C:/Program Files (x86)"),
        ])
    elif system == "darwin":
        paths.extend([
            home / "Downloads",
            home / "Documents",
            home / "Desktop",
            Path("/Applications"),
        ])
    else:  # assume Linux/Unix
        paths.extend([
            home / "Downloads",
            home / "Documents",
            home / "Desktop",
            Path("/usr/local/bin"),
            Path("/usr/bin"),
        ])

    return [path for path in paths if path.exists()]


def iter_files(paths: Iterable[Path], follow_symlinks: bool = False) -> Iterator[Path]:
    """Yield files within ``paths`` safely, handling permission errors."""

    for base in paths:
        base = Path(base)
        if not base.exists():
            LOGGER.debug("Scan path %s does not exist", base)
            continue

        if base.is_file():
            yield base
            continue

        for root, dirs, files in os.walk(base, followlinks=follow_symlinks):
            root_path = Path(root)
            for name in files:
                path = root_path / name
                try:
                    if path.is_file():
                        yield path
                except PermissionError:
                    LOGGER.warning("Permission denied reading %s", path)
            dirs[:] = [
                d
                for d in dirs
                if follow_symlinks or not (root_path / d).is_symlink()
            ]


def chunk_reader(path: Path, block_size: int = BLOCK_SIZE) -> Iterator[bytes]:
    """Yield chunks of bytes from ``path``."""

    with path.open("rb") as handle:
        while True:
            data = handle.read(block_size)
            if not data:
                break
            yield data


def compute_sha256(path: Path, block_size: int = BLOCK_SIZE) -> str:
    """Compute the SHA-256 hash for ``path`` in a streaming fashion."""

    digest = hashlib.sha256()
    for chunk in chunk_reader(path, block_size=block_size):
        digest.update(chunk)
    return digest.hexdigest()


def safe_relative_path(path: Path, base: Path) -> Path:
    """Return ``path`` relative to ``base`` without escaping the root."""

    try:
        return path.relative_to(base)
    except ValueError:
        return path


def group_paths_by_size(paths: Iterable[Path]) -> dict[int, List[Path]]:
    """Group paths by file size to optimise duplicate detection."""

    size_map: dict[int, List[Path]] = {}
    for path in paths:
        try:
            size = path.stat().st_size
        except (OSError, PermissionError) as exc:
            LOGGER.warning("Unable to stat %s: %s", path, exc)
            continue
        size_map.setdefault(size, []).append(path)
    return size_map

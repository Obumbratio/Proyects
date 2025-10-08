"""Duplicate file detection utilities."""
from __future__ import annotations

import logging
from collections import defaultdict
from pathlib import Path
from typing import Dict, Iterable, List

from .files import compute_sha256, group_paths_by_size

LOGGER = logging.getLogger(__name__)


def find_duplicates(
    paths: Iterable[Path], *, block_size: int
) -> Dict[str, List[Path]]:
    """Return mapping of SHA-256 hash to duplicate paths."""

    size_map = group_paths_by_size(paths)
    duplicates: Dict[str, List[Path]] = defaultdict(list)
    for size, candidates in size_map.items():
        if len(candidates) < 2:
            continue
        LOGGER.debug("Analysing %d candidates of size %d", len(candidates), size)
        for path in candidates:
            try:
                digest = compute_sha256(path, block_size=block_size)
            except (OSError, PermissionError) as exc:
                LOGGER.warning("Unable to hash %s: %s", path, exc)
                continue
            duplicates[digest].append(path)

    return {digest: items for digest, items in duplicates.items() if len(items) > 1}

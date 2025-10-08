"""Configuration loading utilities for the intelligent antivirus project.

This module is intentionally light-weight and only relies on the Python
standard library to avoid introducing unnecessary dependencies.  The
configuration file is stored in JSON for ease of editing while remaining
portable across the three supported platforms.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict

LOGGER = logging.getLogger(__name__)

DEFAULT_CONFIG_PATHS = (
    Path("config/default_config.json"),
    Path.home() / ".intelligent_antivirus" / "config.json",
)


def load_config(custom_path: str | None = None) -> Dict[str, Any]:
    """Load configuration from JSON files.

    Parameters
    ----------
    custom_path:
        Optional custom path supplied by the user.  When provided the file must
        exist; otherwise, :class:`FileNotFoundError` is raised to make the
        failure explicit.
    """

    candidates = []
    if custom_path:
        candidates.append(Path(custom_path).expanduser())
    candidates.extend(DEFAULT_CONFIG_PATHS)

    for path in candidates:
        try:
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            LOGGER.debug("Loaded configuration from %s", path)
            return data
        except FileNotFoundError:
            LOGGER.debug("Configuration file %s not found", path)
            continue
        except json.JSONDecodeError as exc:
            LOGGER.error("Invalid JSON in configuration file %s: %s", path, exc)
            raise

    LOGGER.warning("No configuration file found; using built-in defaults")
    return DEFAULTS.copy()


DEFAULTS: Dict[str, Any] = {
    "logging": {
        "directory": "logs",
        "filename": "antivirus.log",
        "max_bytes": 1_048_576,
        "backup_count": 5,
    },
    "scanning": {
        "max_workers": 2,
        "block_size": 65536,
        "follow_symlinks": False,
        "allow_network_paths": False,
    },
    "reports": {
        "directory": "reports",
        "format": "json",
    },
    "remediation": {
        "quarantine_dir": "quarantine",
        "require_confirmation": True,
    },
    "ui": {
        "progress_bar_width": 40,
    },
}

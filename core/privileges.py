"""Privilege detection utilities."""
from __future__ import annotations

import ctypes
import os
import platform


def is_admin() -> bool:
    system = platform.system().lower()
    if system == "windows":
        try:
            return bool(ctypes.windll.shell32.IsUserAnAdmin())  # type: ignore[attr-defined]
        except AttributeError:
            return False
    if system in {"linux", "darwin"}:
        return os.geteuid() == 0  # type: ignore[attr-defined]
    return False


def require_elevation_prompt() -> str:
    return (
        "Advertencia: esta acción requiere privilegios de administrador. "
        "¿Conceder permiso? (S/N)"
    )

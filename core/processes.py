"""Process inspection utilities."""
from __future__ import annotations

import logging
import platform
import subprocess
import csv
from dataclasses import dataclass
from typing import Iterator, List, Optional

try:
    import psutil  # type: ignore
except Exception:  # pragma: no cover - psutil may be unavailable
    psutil = None

LOGGER = logging.getLogger(__name__)


@dataclass
class ProcessInfo:
    pid: int
    name: str
    exe: str | None
    username: str | None
    connections: List[str]
    startup: bool = False


def iter_processes() -> Iterator[ProcessInfo]:
    if psutil:
        for proc in psutil.process_iter(attrs=["pid", "name", "exe", "username"]):
            try:
                conns = proc.connections(kind="inet")
                connections = [
                    f"{conn.laddr.ip}:{conn.laddr.port}"
                    for conn in conns
                    if conn.laddr
                ]
            except Exception:  # pragma: no cover - psutil specifics
                connections = []
            yield ProcessInfo(
                pid=proc.info.get("pid", 0),
                name=proc.info.get("name") or "unknown",
                exe=proc.info.get("exe"),
                username=proc.info.get("username"),
                connections=connections,
                startup=is_in_startup(proc.info.get("exe")),
            )
        return

    # Fallback using ps command
    system = platform.system().lower()
    if system in {"linux", "darwin"}:
        try:
            output = subprocess.check_output(["ps", "-eo", "pid,comm"], text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            LOGGER.warning("Unable to enumerate processes via ps: %s", exc)
            return
        for line in output.splitlines()[1:]:
            parts = line.strip().split(maxsplit=1)
            if not parts:
                continue
            pid = int(parts[0])
            name = parts[1] if len(parts) > 1 else "unknown"
            yield ProcessInfo(pid=pid, name=name, exe=None, username=None, connections=[])
    else:
        # Windows fallback using tasklist
        try:
            output = subprocess.check_output(["tasklist", "/fo", "csv"], text=True)
        except (subprocess.CalledProcessError, FileNotFoundError) as exc:
            LOGGER.warning("Unable to enumerate processes via tasklist: %s", exc)
            return
        reader = csv.reader(output.splitlines())
        next(reader, None)  # skip header
        for row in reader:
            if len(row) < 2:
                continue
            try:
                pid = int(row[1])
            except ValueError:
                continue
            name = row[0]
            yield ProcessInfo(pid=pid, name=name, exe=None, username=None, connections=[])


STARTUP_PATHS = [
    "~/Library/LaunchAgents",
    "~/Library/LaunchDaemons",
    "~/Library/StartupItems",
    "~/AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup",
    "/etc/xdg/autostart",
    "~/.config/autostart",
]


def is_in_startup(executable: Optional[str]) -> bool:
    if not executable:
        return False
    exe_path = str(executable).lower()
    for entry in STARTUP_PATHS:
        if entry and entry.lower().replace("\\", "/") in exe_path.replace("\\", "/"):
            return True
    return False

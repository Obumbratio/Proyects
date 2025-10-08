"""Remediation utilities."""
"""Remediation utilities for the antivirus project."""
from __future__ import annotations

import logging
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import List

from .privileges import is_admin

LOGGER = logging.getLogger(__name__)


@dataclass
class RemediationAction:
    action: str
    target: Path
    status: str
    details: str


class Remediator:
    def __init__(self, quarantine_dir: Path, *, dry_run: bool = False) -> None:
        self.quarantine_dir = quarantine_dir
        self.quarantine_dir.mkdir(parents=True, exist_ok=True)
        self.dry_run = dry_run
        self.log: List[RemediationAction] = []

    def quarantine(self, path: Path) -> None:
        if not path.exists():
            self.log.append(
                RemediationAction(
                    action="quarantine",
                    target=path,
                    status="failed",
                    details="El archivo no existe",
                )
            )
            return
        destination = self.quarantine_dir / path.name
        if destination.exists():
            try:
                timestamp = int(path.stat().st_mtime)
            except OSError:
                timestamp = 0
            destination = self.quarantine_dir / f"{path.stem}_{timestamp}{path.suffix}"
        if self.dry_run:
            self.log.append(
                RemediationAction(
                    action="quarantine",
                    target=path,
                    status="simulated",
                    details=f"Would move to {destination}",
                )
            )
            return
        try:
            shutil.move(str(path), destination)
            self.log.append(
                RemediationAction(
                    action="quarantine",
                    target=path,
                    status="success",
                    details=f"Moved to {destination}",
                )
            )
        except Exception as exc:
            self.log.append(
                RemediationAction(
                    action="quarantine",
                    target=path,
                    status="failed",
                    details=str(exc),
                )
            )

    def delete(self, path: Path) -> None:
        if not path.exists():
            self.log.append(
                RemediationAction(
                    action="delete",
                    target=path,
                    status="failed",
                    details="El elemento no existe",
                )
            )
            return
        if self.dry_run:
            self.log.append(
                RemediationAction(
                    action="delete",
                    target=path,
                    status="simulated",
                    details="Would delete permanently",
                )
            )
            return
        try:
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
            self.log.append(
                RemediationAction(
                    action="delete",
                    target=path,
                    status="success",
                    details="Removed permanently",
                )
            )
        except Exception as exc:
            self.log.append(
                RemediationAction(
                    action="delete",
                    target=path,
                    status="failed",
                    details=str(exc),
                )
            )

    def restore(self, filename: str, destination: Path) -> None:
        source = self.quarantine_dir / filename
        if not source.exists():
            self.log.append(
                RemediationAction(
                    action="restore",
                    target=destination,
                    status="failed",
                    details="File not present in quarantine",
                )
            )
            return
        if self.dry_run:
            self.log.append(
                RemediationAction(
                    action="restore",
                    target=destination,
                    status="simulated",
                    details=f"Would restore {source} to {destination}",
                )
            )
            return
        try:
            shutil.move(str(source), destination)
            self.log.append(
                RemediationAction(
                    action="restore",
                    target=destination,
                    status="success",
                    details=f"Restored from {source}",
                )
            )
        except Exception as exc:
            self.log.append(
                RemediationAction(
                    action="restore",
                    target=destination,
                    status="failed",
                    details=str(exc),
                )
            )

    def requires_admin(self) -> bool:
        return not is_admin()

    def get_log(self) -> List[RemediationAction]:
        return self.log

    def clear_log(self) -> None:
        self.log.clear()

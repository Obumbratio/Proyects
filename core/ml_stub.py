"""Placeholder module for future machine learning integrations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List


@dataclass
class MLDetection:
    label: str
    confidence: float
    explanation: str


class MLDetector:
    """Stub implementation that returns no detections.

    The class exposes a minimal API for integration tests and for future work
    without performing any real machine learning operations today.
    """

    def __init__(self, enabled: bool = False) -> None:
        self.enabled = enabled

    def analyse_files(self, paths: Iterable[str]) -> List[MLDetection]:
        if not self.enabled:
            return []
        return []

    def analyse_processes(self, pids: Iterable[int]) -> List[MLDetection]:
        if not self.enabled:
            return []
        return []

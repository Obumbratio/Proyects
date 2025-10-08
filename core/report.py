"""Reporting utilities for the antivirus."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

LOGGER = logging.getLogger(__name__)


@dataclass
class ReportItem:
    title: str
    details: Dict[str, Any]
    risk: str
    recommendations: List[str] = field(default_factory=list)


@dataclass
class ScanReport:
    name: str
    started_at: datetime
    finished_at: datetime | None = None
    summary: Dict[str, Any] = field(default_factory=dict)
    findings: List[ReportItem] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "summary": self.summary,
            "findings": [
                {
                    "title": item.title,
                    "details": item.details,
                    "risk": item.risk,
                    "recommendations": item.recommendations,
                }
                for item in self.findings
            ],
            "limitations": self.limitations,
        }

    def add_finding(self, item: ReportItem) -> None:
        self.findings.append(item)

    def add_limitation(self, message: str) -> None:
        self.limitations.append(message)


class ReportWriter:
    """Persist reports to disk."""

    def __init__(self, directory: Path) -> None:
        self.directory = directory
        self.directory.mkdir(parents=True, exist_ok=True)
        self.last_path: Path | None = None

    def write(self, report: ScanReport, *, to_json: bool = True) -> Path:
        timestamp = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        filename = f"{timestamp}_{report.name.replace(' ', '_').lower()}"
        path = self.directory / (filename + (".json" if to_json else ".txt"))
        if to_json:
            with path.open("w", encoding="utf-8") as handle:
                json.dump(report.to_dict(), handle, indent=2)
        else:
            with path.open("w", encoding="utf-8") as handle:
                handle.write(self.to_text(report))
        LOGGER.info("Report written to %s", path)
        self.last_path = path
        return path

    @staticmethod
    def to_text(report: ScanReport) -> str:
        lines = [
            f"Report: {report.name}",
            f"Started: {report.started_at.isoformat()}",
            f"Finished: {(report.finished_at.isoformat() if report.finished_at else 'incomplete')}",
            "Summary:",
        ]
        for key, value in report.summary.items():
            lines.append(f"  - {key}: {value}")
        if report.findings:
            lines.append("Findings:")
            for item in report.findings:
                lines.append(f"* {item.title} (risk: {item.risk})")
                for rec in item.recommendations:
                    lines.append(f"    Recommendation: {rec}")
                for key, value in item.details.items():
                    lines.append(f"    {key}: {value}")
        if report.limitations:
            lines.append("Limitations:")
            for note in report.limitations:
                lines.append(f"  - {note}")
        return "\n".join(lines)


class ReportAggregator:
    """Aggregate multiple reports into a master report."""

    def __init__(self, name: str) -> None:
        self.master = ScanReport(name=name, started_at=datetime.utcnow())

    def add_report(self, report: ScanReport) -> None:
        self.master.summary.setdefault("included_reports", []).append(report.name)
        self.master.summary.setdefault("total_findings", 0)
        self.master.summary["total_findings"] += len(report.findings)
        self.master.findings.extend(report.findings)
        self.master.limitations.extend(report.limitations)

    def build(self) -> ScanReport:
        self.master.finished_at = datetime.utcnow()
        return self.master

"""High level scanning orchestration."""
from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from . import heuristics
from .dupes import find_duplicates
from .files import compute_sha256, get_default_scan_paths, iter_files
from .gpu import GPUInspector
from .ml_stub import MLDetector
from .processes import iter_processes
from .report import ReportItem, ReportWriter, ScanReport
from .signatures import SignatureDatabase

LOGGER = logging.getLogger(__name__)


class AntivirusScanner:
    def __init__(
        self,
        *,
        config: Dict,
        report_writer: ReportWriter,
        signature_db: Optional[SignatureDatabase] = None,
        dry_run: bool = False,
    ) -> None:
        self.config = config
        self.report_writer = report_writer
        self.signature_db = signature_db or SignatureDatabase()
        self.dry_run = dry_run
        self.ml_detector = MLDetector(enabled=False)
        self._write_json = (
            str(self.config.get("reports", {}).get("format", "json")).lower()
            == "json"
        )

    # ------------------------------------------------------------------
    # File scanning

    def scan_files(self, paths: Optional[List[Path]] = None) -> ScanReport:
        paths = paths or get_default_scan_paths()
        report = ScanReport(name="escaneo_archivos", started_at=datetime.utcnow())
        block_size = int(self.config.get("scanning", {}).get("block_size", 65536))
        follow_symlinks = bool(
            self.config.get("scanning", {}).get("follow_symlinks", False)
        )

        scanned = 0
        for path in iter_files(paths, follow_symlinks=follow_symlinks):
            scanned += 1
            hash_value = None
            matches = []
            try:
                hash_value = compute_sha256(path, block_size=block_size)
                matches = self.signature_db.find_matches(
                    sha256=hash_value, filename=path.name
                )
            except (OSError, PermissionError) as exc:
                LOGGER.warning("Unable to hash %s: %s", path, exc)
                report.add_limitation(f"No se pudo leer {path}: {exc}")
                continue
            heuristics_results = heuristics.analyse_file(path)
            if matches or heuristics_results:
                item_details = {
                    "ruta": str(path),
                    "hash_sha256": hash_value,
                    "firmas": [sig.identifier for sig in matches],
                    "heuristicas": [res.identifier for res in heuristics_results],
                }
                report.add_finding(
                    ReportItem(
                        title=f"Archivo sospechoso: {path.name}",
                        details=item_details,
                        risk="high" if matches else "medium",
                        recommendations=[
                            "Enviar a cuarentena",
                            "Eliminar solo tras verificación manual",
                        ],
                    )
                )

        report.summary = {
            "archivos_escaneados": scanned,
            "sospechosos": len(report.findings),
        }
        report.finished_at = datetime.utcnow()
        self.report_writer.write(report, to_json=self._write_json)
        return report

    # ------------------------------------------------------------------
    # Process scanning

    def scan_processes(self) -> ScanReport:
        report = ScanReport(name="escaneo_procesos", started_at=datetime.utcnow())
        processes = list(iter_processes())
        for process in processes:
            matches = self.signature_db.find_matches(filename=process.name)
            heuristics_results = heuristics.analyse_process(
                {
                    "name": process.name,
                    "exe": process.exe or "",
                    "startup": process.startup,
                }
            )
            if matches or heuristics_results:
                report.add_finding(
                    ReportItem(
                        title=f"Proceso sospechoso: {process.name}",
                        details={
                            "pid": process.pid,
                            "exe": process.exe,
                            "conexiones": process.connections,
                            "firmas": [sig.identifier for sig in matches],
                            "heuristicas": [res.identifier for res in heuristics_results],
                        },
                        risk="high" if matches else "medium",
                        recommendations=[
                            "Revisar manualmente",
                            "Finalizar proceso si se confirma malicioso",
                        ],
                    )
                )
        report.summary = {
            "procesos_escaneados": len(processes),
            "sospechosos": len(report.findings),
        }
        report.finished_at = datetime.utcnow()
        self.report_writer.write(report, to_json=self._write_json)
        return report

    # ------------------------------------------------------------------
    # GPU scanning

    def scan_gpu_processes(self) -> ScanReport:
        report = ScanReport(name="escaneo_gpu", started_at=datetime.utcnow())
        inspector = GPUInspector()
        gpu_processes = inspector.inspect()
        if not gpu_processes:
            report.add_limitation(
                "No se encontraron procesos GPU o la función no está disponible"
            )
        else:
            for proc in gpu_processes:
                matches = self.signature_db.find_matches(filename=proc.name)
                if matches:
                    report.add_finding(
                        ReportItem(
                            title=f"Proceso GPU sospechoso: {proc.name}",
                            details={
                                "pid": proc.pid,
                                "memoria_gpu_mb": proc.gpu_memory_mb,
                                "firmas": [sig.identifier for sig in matches],
                            },
                            risk="high",
                            recommendations=[
                                "Verificar origen del proceso",
                                "Finalizar solo tras confirmación",
                            ],
                        )
                    )
        report.summary = {
            "procesos_gpu_detectados": len(gpu_processes),
            "sospechosos": len(report.findings),
        }
        report.finished_at = datetime.utcnow()
        self.report_writer.write(report, to_json=self._write_json)
        return report

    # ------------------------------------------------------------------
    # Duplicate scanning

    def scan_duplicates(self, paths: Optional[List[Path]] = None) -> ScanReport:
        paths = paths or get_default_scan_paths()
        report = ScanReport(name="busqueda_duplicados", started_at=datetime.utcnow())
        block_size = int(self.config.get("scanning", {}).get("block_size", 65536))
        follow_symlinks = bool(
            self.config.get("scanning", {}).get("follow_symlinks", False)
        )
        all_files = list(iter_files(paths, follow_symlinks=follow_symlinks))
        duplicates = find_duplicates(all_files, block_size=block_size)
        total_space = 0
        for digest, items in duplicates.items():
            size = items[0].stat().st_size if items else 0
            total_space += size * (len(items) - 1)
            report.add_finding(
                ReportItem(
                    title=f"Duplicados hash {digest[:8]}",
                    details={"archivos": [str(item) for item in items], "tamano": size},
                    risk="low",
                    recommendations=[
                        "Considerar eliminar duplicados tras revisión",
                    ],
                )
            )
        report.summary = {
            "grupos": len(duplicates),
            "espacio_recuperable": total_space,
        }
        report.finished_at = datetime.utcnow()
        self.report_writer.write(report, to_json=self._write_json)
        return report

    # ------------------------------------------------------------------
    # Full scan orchestration

    def full_scan(self) -> ScanReport:
        report = ScanReport(name="escaneo_completo", started_at=datetime.utcnow())
        sub_reports = [
            self.scan_files(),
            self.scan_processes(),
            self.scan_gpu_processes(),
            self.scan_duplicates(),
        ]
        findings = sum(len(sub.findings) for sub in sub_reports)
        report.summary = {
            "reportes_incluidos": [sub.name for sub in sub_reports],
            "hallazgos_totales": findings,
        }
        for sub in sub_reports:
            report.findings.extend(sub.findings)
            report.limitations.extend(sub.limitations)
        report.finished_at = datetime.utcnow()
        self.report_writer.write(report, to_json=self._write_json)
        return report

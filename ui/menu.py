"""Console UI for the intelligent antivirus."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict

from core.optimize import cleanup, estimate_cleanup, get_temp_directories
from core.privileges import require_elevation_prompt
from core.remediation import Remediator
from core.report import ScanReport
from core.scanner import AntivirusScanner

LOGGER = logging.getLogger(__name__)


class ConsoleMenu:
    def __init__(
        self,
        scanner: AntivirusScanner,
        remediator: Remediator,
        config: Dict,
        *,
        dry_run: bool = False,
    ) -> None:
        self.scanner = scanner
        self.remediator = remediator
        self.config = config
        self.dry_run = dry_run

    def run(self) -> None:
        while True:
            print("\n=== Antivirus Inteligente ===")
            print("1. Escaneo completo")
            print("2. Escaneo de archivos")
            print("3. Escaneo de procesos")
            print("4. Escaneo de procesos GPU")
            print("5. Buscar duplicados")
            print("6. Ver reportes")
            print("7. Salir")
            choice = input("Seleccione una opción: ").strip()

            if choice == "1":
                report = self.scanner.full_scan()
                self._handle_post_scan(report)
            elif choice == "2":
                report = self.scanner.scan_files()
                self._handle_post_scan(report)
            elif choice == "3":
                report = self.scanner.scan_processes()
                self._handle_post_scan(report)
            elif choice == "4":
                report = self.scanner.scan_gpu_processes()
                self._handle_post_scan(report)
            elif choice == "5":
                report = self.scanner.scan_duplicates()
                self._handle_post_scan(report)
            elif choice == "6":
                self._view_reports()
            elif choice == "7":
                print("¡Hasta luego!")
                break
            else:
                print("Opción no válida. Intente nuevamente.")

    # ------------------------------------------------------------------
    def _handle_post_scan(self, report: ScanReport) -> None:
        print("\nResumen del reporte:")
        for key, value in report.summary.items():
            print(f"  - {key}: {value}")
        if report.limitations:
            print("Limitaciones:")
            for note in report.limitations:
                print(f"  - {note}")
        if not report.findings:
            print("No se encontraron hallazgos sospechosos.")
            return

        while True:
            print("\nAcciones disponibles:")
            print("1) Eliminar/Enviar a cuarentena")
            print("2) Finalizar procesos sospechosos")
            print("3) Limpiar caché")
            print("4) Optimizar el sistema")
            print("5) Salir")
            action = input("Seleccione una acción: ").strip()
            if action == "1":
                self._handle_file_remediation(report)
            elif action == "2":
                print(
                    "Finalizar procesos debe hacerse manualmente tras confirmación."
                )
            elif action == "3":
                self._clean_cache()
            elif action == "4":
                self._optimize_system()
            elif action == "5":
                break
            else:
                print("Opción no válida.")

        self._print_remediation_log()

    def _handle_file_remediation(self, report: ScanReport) -> None:
        if self.remediator.requires_admin():
            response = input(require_elevation_prompt() + " ").strip().lower()
            if response != "s":
                print("Operación cancelada.")
                return

        for finding in report.findings:
            path_value = finding.details.get("ruta")
            if path_value:
                path = Path(path_value)
                decision = self._confirm_action(
                    f"¿Enviar {path} a cuarentena? (S/N) "
                )
                if decision:
                    self.remediator.quarantine(path)
                else:
                    decision_delete = self._confirm_action(
                        f"¿Eliminar permanentemente {path}? (S/N) "
                    )
                    if decision_delete:
                        self.remediator.delete(path)
            duplicates = finding.details.get("archivos")
            if duplicates:
                for duplicate_path in duplicates[1:]:
                    path = Path(duplicate_path)
                    decision = self._confirm_action(
                        f"¿Mover duplicado {path} a cuarentena? (S/N) "
                    )
                    if decision:
                        self.remediator.quarantine(path)

    def _confirm_action(self, prompt: str) -> bool:
        response = input(prompt).strip().lower()
        return response == "s"

    def _print_remediation_log(self) -> None:
        if not self.remediator.get_log():
            return
        print("\nReporte post-acción:")
        for entry in self.remediator.get_log():
            print(
                f"- {entry.action} -> {entry.target} ({entry.status}) :: {entry.details}"
            )
        self.remediator.clear_log()

    def _clean_cache(self) -> None:
        directories = get_temp_directories()
        if not directories:
            print("No se detectaron cachés para limpiar.")
            return
        estimation = estimate_cleanup(directories)
        print("Directorio -> bytes estimados a liberar:")
        for directory, size in estimation.items():
            print(f"- {directory}: {size}")
        confirm = self._confirm_action("¿Proceder con la limpieza segura? (S/N) ")
        if not confirm:
            print("Limpieza cancelada.")
            return
        results = cleanup(directories, dry_run=self.dry_run)
        for directory, status in results.items():
            print(f"{directory}: {status}")

    def _optimize_system(self) -> None:
        print("Recomendaciones de optimización segura:")
        recommendations = [
            "Revise programas de inicio y desactive los innecesarios.",
            "Mantenga el sistema operativo actualizado.",
            "Realice copias de seguridad periódicas de sus datos.",
            "Considere desinstalar aplicaciones que ya no utilice.",
        ]
        for item in recommendations:
            print(f"- {item}")

    def _view_reports(self) -> None:
        report_dir = Path(self.config.get("reports", {}).get("directory", "reports"))
        if not report_dir.exists():
            print("No hay reportes disponibles aún.")
            return
        files = sorted(report_dir.glob("*.json"), reverse=True)
        if not files:
            print("No hay reportes almacenados.")
            return
        for idx, path in enumerate(files[:10], start=1):
            print(f"{idx}. {path.name}")
        choice = input(
            "Seleccione un reporte para ver (número) o presione Enter para salir: "
        ).strip()
        if not choice:
            return
        try:
            index = int(choice) - 1
        except ValueError:
            print("Selección inválida.")
            return
        if index < 0 or index >= len(files):
            print("Selección fuera de rango.")
            return
        path = files[index]
        with path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        print(json.dumps(data, indent=2, ensure_ascii=False))

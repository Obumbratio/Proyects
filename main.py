"""Entry point for the intelligent antivirus CLI."""
from __future__ import annotations

import argparse
import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import List, Optional

from core.config import load_config
from core.optimize import cleanup, estimate_cleanup, get_temp_directories
from core.remediation import Remediator
from core.report import ReportWriter, ScanReport
from core.scanner import AntivirusScanner
from ui.menu import ConsoleMenu


def setup_logging(config: dict) -> None:
    log_cfg = config.get("logging", {})
    directory = Path(log_cfg.get("directory", "logs"))
    directory.mkdir(parents=True, exist_ok=True)
    logfile = directory / log_cfg.get("filename", "antivirus.log")
    handler = RotatingFileHandler(
        logfile,
        maxBytes=int(log_cfg.get("max_bytes", 1_048_576)),
        backupCount=int(log_cfg.get("backup_count", 5)),
        encoding="utf-8",
    )
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    root = logging.getLogger()
    root.setLevel(logging.INFO)
    root.addHandler(handler)
    console = logging.StreamHandler()
    console.setFormatter(formatter)
    root.addHandler(console)


def create_scanner(config: dict, *, dry_run: bool) -> AntivirusScanner:
    report_dir = Path(config.get("reports", {}).get("directory", "reports"))
    writer = ReportWriter(report_dir)
    scanner = AntivirusScanner(config=config, report_writer=writer, dry_run=dry_run)
    return scanner


def create_remediator(config: dict, *, dry_run: bool) -> Remediator:
    quarantine_dir = Path(
        config.get("remediation", {}).get("quarantine_dir", "quarantine")
    )
    return Remediator(quarantine_dir, dry_run=dry_run)


def print_report_summary(report: ScanReport, writer: ReportWriter) -> None:
    print(json.dumps(report.to_dict(), indent=2, ensure_ascii=False))
    if writer.last_path:
        print(f"Reporte guardado en: {writer.last_path}")


def format_report_text(data: dict) -> str:
    lines = [
        f"Reporte: {data.get('name', 'desconocido')}",
        f"Inicio: {data.get('started_at', 'N/D')}",
        f"Fin: {data.get('finished_at', 'N/D')}",
        "Resumen:",
    ]
    summary = data.get("summary", {})
    for key, value in summary.items():
        lines.append(f"  - {key}: {value}")
    findings = data.get("findings", [])
    if findings:
        lines.append("Hallazgos:")
        for item in findings:
            lines.append(f"* {item.get('title', 'Sin título')} (riesgo: {item.get('risk', 'N/D')})")
            for key, value in item.get("details", {}).items():
                lines.append(f"    {key}: {value}")
            for rec in item.get("recommendations", []):
                lines.append(f"    Recomendación: {rec}")
    limitations = data.get("limitations", [])
    if limitations:
        lines.append("Limitaciones:")
        for note in limitations:
            lines.append(f"  - {note}")
    return "\n".join(lines)


def handle_reports_command(args: argparse.Namespace, config: dict) -> None:
    report_dir = Path(config.get("reports", {}).get("directory", "reports"))
    if not report_dir.exists():
        print("No se encontraron reportes.")
        return
    files = sorted(report_dir.glob("*.json"), reverse=True)
    if not files:
        print("No se encontraron reportes.")
        return
    if args.last:
        target = files[0]
    else:
        for idx, path in enumerate(files, start=1):
            print(f"{idx}. {path.name}")
        choice = input("Seleccione el número del reporte a abrir: ").strip()
        try:
            index = int(choice) - 1
            target = files[index]
        except (ValueError, IndexError):
            print("Selección inválida.")
            return
    with target.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if args.format == "text":
        print(format_report_text(data))
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))


def remediate_from_report(path: Path, remediator: Remediator) -> None:
    if not path.exists():
        print(f"El reporte {path} no existe.")
        return
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    findings = data.get("findings", [])
    if not findings:
        print("No hay elementos para remediar en este reporte.")
        return
    if remediator.requires_admin():
        from core.privileges import require_elevation_prompt

        response = input(require_elevation_prompt() + " ").strip().lower()
        if response != "s":
            print("Operación cancelada.")
            return
    for finding in findings:
        details = finding.get("details", {})
        ruta = details.get("ruta")
        if ruta:
            decision = input(f"¿Enviar {ruta} a cuarentena? (S/N) ").strip().lower()
            if decision == "s":
                remediator.quarantine(Path(ruta))
            else:
                decision_del = input(
                    f"¿Eliminar permanentemente {ruta}? (S/N) "
                ).strip().lower()
                if decision_del == "s":
                    remediator.delete(Path(ruta))
        duplicates = details.get("archivos")
        if duplicates:
            for duplicate in duplicates[1:]:
                decision = input(
                    f"¿Mover duplicado {duplicate} a cuarentena? (S/N) "
                ).strip().lower()
                if decision == "s":
                    remediator.quarantine(Path(duplicate))
    for entry in remediator.get_log():
        print(
            f"- {entry.action} -> {entry.target} ({entry.status}) :: {entry.details}"
        )
    remediator.clear_log()


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Antivirus inteligente")
    parser.add_argument("--config", help="Ruta a archivo de configuración", default=None)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Ejecuta las operaciones en modo simulación",
    )
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("full-scan", help="Ejecuta escaneo completo")

    files_parser = subparsers.add_parser("scan-files", help="Escanea archivos")
    files_parser.add_argument(
        "--path",
        action="append",
        help="Ruta adicional para escanear",
    )

    subparsers.add_parser("scan-processes", help="Escanea procesos")
    subparsers.add_parser("scan-gpu", help="Escanea procesos GPU")

    dupes_parser = subparsers.add_parser("find-dupes", help="Busca duplicados")
    dupes_parser.add_argument(
        "--paths",
        nargs="+",
        help="Rutas a incluir en la búsqueda de duplicados",
    )

    reports_parser = subparsers.add_parser("reports", help="Gestiona reportes")
    reports_parser.add_argument("--last", action="store_true", help="Abre el último reporte")
    reports_parser.add_argument(
        "--format",
        choices=["json", "text"],
        default="json",
        help="Formato de salida",
    )

    remediate_parser = subparsers.add_parser("remediate", help="Remediar desde reporte")
    remediate_parser.add_argument(
        "--from-report",
        required=True,
        help="Ruta al reporte JSON",
    )

    subparsers.add_parser("optimize", help="Limpia cachés y aplica optimizaciones seguras")

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> None:
    args = parse_args(argv)
    config = load_config(args.config)
    setup_logging(config)
    scanner = create_scanner(config, dry_run=args.dry_run)
    remediator = create_remediator(config, dry_run=args.dry_run)

    if not args.command:
        menu = ConsoleMenu(scanner, remediator, config, dry_run=args.dry_run)
        menu.run()
        return

    if args.command == "full-scan":
        report = scanner.full_scan()
        print_report_summary(report, scanner.report_writer)
    elif args.command == "scan-files":
        paths = [Path(p) for p in args.path] if args.path else None
        report = scanner.scan_files(paths)
        print_report_summary(report, scanner.report_writer)
    elif args.command == "scan-processes":
        report = scanner.scan_processes()
        print_report_summary(report, scanner.report_writer)
    elif args.command == "scan-gpu":
        report = scanner.scan_gpu_processes()
        print_report_summary(report, scanner.report_writer)
    elif args.command == "find-dupes":
        paths = [Path(p) for p in args.paths] if args.paths else None
        report = scanner.scan_duplicates(paths)
        print_report_summary(report, scanner.report_writer)
    elif args.command == "reports":
        handle_reports_command(args, config)
    elif args.command == "remediate":
        remediate_from_report(Path(args.from_report), remediator)
    elif args.command == "optimize":
        directories = get_temp_directories()
        if not directories:
            print("No se encontraron directorios temporales para limpiar.")
            return
        estimation = estimate_cleanup(directories)
        print("Resumen de cachés detectadas:")
        for directory, size in estimation.items():
            print(f"- {directory}: {size} bytes")
        if args.dry_run:
            proceed = input("Modo simulación activo. ¿Mostrar acciones simuladas? (S/N) ").strip().lower()
            if proceed != "s":
                return
        confirm = input("¿Desea limpiar estas rutas? (S/N) ").strip().lower()
        if confirm != "s":
            print("Operación cancelada.")
            return
        results = cleanup(directories, dry_run=args.dry_run)
        for directory, status in results.items():
            print(f"- {directory}: {status}")
    else:
        raise SystemExit(f"Comando desconocido: {args.command}")


if __name__ == "__main__":  # pragma: no cover
    main()

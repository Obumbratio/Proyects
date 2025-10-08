import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path

from core.report import ReportItem, ReportWriter, ScanReport


class TestReport(unittest.TestCase):
    def test_report_writer_creates_json(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            directory = Path(tmp)
            writer = ReportWriter(directory)
            report = ScanReport(name="prueba", started_at=datetime.utcnow())
            report.summary = {"encontrados": 1}
            report.add_finding(
                ReportItem(
                    title="Elemento", details={"ruta": "test"}, risk="medium"
                )
            )
            path = writer.write(report, to_json=True)
            self.assertTrue(path.exists())
            data = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(data["name"], "prueba")
            self.assertEqual(data["summary"]["encontrados"], 1)


if __name__ == "__main__":
    unittest.main()

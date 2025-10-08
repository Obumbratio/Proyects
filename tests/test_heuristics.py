import tempfile
from pathlib import Path
import unittest

from core import heuristics


class TestHeuristics(unittest.TestCase):
    def test_detects_suspicious_extension(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "runme.exe"
            path.write_text("binary", encoding="utf-8")
            results = heuristics.analyse_file(path)
            identifiers = {result.identifier for result in results}
            self.assertIn("suspicious-extension", identifiers)

    def test_detects_temp_process(self) -> None:
        info = {"name": "temp.tmp", "exe": "C:/temp/tmp.exe", "startup": False}
        results = heuristics.analyse_process(info)
        identifiers = {result.identifier for result in results}
        self.assertIn("temp-process", identifiers)


if __name__ == "__main__":
    unittest.main()

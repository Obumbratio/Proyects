import tempfile
from pathlib import Path
import unittest

from core.files import compute_sha256


class TestFiles(unittest.TestCase):
    def test_compute_sha256(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "sample.txt"
            path.write_text("antivirus", encoding="utf-8")
            digest = compute_sha256(path)
            self.assertEqual(
                digest,
                "d3bc9bd14ff82827399ca2cf48a4cdfd19cc4a876f81f5c4969d0a70afa54756",
            )


if __name__ == "__main__":
    unittest.main()

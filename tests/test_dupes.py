import tempfile
from pathlib import Path
import unittest

from core.dupes import find_duplicates


class TestDupes(unittest.TestCase):
    def test_find_duplicates(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            file_a = base / "a.txt"
            file_b = base / "b.txt"
            file_c = base / "c.txt"
            file_a.write_text("hello", encoding="utf-8")
            file_b.write_text("hello", encoding="utf-8")
            file_c.write_text("world", encoding="utf-8")
            duplicates = find_duplicates([file_a, file_b, file_c], block_size=1024)
            self.assertEqual(len(duplicates), 1)
            only_hash, paths = next(iter(duplicates.items()))
            self.assertEqual(set(paths), {file_a, file_b})


if __name__ == "__main__":
    unittest.main()

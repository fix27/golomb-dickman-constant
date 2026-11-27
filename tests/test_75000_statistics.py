"""Small deterministic tests for audit/75000_statistics.py.

Run with the standard library (pytest is not required):

    python -m unittest discover -s tests -v
"""

from __future__ import annotations

import hashlib
import importlib.util
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "audit" / "75000_statistics.py"

spec = importlib.util.spec_from_file_location("gd_stats", SCRIPT)
assert spec is not None and spec.loader is not None
stats = importlib.util.module_from_spec(spec)
spec.loader.exec_module(stats)


class HelperTests(unittest.TestCase):
    def test_canonical_hash(self) -> None:
        data = "6243299885"
        self.assertEqual(
            stats.canonical_hash(data),
            hashlib.sha256((data + "\n").encode("ascii")).hexdigest(),
        )

    def test_ngram_values(self) -> None:
        values = stats.ngram_values(__import__("numpy").array([1, 2, 3, 4]), 2)
        self.assertEqual(values.tolist(), [12, 23, 34])

    def test_kmp_finds_overlapping_hits(self) -> None:
        info = stats.kmp_all("abababa", "aba")
        self.assertEqual(info["first_0based"], [0, 2, 4])

    def test_longest_repeat_is_exact(self) -> None:
        info = stats.longest_repeat("xx6243299885yy6243299885zz")
        self.assertEqual(info["length"], 10)
        self.assertEqual(info["occurrences"], 2)
        self.assertEqual(info["substring"], "6243299885")

    def test_longest_palindrome(self) -> None:
        info = stats.longest_palindrome("a05224342250b")
        self.assertEqual(info["length"], 11)
        self.assertEqual(info["palindrome"], "05224342250")

    def test_berlekamp_massey_known_sequences(self) -> None:
        self.assertEqual(stats.berlekamp_massey([0] * 20), 0)
        self.assertEqual(stats.berlekamp_massey([1] * 20), 1)
        self.assertEqual(stats.berlekamp_massey([0, 1] * 10), 2)
        s = [1, 0, 1, 1, 0]
        for n in range(5, 100):
            s.append(s[n - 3] ^ s[n - 5])
        self.assertEqual(stats.berlekamp_massey(s), 5)


if __name__ == "__main__":
    unittest.main()

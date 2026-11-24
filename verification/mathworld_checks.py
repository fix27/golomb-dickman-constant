#!/usr/bin/env python3
"""Checks of the statements on MathWorld's "Golomb-Dickman Constant Digits"
page against a local decimal expansion of the Golomb-Dickman constant.

Page: https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html
      (retrieved 2026-11-16; page last updated 2026-11-14)

The script checks, claim by claim:

  * the opening digits 0.6243299885...;
  * the historical depth claims (Mitchell 1968, 53 places; Weisstein 2013,
    15,000 places) -- these are attributions, not reproducible values, so
    they are reported as NOT_VERIFIABLE rather than PASS/FAIL;
  * the Earls sequence (A225242): 28, 256, 1967, 387, ...;
  * the Lambda-constant prime lengths (A174974): 6, 27, 57, 60, 1659, 2508;
  * the first positions of n = 0, 1, 2, ... (A229195): 15, 28, 2, 4, ...;
  * digit scanning: the last new k-string and its end position for k = 1, 2, 3
    (1/28, 33/587, 821/6322), and the k = 4..6 coverage as an extension;
  * absence of 0123456789 and 9876543210 in the first 15,000 digits (and in
    the whole file);
  * the reported digit-count table for 10, 100, 1,000 and 10,000 digits;
  * the first Lambda-constant primes (A174975), the primality of the 1659- and
    2508-digit prefixes, and the fact that the whole 50,000-digit number is
    composite.

Extra long-sequence checks (not MathWorld claims):

  * longest runs: identical digits, per-digit, even/odd, low/high, prime
    digits, consecutive increasing/decreasing, alternating parity/low-high;
  * longest palindrome (Manacher);
  * longest repeated substring (2 and 3 occurrences), tandem repeats, and
    periodic runs with at least two full copies;
  * k-gram coverage for k = 1..6, missing 4-grams, most frequent 4/5/6-grams;
  * chi-square tests: digit frequencies, digit vs position mod 10, overlapping
    and non-overlapping pairs, and overlapping triples;
  * permutation-test p-values for up/down and equal/unequal runs (fixed-seed
    Monte Carlo, not an exact test);
  * optional prime scan: exhaustive prefix lengths 1..2508, a sampled scan
    from 2509 to 15000 (--deep-primes), and random substrings.

Usage
-----
    python verification/mathworld_checks.py
    python verification/mathworld_checks.py --primes
    python verification/mathworld_checks.py --primes --deep-primes --json out.json

Only the Python standard library is required.  sympy is optional and is used
for an independent BPSW confirmation of large candidates; without sympy the
Miller-Rabin result is reported as a probable prime.  Miller-Rabin and BPSW
are probable-prime tests: no APRCL/ECPP primality certificate is produced
here.  Nothing here proves normality, and nothing here is a world-record
claim.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)

REPO = Path(__file__).resolve().parent.parent
DEFAULT_DIGITS = REPO / "50000" / "golomb_dickman_50000_digits.txt"
DEFAULT_OEIS = REPO / "verification" / "reports" / "oeis"
PAGE_URL = "https://mathworld.wolfram.com/Golomb-DickmanConstantDigits.html"
PAGE_RETRIEVED = "2026-11-16"

EXPECTED_EARLS = {1: 28, 2: 256, 3: 1967, 4: 387}
EXPECTED_FIRST_POSITIONS = [15, 28, 2, 4, 3, 10, 1, 17, 8, 6]
EXPECTED_COUNTS = {
    10: [0, 0, 2, 1, 1, 1, 1, 0, 2, 2],
    100: [9, 7, 12, 10, 9, 12, 10, 5, 14, 12],
    1000: [89, 108, 93, 94, 100, 98, 104, 96, 109, 109],
    10000: [987, 999, 996, 989, 1021, 983, 1042, 995, 993, 995],
}
EXPECTED_PRIME_LENGTHS = [6, 27, 57, 60, 1659, 2508]


def configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_digits(path: Path) -> tuple[str, dict[str, object]]:
    raw = path.read_bytes()
    text = raw.decode("ascii")
    had_cr = "\r" in text
    normalized = text.replace("\r\n", "\n").replace("\r", "\n").strip()
    if not normalized.isdigit():
        raise SystemExit(f"{path}: not a decimal digit string")
    canonical = (normalized + "\n").encode("ascii")
    meta = {
        "path": str(path),
        "digits": len(normalized),
        "sha256_canonical": sha256_bytes(canonical),
        "sha256_as_read": sha256_bytes(raw),
        "had_cr": had_cr,
        "canonical_form": "digits followed by one LF",
    }
    return normalized, meta


def parse_bfile(path: Path) -> dict[int, str]:
    terms: dict[int, str] = {}
    if not path.is_file():
        return terms
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) != 2:
            continue
        terms[int(parts[0])] = parts[1]
    return terms


def first_start(digits: str, pattern: str) -> int | None:
    """1-based position of the first digit of the first occurrence."""
    index = digits.find(pattern)
    return None if index < 0 else index + 1


def chi2_sf(x: float, df: int) -> float:
    """Upper tail of the chi-square distribution, standard library only."""
    a = df / 2.0
    z = x / 2.0
    if z <= 0:
        return 1.0
    if z < a + 1.0:  # series for P(a, z)
        ap = a
        term = 1.0 / a
        total = term
        for _ in range(10000):
            ap += 1.0
            term *= z / ap
            total += term
            if abs(term) < abs(total) * 1e-16:
                break
        p = total * math.exp(-z + a * math.log(z) - math.lgamma(a))
        return max(0.0, min(1.0, 1.0 - p))
    tiny = 1e-300
    b = z + 1.0 - a
    c = 1.0 / tiny
    d = 1.0 / b
    h = d
    for i in range(1, 10000):
        an = -i * (i - a)
        b += 2.0
        d = an * d + b
        if abs(d) < tiny:
            d = tiny
        c = b + an / c
        if abs(c) < tiny:
            c = tiny
        d = 1.0 / d
        delta = d * c
        h *= delta
        if abs(delta - 1.0) < 1e-16:
            break
    q = math.exp(-z + a * math.log(z) - math.lgamma(a)) * h
    return max(0.0, min(1.0, q))


def run_count(values: list[int]) -> int:
    """Number of runs in a binary/sign sequence (0 for an empty sequence)."""
    if not values:
        return 0
    return 1 + sum(1 for i in range(1, len(values)) if values[i] != values[i - 1])


def permutation_runs_pvalue(
    values: list[int], trials: int = 500, seed: int = 20261124
) -> dict[str, object]:
    """Two-sided fixed-seed permutation test for the number of runs.

    Up/down signs are not independent after equal pairs are dropped, so a
    naive Wald-Wolfowitz normal approximation is inappropriate.  Shuffling
    the observed multiset of signs preserves its composition and calibrates
    the run count empirically.  This is Monte Carlo evidence, not an exact
    test; the seed makes it reproducible.
    """
    observed = run_count(values)
    if len(values) < 2:
        return {
            "runs": observed,
            "elements": len(values),
            "p_value": None,
            "method": "too few observations for a permutation test",
            "trials": 0,
            "extreme_or_equal": 0,
            "mean_runs": None,
        }
    rng = random.Random(seed)
    shuffled = list(values)
    permuted: list[int] = []
    for _ in range(trials):
        rng.shuffle(shuffled)
        permuted.append(run_count(shuffled))
    mean = sum(permuted) / trials
    deviation = abs(observed - mean)
    extreme = sum(1 for value in permuted if abs(value - mean) >= deviation)
    return {
        "runs": observed,
        "elements": len(values),
        "p_value": (extreme + 1) / (trials + 1),
        "method": (
            f"two-sided permutation test, fixed seed {seed}, "
            f"{trials} shuffles (Monte Carlo, not exact)"
        ),
        "trials": trials,
        "extreme_or_equal": extreme,
        "mean_runs": mean,
    }


# ---------------------------------------------------------------- MathWorld

def mathworld_claims(
    digits: str,
    oeis: Path,
    prime_result: dict[str, object] | None,
) -> list[dict[str, object]]:
    n = len(digits)
    claims: list[dict[str, object]] = []

    opening = digits[:10]
    claims.append(
        {
            "id": "opening",
            "statement": "decimal expansion begins 0.6243299885...",
            "verdict": "PASS" if opening == "6243299885" else "FAIL",
            "details": {"first_10": opening, "expected": "6243299885"},
        }
    )

    claims.append(
        {
            "id": "mitchell_53",
            "statement": "Mitchell (1968) computed lambda to 53 decimal places",
            "verdict": "NOT_VERIFIABLE",
            "details": {
                "reason": "historical attribution; the 1968 value is not on the page",
                "first_53": digits[:53],
                "note": "the 53-digit prefix is consistent with the certified value",
            },
        }
    )

    claims.append(
        {
            "id": "weisstein_15000",
            "statement": "lambda computed to 15000 decimal digits by E. Weisstein (2013)",
            "verdict": "NOT_VERIFIABLE",
            "details": {
                "reason": "historical computation-depth claim, not a numeric value",
                "our_digits": n,
                "note": "this file extends the reported depth; it does not verify the 2013 run",
            },
        }
    )

    earls = {}
    for copies, expected in EXPECTED_EARLS.items():
        pattern = str(copies) * copies
        actual = first_start(digits, pattern)
        earls[str(copies)] = {
            "pattern": pattern,
            "expected_start_position": expected,
            "actual_start_position": actual,
            "ok": actual == expected,
        }
    claims.append(
        {
            "id": "earls",
            "statement": "Earls sequence begins 28, 256, 1967, 387 (A225242)",
            "verdict": "PASS" if all(v["ok"] for v in earls.values()) else "FAIL",
            "details": earls,
        }
    )

    b229195 = parse_bfile(oeis / "b229195.txt")
    first_positions = {
        str(d): first_start(digits, str(d)) for d in range(10)
    }
    mismatches = []
    for key in sorted(b229195):
        expected = int(b229195[key])
        actual = first_start(digits, str(key))
        if actual != expected:
            mismatches.append({"n": key, "expected": expected, "actual": actual})
    first10_ok = [first_positions[str(d)] for d in range(10)] == EXPECTED_FIRST_POSITIONS
    claims.append(
        {
            "id": "a229195",
            "statement": "first positions of n = 0,1,2,... are 15,28,2,4,3,10,1,17,8,6 (A229195)",
            "verdict": "PASS" if first10_ok and not mismatches else "FAIL",
            "details": {
                "first_10": first_positions,
                "first_10_ok": first10_ok,
                "bfile_terms_checked": len(b229195),
                "bfile_max_position": max((int(v) for v in b229195.values()), default=None),
                "mismatches": mismatches,
                "bfile_present": bool(b229195),
            },
        }
    )

    scans = {k: scan_strings(digits, k) for k in range(1, 7)}
    scanning_ok = (
        scans[1]["last_new"] == "1"
        and scans[1]["last_end"] == 28
        and scans[2]["last_new"] == "33"
        and scans[2]["last_end"] == 587
        and scans[3]["last_new"] == "821"
        and scans[3]["last_end"] == 6322
    )
    claims.append(
        {
            "id": "digit_scanning",
            "statement": "last new strings for k=1,2,... are 1,33,821,... ending at 28,587,6322",
            "verdict": "PASS" if scanning_ok else "FAIL",
            "details": {
                "k1": scans[1],
                "k2": scans[2],
                "k3": scans[3],
                "extension_k4": scans[4],
                "extension_k5": scans[5],
                "extension_k6": scans[6],
            },
        }
    )

    absent = {}
    for pattern in ("0123456789", "9876543210"):
        pos_all = first_start(digits, pattern)
        pos_15k = first_start(digits[:15000], pattern)
        absent[pattern] = {
            "position_in_first_15000": pos_15k,
            "position_in_full_file": pos_all,
        }
    claims.append(
        {
            "id": "absent_pandigital",
            "statement": "0123456789 and 9876543210 do not occur in the first 15000 digits",
            "verdict": "PASS"
            if all(v["position_in_first_15000"] is None for v in absent.values())
            else "FAIL",
            "details": absent,
        }
    )

    claims.append(
        {
            "id": "normality",
            "statement": "it is not known whether lambda is normal in base 10",
            "verdict": "OPEN",
            "details": {
                "note": "a statement about the state of knowledge, not a digit pattern; "
                "50,000 digits cannot establish normality either way",
            },
        }
    )

    counts = {}
    counts_ok = True
    for length, expected in EXPECTED_COUNTS.items():
        actual = [digits[:length].count(str(d)) for d in range(10)]
        ok = actual == expected
        counts_ok = counts_ok and ok
        counts[str(length)] = {"expected": expected, "actual": actual, "ok": ok}
    counts["50000"] = {
        "actual": [digits.count(str(d)) for d in range(10)],
        "note": "extension: full file",
    }
    claims.append(
        {
            "id": "digit_counts",
            "statement": "reported digit counts for the first 10, 100, 1000 and 10000 digits",
            "verdict": "PASS" if counts_ok else "FAIL",
            "details": counts,
        }
    )

    b174975 = parse_bfile(oeis / "b174975.txt")
    prime_prefixes = {}
    for key in sorted(b174975, key=int):
        value = b174975[key]
        prime_prefixes[str(key)] = {
            "digits": len(value),
            "matches_prefix": digits[: len(value)] == value,
            "head": value[:30] + ("..." if len(value) > 30 else ""),
        }
    prefixes_ok = bool(prime_prefixes) and all(
        v["matches_prefix"] for v in prime_prefixes.values()
    )
    claims.append(
        {
            "id": "a174975",
            "statement": "first lambda-constant primes are 624329, 624329988543550870992936383, ...",
            "verdict": "PASS" if prefixes_ok else "FAIL" if prime_prefixes else "NOT_RUN",
            "details": {
                "bfile_terms": len(prime_prefixes),
                "values": prime_prefixes,
                "bfile_present": (oeis / "b174975.txt").is_file(),
            },
        }
    )

    if prime_result is None:
        claims.append(
            {
                "id": "prime_lengths",
                "statement": "lambda-constant primes occur for 6,27,57,60,1659,2508,... digits",
                "verdict": "NOT_RUN",
                "details": {"hint": "rerun with --primes"},
            }
        )
        claims.append(
            {
                "id": "search_15000",
                "statement": "Weisstein reported a completed prime search through 15000 digits",
                "verdict": "NOT_VERIFIABLE",
                "details": {"hint": "rerun with --primes --deep-primes for a partial check"},
            }
        )
    else:
        found = prime_result["exhaustive_1_2508"]["prime_lengths"]
        claims.append(
            {
                "id": "prime_lengths",
                "statement": "lambda-constant primes occur for 6,27,57,60,1659,2508,... digits",
                "verdict": "PASS" if found == EXPECTED_PRIME_LENGTHS else "FAIL",
                "details": {
                    "exhaustive_scan_1_2508": found,
                    "expected": EXPECTED_PRIME_LENGTHS,
                    "strong": prime_result["strong_primes"],
                },
            }
        )
        sample = prime_result.get("sample_2509_15000")
        if sample is None:
            claims.append(
                {
                    "id": "search_15000",
                    "statement": "Weisstein reported a completed prime search through 15000 digits",
                    "verdict": "NOT_VERIFIABLE",
                    "details": {
                        "reason": "an exhaustive 2509..15000 scan was not run; "
                        "the historical run cannot be verified from the digits alone"
                    },
                }
            )
        else:
            claims.append(
                {
                    "id": "search_15000",
                    "statement": "Weisstein reported a completed prime search through 15000 digits",
                    "verdict": "PARTIAL",
                    "details": {
                        "sampled_lengths": sample["lengths_tested"],
                        "first": sample["first"],
                        "last": sample["last"],
                        "step": sample["step"],
                        "primes_found": sample["prime_lengths"],
                        "note": "real or composite at the sampled lengths only; "
                        "sampling cannot confirm or refute the historical exhaustive search",
                    },
                }
            )

    return claims


# ------------------------------------------------------------- digit checks

def scan_strings(digits: str, k: int) -> dict[str, object]:
    seen: set[str] = set()
    last_new = None
    last_end = None
    for i in range(len(digits) - k + 1):
        window = digits[i : i + k]
        if window not in seen:
            seen.add(window)
            last_new = window
            last_end = i + k
    possible = 10**k
    return {
        "length": k,
        "possible": possible,
        "distinct": len(seen),
        "missing": possible - len(seen),
        "complete": len(seen) == possible,
        "last_new": last_new,
        "last_end": last_end,
    }


def longest_run(digits: str, predicate) -> dict[str, object]:
    best = (0, 0, 0)
    current = 0
    start = 0
    for i, ch in enumerate(digits):
        if predicate(int(ch)):
            if current == 0:
                start = i
            current += 1
            if current > best[0]:
                best = (current, start, i)
        else:
            current = 0
    length, first, last = best
    return {
        "length": length,
        "start": first + 1,
        "end": last + 1,
        "substring": digits[first : last + 1],
    }


def identical_runs(digits: str) -> dict[str, object]:
    runs = []
    current = 1
    start = 0
    for i in range(1, len(digits) + 1):
        if i < len(digits) and digits[i] == digits[i - 1]:
            current += 1
            continue
        if current >= 2:
            runs.append(
                {
                    "length": current,
                    "start": start + 1,
                    "end": i,
                    "digit": digits[start],
                }
            )
        if i < len(digits):
            start = i
            current = 1
    runs.sort(key=lambda r: (-r["length"], r["start"]))
    return {
        "longest": runs[0] if runs else None,
        "top10": runs[:10],
        "count_runs_length_ge_6": sum(1 for r in runs if r["length"] >= 6),
        "count_runs_length_ge_2": len(runs),
    }


def consecutive_run(digits: str, step: int) -> dict[str, object]:
    best = (0, 0, 0)
    current = 1
    start = 0
    for i in range(1, len(digits)):
        if int(digits[i]) - int(digits[i - 1]) == step:
            current += 1
        else:
            if current > best[0]:
                best = (current, start, i - 1)
            current = 1
            start = i
    if current > best[0]:
        best = (current, start, len(digits) - 1)
    length, first, last = best
    return {
        "length": length,
        "start": first + 1,
        "end": last + 1,
        "substring": digits[first : last + 1],
    }


def alternating_run(digits: str, key) -> dict[str, object]:
    best = (0, 0, 0)
    current = 1
    start = 0
    for i in range(1, len(digits)):
        if key(int(digits[i])) != key(int(digits[i - 1])):
            current += 1
        else:
            if current > best[0]:
                best = (current, start, i - 1)
            current = 1
            start = i
    if current > best[0]:
        best = (current, start, len(digits) - 1)
    length, first, last = best
    return {
        "length": length,
        "start": first + 1,
        "end": last + 1,
        "substring": digits[first : last + 1],
    }


def longest_palindrome(digits: str) -> dict[str, object]:
    transformed = "^#" + "#".join(digits) + "#$"
    radius = [0] * len(transformed)
    center = right = 0
    for i in range(1, len(transformed) - 1):
        mirror = 2 * center - i
        if i < right:
            radius[i] = min(right - i, radius[mirror])
        while (
            transformed[i + 1 + radius[i]] == transformed[i - 1 - radius[i]]
        ):
            radius[i] += 1
        if i + radius[i] > right:
            center, right = i, i + radius[i]
    length, middle = max((value, i) for i, value in enumerate(radius))
    start = (middle - length) // 2
    return {
        "length": length,
        "start": start + 1,
        "end": start + length,
        "substring": digits[start : start + length],
    }


class RollingHash:
    def __init__(self, digits: str) -> None:
        self.digits = digits
        self.mod1 = (1 << 61) - 1
        self.mod2 = (1 << 64) - 1
        self.base = 911382323
        count = len(digits)
        self.pow1 = [1] * (count + 1)
        self.pow2 = [1] * (count + 1)
        self.hash1 = [0] * (count + 1)
        self.hash2 = [0] * (count + 1)
        for i, ch in enumerate(digits):
            value = int(ch) + 1
            self.pow1[i + 1] = (self.pow1[i] * self.base) % self.mod1
            self.pow2[i + 1] = (self.pow2[i] * self.base) % self.mod2
            self.hash1[i + 1] = (self.hash1[i] * self.base + value) % self.mod1
            self.hash2[i + 1] = (self.hash2[i] * self.base + value) % self.mod2

    def get(self, start: int, length: int) -> tuple[int, int]:
        first = (
            self.hash1[start + length] - self.hash1[start] * self.pow1[length]
        ) % self.mod1
        second = (
            self.hash2[start + length] - self.hash2[start] * self.pow2[length]
        ) % self.mod2
        return first, second

    def find(self, length: int, need: int = 2) -> list[int] | None:
        seen: dict[tuple[int, int], list[int]] = {}
        for start in range(len(self.digits) - length + 1):
            key = self.get(start, length)
            bucket = seen.get(key)
            if bucket is None:
                seen[key] = [start]
                continue
            for previous in bucket:
                if (
                    self.digits[previous : previous + length]
                    == self.digits[start : start + length]
                ):
                    bucket.append(start)
                    if len(bucket) >= need:
                        return bucket[:need]
                    break
            else:
                bucket.append(start)
        return None

    def longest_repeat(self, need: int = 2):
        low, high = 1, len(self.digits) - 1
        best = None
        while low <= high:
            middle = (low + high) // 2
            found = self.find(middle, need)
            if found:
                best = (middle, found)
                low = middle + 1
            else:
                high = middle - 1
        return best


def repeat_details(digits: str, start0: int, length: int) -> dict[str, object]:
    substring = digits[start0 : start0 + length]
    occurrences = []
    cursor = 0
    while True:
        index = digits.find(substring, cursor)
        if index < 0:
            break
        occurrences.append(index + 1)
        cursor = index + 1
    return {
        "length": length,
        "substring": substring,
        "occurrences": occurrences,
        "start": start0 + 1,
    }


def digit_checks(digits: str) -> dict[str, object]:
    n = len(digits)

    counts = [digits.count(str(d)) for d in range(10)]
    digit_sum = sum(int(ch) for ch in digits)
    mean = digit_sum / n
    variance = sum((int(ch) - 4.5) ** 2 for ch in digits) / n
    chi_uniform = sum((value - n / 10) ** 2 / (n / 10) for value in counts)

    position_table = [[0] * 10 for _ in range(10)]
    for i, ch in enumerate(digits):
        position_table[i % 10][int(ch)] += 1
    cell = n / 100.0
    chi_position = sum(
        (position_table[row][col] - cell) ** 2 / cell
        for row in range(10)
        for col in range(10)
    )

    pair_counts = Counter(digits[i : i + 2] for i in range(n - 1))
    pair_expected = (n - 1) / 100.0
    chi_pairs = sum(
        (value - pair_expected) ** 2 / pair_expected for value in pair_counts.values()
    )
    chi_pairs += pair_expected * (100 - len(pair_counts))

    nonoverlap = Counter(digits[i : i + 2] for i in range(0, n - 1, 2))
    nonoverlap_expected = len(range(0, n - 1, 2)) / 100.0
    chi_nonoverlap = sum(
        (value - nonoverlap_expected) ** 2 / nonoverlap_expected
        for value in nonoverlap.values()
    )
    chi_nonoverlap += nonoverlap_expected * (100 - len(nonoverlap))

    triple_counts = Counter(digits[i : i + 3] for i in range(n - 2))
    triple_expected = (n - 2) / 1000.0
    chi_triplets = sum(
        (value - triple_expected) ** 2 / triple_expected
        for value in triple_counts.values()
    )
    chi_triplets += triple_expected * (1000 - len(triple_counts))

    up_down: list[int] = []
    equal_unequal: list[int] = []
    for i in range(n - 1):
        left, right = int(digits[i]), int(digits[i + 1])
        equal_unequal.append(1 if right == left else 0)
        if right != left:
            up_down.append(1 if right > left else -1)
    runs_significance = {
        "up_down": permutation_runs_pvalue(up_down),
        "equal_unequal": permutation_runs_pvalue(equal_unequal),
    }

    coverage = {}
    for k in range(1, 7):
        counter = Counter(digits[i : i + k] for i in range(n - k + 1))
        coverage[str(k)] = {
            "possible": 10**k,
            "distinct": len(counter),
            "missing": 10**k - len(counter),
            "max_count": max(counter.values()),
            "most_common": counter.most_common(5),
        }

    missing4 = []
    seen4 = {digits[i : i + 4] for i in range(n - 3)}
    for value in range(10000):
        word = f"{value:04d}"
        if word not in seen4:
            missing4.append(word)
            if len(missing4) == 10:
                break

    per_digit_runs = {}
    for d in range(10):
        per_digit_runs[str(d)] = longest_run(digits, lambda x, d=d: x == d)

    hashing = RollingHash(digits)
    start_time = time.time()
    repeat2 = hashing.longest_repeat(2)
    repeat3 = hashing.longest_repeat(3)
    repeats_seconds = round(time.time() - start_time, 1)

    tandem = None
    for block_length in range(200, 0, -1):
        match = re.search(r"(?=(\d{%d})\1)" % block_length, digits)
        if match:
            tandem = {
                "block_length": block_length,
                "total_length": 2 * block_length,
                "start": match.start() + 1,
                "block": match.group(1),
            }
            break

    periodic = []
    for period in range(1, 101):
        best = (0, 0)
        current = 0
        start = 0
        for i in range(period, n):
            if digits[i] == digits[i - period]:
                if current == 0:
                    start = i - period
                current += 1
                if current > best[0]:
                    best = (current, start)
            else:
                current = 0
        comparisons, start = best
        if comparisons >= period:  # at least two full copies
            periodic.append(
                {
                    "period": period,
                    "repeat_length": comparisons + period,
                    "start": start + 1,
                    "end": start + comparisons + period,
                    "substring": digits[start : start + comparisons + period],
                }
            )
    periodic.sort(key=lambda item: (-item["repeat_length"], item["period"]))

    return {
        "digit_sum": digit_sum,
        "digit_mean": mean,
        "digit_variance": variance,
        "counts": counts,
        "chi2_uniform": {
            "value": chi_uniform,
            "df": 9,
            "p_value": chi2_sf(chi_uniform, 9),
            "critical_5pct": 16.919,
        },
        "chi2_position_mod10": {
            "value": chi_position,
            "df": 81,
            "p_value": chi2_sf(chi_position, 81),
            "critical_5pct": 103.010,
        },
        "pairs": {
            "distinct": len(pair_counts),
            "min_count": min(pair_counts.values()),
            "max_count": max(pair_counts.values()),
            "most_common": pair_counts.most_common(5),
            "chi2": chi_pairs,
            "df": 99,
            "p_value": chi2_sf(chi_pairs, 99),
            "critical_5pct": 123.225,
        },
        "nonoverlap_pairs": {
            "pairs": len(range(0, n - 1, 2)),
            "distinct": len(nonoverlap),
            "chi2": chi_nonoverlap,
            "df": 99,
            "p_value": chi2_sf(chi_nonoverlap, 99),
            "critical_5pct": 123.225,
        },
        "chi2_triplets": {
            "triples": n - 2,
            "distinct": len(triple_counts),
            "value": chi_triplets,
            "df": 999,
            "p_value": chi2_sf(chi_triplets, 999),
        },
        "coverage": coverage,
        "missing_4grams_first10": missing4,
        "expected_missing_4grams": 10000 * math.exp(-(n - 3) / 10000),
        "expected_distinct_5grams": 100000 * (1 - math.exp(-(n - 4) / 100000)),
        "expected_distinct_6grams": 1000000 * (1 - math.exp(-(n - 5) / 1000000)),
        "runs": {
            "identical": identical_runs(digits),
            "per_digit": per_digit_runs,
            "even": longest_run(digits, lambda x: x % 2 == 0),
            "odd": longest_run(digits, lambda x: x % 2 == 1),
            "low_0_4": longest_run(digits, lambda x: x < 5),
            "high_5_9": longest_run(digits, lambda x: x >= 5),
            "prime_digits_2_3_5_7": longest_run(digits, lambda x: x in (2, 3, 5, 7)),
            "increasing_consecutive": consecutive_run(digits, 1),
            "decreasing_consecutive": consecutive_run(digits, -1),
            "alternating_parity": alternating_run(digits, lambda x: x % 2),
            "alternating_low_high": alternating_run(digits, lambda x: x < 5),
        },
        "runs_significance": runs_significance,
        "palindrome": longest_palindrome(digits),
        "repeats": {
            "longest_repeated_twice": repeat_details(digits, repeat2[1][0], repeat2[0])
            if repeat2
            else None,
            "longest_repeated_three_times": repeat_details(digits, repeat3[1][0], repeat3[0])
            if repeat3
            else None,
            "seconds": repeats_seconds,
        },
        "tandem_repeat": tandem,
        "periodic_runs": periodic[:10],
    }


# ------------------------------------------------------------------ primes

def make_small_primes(limit: int = 1000) -> list[int]:
    sieve = bytearray(b"\x01") * (limit + 1)
    sieve[0:2] = b"\x00\x00"
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i * i : limit + 1 : i] = b"\x00" * (
                ((limit - i * i) // i) + 1
            )
    return [i for i in range(2, limit + 1) if sieve[i]]


SMALL_PRIMES = make_small_primes()


def is_probable_prime(n: int, bases=(2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)) -> bool:
    if n < 2:
        return False
    for p in SMALL_PRIMES:
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in bases:
        if a >= n:
            continue
        x = pow(a, d, n)
        if x == 1 or x == n - 1:
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            return False
    return True


def sympy_isprime(n: int) -> bool | str:
    try:
        import sympy  # type: ignore

        return bool(sympy.isprime(n))
    except Exception as exc:  # pragma: no cover - optional dependency
        return f"unavailable: {exc}"


def prime_checks(digits: str, deep: bool) -> dict[str, object]:
    result: dict[str, object] = {
        "trial_division_limit": SMALL_PRIMES[-1],
        "method": "trial division plus Miller-Rabin (12 fixed bases for the "
        "large prefixes); sympy BPSW when available.  These are "
        "probable-prime tests, not APRCL/ECPP primality proofs",
    }

    # Exhaustive prefix scan 1..2508.
    found = []
    value = 0
    started = time.time()
    for length, ch in enumerate(digits[:2508], start=1):
        value = value * 10 + int(ch)
        if is_probable_prime(value, bases=(2, 3, 5, 7, 11)):
            found.append(length)
    elapsed = time.time() - started
    result["exhaustive_1_2508"] = {
        "limit": 2508,
        "prime_lengths": found,
        "seconds": round(elapsed, 1),
    }
    print(
        f"  primes 1..2508: {found} in {elapsed:.1f}s", flush=True
    )

    strong = {}
    for length in (1659, 2508):
        candidate = int(digits[:length])
        started = time.time()
        miller = is_probable_prime(candidate)
        miller_seconds = time.time() - started
        started = time.time()
        bpsw = sympy_isprime(candidate)
        bpsw_seconds = time.time() - started
        strong[str(length)] = {
            "digits": length,
            "miller_rabin_12_bases": miller,
            "sympy_bpsw": bpsw,
            "seconds_miller_rabin": round(miller_seconds, 1),
            "seconds_bpsw": round(bpsw_seconds, 1),
            "head": digits[:20],
            "tail": digits[length - 20 : length],
        }
        print(f"  strong {length}: MR={miller} BPSW={bpsw}", flush=True)
    result["strong_primes"] = strong

    total = sum(int(ch) for ch in digits)
    result["whole_50000_digit_number"] = {
        "last_digit": digits[-1],
        "digit_sum": total,
        "divisible_by_10": digits[-1] == "0",
        "divisible_by_3": total % 3 == 0,
        "divisible_by_9": total % 9 == 0,
        "conclusion": "composite (last digit 0)" if digits[-1] == "0" else "see checks",
    }

    if not deep:
        return result

    # Sampled scan 2509..15000: every 97th length plus a few round numbers.
    sample = set(range(2509, 15001, 97))
    sample.update([3000, 3500, 4000, 4500, 5000, 6000, 7500, 9000, 10000, 12000, 15000])
    sample = sorted(sample)
    sample_found = []
    value = int(digits[:2508])
    started = time.time()
    for length in range(2509, 15001):
        value = value * 10 + int(digits[length - 1])
        if length in sample and is_probable_prime(value, bases=(2, 3, 5, 7)):
            sample_found.append(length)
            print(f"  sampled prime at {length}", flush=True)
    elapsed = time.time() - started
    result["sample_2509_15000"] = {
        "lengths_tested": len(sample),
        "first": sample[0],
        "last": sample[-1],
        "step": 97,
        "prime_lengths": sample_found,
        "seconds": round(elapsed, 1),
    }
    print(
        f"  sampled 2509..15000: {len(sample)} lengths, found {sample_found}, {elapsed:.1f}s",
        flush=True,
    )

    rng = random.Random(20261116)
    random_results = {}
    for length, requested in ((20, 60), (50, 60), (100, 60), (200, 40), (1000, 20), (5000, 5)):
        tested = 0
        primes = []
        started = time.time()
        for _ in range(requested):
            start = rng.randrange(0, len(digits) - length)
            if digits[start] == "0":
                continue
            candidate = int(digits[start : start + length])
            tested += 1
            if is_probable_prime(candidate, bases=(2, 3, 5, 7, 11)):
                primes.append(
                    {
                        "start": start + 1,
                        "head": digits[start : start + 20],
                        "tail": digits[start + length - 10 : start + length],
                    }
                )
        random_results[str(length)] = {
            "requested": requested,
            "tested": tested,
            "probable_primes": len(primes),
            "examples": primes[:5],
            "seconds": round(time.time() - started, 1),
        }
        print(
            f"  random substrings length {length}: {tested} tested, {len(primes)} probable primes",
            flush=True,
        )
    result["random_substrings"] = random_results
    return result


# --------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    configure_stdio()
    parser = argparse.ArgumentParser(
        description="Check MathWorld's Golomb-Dickman Constant Digits statements."
    )
    parser.add_argument("--digits", type=Path, default=DEFAULT_DIGITS)
    parser.add_argument("--oeis-dir", type=Path, default=DEFAULT_OEIS)
    parser.add_argument("--json", type=Path, default=None, help="write the full report")
    parser.add_argument("--primes", action="store_true", help="run the prime checks")
    parser.add_argument(
        "--deep-primes",
        action="store_true",
        help="also sample prefix lengths 2509..15000 and random substrings (slow)",
    )
    args = parser.parse_args(argv)
    if args.deep_primes:
        args.primes = True

    digits, meta = load_digits(args.digits)
    print(
        f"digits: {meta['digits']}  sha256(canonical): {meta['sha256_canonical']}  "
        f"as-read: {meta['sha256_as_read']}  CRLF: {meta['had_cr']}"
    )

    started = time.time()
    prime_result = None
    if args.primes:
        print("prime checks:", flush=True)
        prime_result = prime_checks(digits, args.deep_primes)
    claims = mathworld_claims(digits, args.oeis_dir, prime_result)
    print("digit checks:", flush=True)
    extras = digit_checks(digits)
    elapsed = time.time() - started

    report = {
        "author": {
            "name_ru": "Поздняков Константин Николаевич",
            "name_en": "Konstantin N. Pozdnyakov",
            "location": "Surgut, Khanty-Mansi Autonomous Okrug — Yugra, Russia",
            "email": "fix@inbox.ru",
        },
        "page": {
            "url": PAGE_URL,
            "retrieved": PAGE_RETRIEVED,
            "note": "statement wording paraphrased from the page",
        },
        "inputs": meta,
        "mathworld": claims,
        "extra_checks": extras,
        "primes": prime_result,
        "seconds": round(elapsed, 1),
        "disclaimer": (
            "These are checks of the listed statements and of the digit string. "
            "They do not prove that lambda lies in the certified interval, do not "
            "establish normality, and are not a world-record claim."
        ),
    }

    print("\nMathWorld claims:")
    for claim in claims:
        print(f"  [{claim['verdict']:>14}] {claim['id']}: {claim['statement']}")

    print("\nExtra checks:")
    runs = extras["runs"]
    print(f"  digit counts: {extras['counts']}")
    print(
        f"  chi2 uniform: {extras['chi2_uniform']['value']:.4f} "
        f"(p={extras['chi2_uniform']['p_value']:.4f})"
    )
    print(
        f"  chi2 position mod 10: {extras['chi2_position_mod10']['value']:.3f} "
        f"(p={extras['chi2_position_mod10']['p_value']:.4f})"
    )
    print(
        f"  chi2 triplets: {extras['chi2_triplets']['value']:.4f} "
        f"(df={extras['chi2_triplets']['df']}, "
        f"p={extras['chi2_triplets']['p_value']:.4f})"
    )
    for name, test in extras["runs_significance"].items():
        p_value = test["p_value"]
        shown = "n/a" if p_value is None else f"{p_value:.4f}"
        print(f"  runs test ({name}): {test['runs']} runs, p={shown}")
    print(
        f"  identical run: {runs['identical']['longest']}; "
        f"runs >= 6: {runs['identical']['count_runs_length_ge_6']}"
    )
    print(f"  increasing: {runs['increasing_consecutive']}")
    print(f"  decreasing: {runs['decreasing_consecutive']}")
    print(f"  alternating parity: {runs['alternating_parity']['length']}")
    print(f"  alternating low/high: {runs['alternating_low_high']['length']}")
    print(f"  palindrome: {extras['palindrome']}")
    print(f"  repeat twice: {extras['repeats']['longest_repeated_twice']}")
    print(f"  repeat three times: {extras['repeats']['longest_repeated_three_times']}")
    print(f"  tandem: {extras['tandem_repeat']}")
    print(f"  periodic: {extras['periodic_runs'][:3]}")
    print(
        "  coverage: "
        + ", ".join(
            f"k={k}: {v['distinct']}/{v['possible']} (missing {v['missing']})"
            for k, v in extras["coverage"].items()
        )
    )
    if prime_result:
        print(f"  prime lengths 1..2508: {prime_result['exhaustive_1_2508']['prime_lengths']}")
        if "sample_2509_15000" in prime_result:
            print(
                f"  sampled 2509..15000: {prime_result['sample_2509_15000']['prime_lengths']}"
            )
        print(f"  whole number: {prime_result['whole_50000_digit_number']['conclusion']}")

    print(f"\ntotal: {elapsed:.1f}s")
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        print(f"report: {args.json}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

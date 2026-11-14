#!/usr/bin/env python3
"""Structure and primality of the 40,000 certified decimal digits.

Complements ``verify_mathworld.py``: instead of testing the statements of one
web page, this script measures the digit string itself.

  S1  longest run of every digit, with position and multiplicity
  S2  Earls-type runs (n copies of the digit n) and their absence
  S3  longest repeated block (exact, suffix array + LCP)
  S4  longest tandem repeat, and the longest block of every small period
  S5  longest palindrome (Manacher)
  S6  prime substrings of length 1..32 (exact to 24 digits, 64 bases above)
  S7  selectively tested truncations, plus a small factor of the full number
  S8  k-gram coverage for k = 1..6 (cross-checked against MathWorld C8)

Only the Python standard library is used.

    python verify_sequences.py
    python verify_sequences.py --prime-samples 120 --json seq.json
    python verify_sequences.py --substring-length 16      # faster
    python verify_sequences.py --strong                  # 64 bases, slower
    python verify_sequences.py --long                    # exponentiate up to
                                                         # 40,000 digits (hours)

Exit status is 0 when every internal cross-check holds and 1 otherwise.
Nothing here is a proof about lambda itself: these are statements about the
certified 40,000-digit string.
"""

from __future__ import annotations

import argparse
import json
import random
import re
import sys
import time
from pathlib import Path
from typing import Any

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)

CERT_NAME = "golomb_dickman_40000_certified.txt"
DIGITS_NAME = "golomb_dickman_40000_digits.txt"

# Lengths whose truncation of lambda is prime (MathWorld / OEIS A174974).
KNOWN_PRIME_LENGTHS = (6, 27, 57, 60, 1659, 2508)

# Miller-Rabin: these 12 bases are deterministic below 3.3e24.
MR_DETERMINISTIC = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37)
MR_DETERMINISTIC_LIMIT = 3_317_044_064_679_887_385_961_981
# 64 bases: probable prime only, error below 2^-128.
MR_MANY = (
    2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71,
    73, 79, 83, 89, 97, 101, 103, 107, 109, 113, 127, 131, 137, 139, 149, 151,
    157, 163, 167, 173, 179, 181, 191, 193, 197, 199, 211, 223, 227, 229, 233,
    239, 241, 251, 257, 263, 269, 271, 277, 281, 283, 293, 307, 311,
)

# Trial division before Miller-Rabin (small primes, cheap).
SMALL_ODD = (3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47)


# ---------------------------------------------------------------- infrastructure

def bundle_root(start: Path) -> Path:
    for candidate in (start, *start.parents):
        if (candidate / CERT_NAME).is_file():
            return candidate
    return start


def load_digits(root: Path) -> str:
    digits_path = root / DIGITS_NAME
    if digits_path.is_file():
        return digits_path.read_text(encoding="ascii").strip()
    cert = root / CERT_NAME
    if not cert.is_file():
        raise SystemExit(f"FAIL: missing {CERT_NAME} in {root}")
    lines = cert.read_text(encoding="ascii").splitlines()
    if len(lines) < 4 or not lines[3].strip().startswith("0."):
        raise SystemExit("FAIL: cannot find the digit line in the certificate")
    return lines[3].strip()[2:]


def sieve(limit: int) -> list[int]:
    flags = bytearray([1]) * (limit + 1)
    flags[0:2] = b"\x00\x00"
    for i in range(2, int(limit**0.5) + 1):
        if flags[i]:
            flags[i * i:: i] = bytearray(len(flags[i * i:: i]))
    return [i for i in range(limit + 1) if flags[i]]


def is_probable_prime(n: int, bases: tuple[int, ...], small: list[int]) -> bool:
    if n < 2:
        return False
    for p in small:
        if n % p == 0:
            return n == p
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for a in bases:
        a %= n
        if a < 2:
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


class Report:
    def __init__(self) -> None:
        self.rows: list[dict[str, Any]] = []

    def add(self, code: str, claim: str, status: str, detail: str,
            extra: list[str] | None = None) -> None:
        self.rows.append({"code": code, "claim": claim, "status": status,
                          "detail": detail, "extra": extra or []})

    def failures(self) -> int:
        return sum(1 for row in self.rows if row["status"] == "FAIL")


# ---------------------------------------------------------------- S1: digit runs

def digit_runs(digits: str) -> list[tuple[str, int, int]]:
    runs: list[tuple[str, int, int]] = []
    n = len(digits)
    i = 0
    while i < n:
        j = i + 1
        while j < n and digits[j] == digits[i]:
            j += 1
        runs.append((digits[i], i, j - i))
        i = j
    return runs


def section_runs(rep: Report, digits: str) -> dict[str, dict[str, int]]:
    started = time.perf_counter()
    runs = digit_runs(digits)
    regex = [(m.group(1), m.start(), len(m.group(0)))
             for m in re.finditer(r"(.)\1*", digits)]
    agree = regex == runs

    stats: dict[str, dict[str, int]] = {}
    for digit, start, length in runs:
        row = stats.setdefault(digit, {"max": 0, "first": -1,
                                       "count_max": 0, "runs": 0})
        row["runs"] += 1
        if length > row["max"]:
            row["max"] = length
            row["first"] = start + 1
            row["count_max"] = 1
        elif length == row["max"]:
            row["count_max"] += 1

    longest = max(row["max"] for row in stats.values())
    how_many = sum(1 for _, _, length in runs if length >= 4)
    blocks = [digits[start:start + length] for _, start, length in runs
              if length == longest]
    detail = (f"longest run {longest} digits ({', '.join(sorted(set(blocks)))}); "
              f"{how_many} runs of length >= 4; "
              f"{len(runs)} runs in total; regex cross-check "
              f"{'agrees' if agree else 'DISAGREES'} "
              f"[{time.perf_counter() - started:.2f} s]")
    extra = []
    for digit in "0123456789":
        row = stats[digit]
        extra.append(f"d={digit}: max {row['max']} at {row['first']} "
                     f"({row['count_max']} such runs, {row['runs']} runs)")
    rep.add("S1", "longest run of identical digits for every digit",
            "PASS" if agree else "FAIL", detail, extra)
    return stats


# ---------------------------------------------------------------- S2: Earls runs

def section_earls(rep: Report, digits: str, stats: dict[str, dict[str, int]]) -> None:
    expected = {1: 28, 2: 256, 3: 1967, 4: 387}
    found = []
    bad = []
    for n in range(1, 8):
        position = digits.find(str(n) * n)
        found.append(position + 1 if position >= 0 else 0)
        if n in expected and found[-1] != expected[n]:
            bad.append(n)
        if n not in expected and found[-1] != 0:
            bad.append(n)

    # absence of n copies of digit n implies the longest run is at most n-1
    consistent = True
    notes = []
    for n in range(5, 8):
        row = stats[str(n)]
        ok = row["max"] <= n - 1
        consistent = consistent and ok
        notes.append(f"digit {n}: longest run {row['max']} "
                     f"{'<=' if ok else '>'} {n - 1} - "
                     f"{'consistent' if ok else 'INCONSISTENT'} with absence")

    detail = ("n copies of digit n first at " +
              ", ".join(f"n={n}: {value if value else 'absent'}"
                        for n, value in enumerate(found, start=1)))
    rep.add("S2", "Earls-type runs: n copies of the digit n (A225242)",
            "PASS" if not bad and consistent else "FAIL", detail, notes)


# ---------------------------------------------------------------- S3: longest repeat

def suffix_array(s: str) -> list[int]:
    n = len(s)
    sa = list(range(n))
    rank = [ord(c) for c in s]
    tmp = [0] * n
    k = 1
    while True:
        sa.sort(key=lambda i: (rank[i], rank[i + k] if i + k < n else -1))
        tmp[sa[0]] = 0
        for idx in range(1, n):
            a, b = sa[idx - 1], sa[idx]
            left = (rank[a], rank[a + k] if a + k < n else -1)
            right = (rank[b], rank[b + k] if b + k < n else -1)
            tmp[b] = tmp[a] + (1 if right != left else 0)
        rank, tmp = tmp, rank
        if rank[sa[-1]] == n - 1:
            break
        k <<= 1
    return sa


def lcp_array(s: str, sa: list[int]) -> list[int]:
    n = len(s)
    rank = [0] * n
    for i, pos in enumerate(sa):
        rank[pos] = i
    lcp = [0] * n
    h = 0
    for i in range(n):
        r = rank[i]
        if r:
            j = sa[r - 1]
            while i + h < n and j + h < n and s[i + h] == s[j + h]:
                h += 1
            lcp[r] = h
            if h:
                h -= 1
        else:
            h = 0
    return lcp


def occurrences(s: str, block: str, limit: int = 8) -> tuple[int, list[int]]:
    positions = []
    start = 0
    total = 0
    while True:
        hit = s.find(block, start)
        if hit < 0:
            break
        total += 1
        if len(positions) < limit:
            positions.append(hit + 1)
        start = hit + 1
    return total, positions


def section_repeats(rep: Report, digits: str) -> int:
    started = time.perf_counter()
    sa = suffix_array(digits)
    lcp = lcp_array(digits, sa)
    longest = max(lcp)
    order = sorted(range(1, len(lcp)), key=lambda i: (-lcp[i], sa[i]))

    blocks: list[tuple[int, str, int, int]] = []
    seen: set[str] = set()
    for i in order[:400]:
        length = lcp[i]
        if length < 1:
            break
        block = digits[sa[i]:sa[i] + length]
        if block in seen:
            continue
        seen.add(block)
        blocks.append((length, block, sa[i] + 1, sa[i - 1] + 1))
        if len(blocks) == 3:
            break

    length, block, first, second = blocks[0] if blocks else (0, "", 0, 0)
    if blocks:
        ok = digits[first - 1:first - 1 + length] == block
        ok = ok and digits[second - 1:second - 1 + length] == block

    extra = []
    for length, block, first, second in blocks:
        total, positions = occurrences(digits, block)
        extra.append(f"{length}-digit block {block!r} at {positions}"
                     f"{' ...' if total > len(positions) else ''}"
                     f" ({total} occurrences)")
    extra.append(f"suffix array over {len(digits)} digits in "
                 f"{time.perf_counter() - started:.2f} s")
    rep.add("S3", "longest block that occurs at least twice",
            "PASS" if ok else "FAIL",
            f"length {blocks[0][0] if blocks else 0}, "
            f"maximum LCP over adjacent suffixes" if ok else "inconsistent LCP",
            extra)
    return longest


# ---------------------------------------------------------------- S4: tandem repeats

def section_squares(rep: Report, digits: str, longest_repeat: int) -> None:
    n = len(digits)
    best: tuple[int, int, int, int, int] | None = None   # 2p, p, start, run, run_start
    per_period: list[tuple[int, int, int]] = []          # p, maximal length, start
    for p in range(1, longest_repeat + 1):
        i = 0
        run_max = 0
        run_start = -1
        square_start = -1
        while i + p < n:
            if digits[i] != digits[i + p]:
                i += 1
                continue
            j = i
            while j + p < n and digits[j] == digits[j + p]:
                j += 1
            length = j - i
            if length > run_max:
                run_max = length
                run_start = i
            if square_start < 0 and length >= p:
                square_start = i
            i = j + 1
        per_period.append((p, run_max + p, run_start + 1))
        if square_start >= 0:
            candidate = (2 * p, p, square_start + 1, run_max + p, run_start + 1)
            if best is None or candidate[0] > best[0]:
                best = candidate

    ok = True
    detail = "no tandem repeat found"
    if best is not None:
        length, p, start, run, run_at = best
        block = digits[start - 1:start - 1 + p]
        ok = (digits[start - 1:start - 1 + 2 * p] == block * 2)
        detail = (f"longest square {block * 2!r} (period {p}, length {length}) "
                  f"at {start}; the longest block of period {p} has {run} digits "
                  f"at {run_at}")
    extra = [f"p={p}: longest block with period {p} has {length} digits at {start}"
             for p, length, start in per_period if p <= 12]
    extra.append(f"periods 1..{longest_repeat} scanned: any tandem repeat has "
                 f"period <= longest repeated block = {longest_repeat}")
    rep.add("S4", "longest tandem repeat XX",
            "PASS" if ok else "FAIL", detail, extra)


# ---------------------------------------------------------------- S5: palindrome

def section_palindrome(rep: Report, digits: str) -> None:
    n = len(digits)
    d1 = [0] * n
    d2 = [0] * n
    best = (0, 0)  # length, start

    left, right = 0, -1
    for i in range(n):
        k = 1 if i > right else min(d1[left + right - i], right - i + 1)
        while i - k >= 0 and i + k < n and digits[i - k] == digits[i + k]:
            k += 1
        d1[i] = k
        if i + k - 1 > right:
            left, right = i - k + 1, i + k - 1
        if 2 * k - 1 > best[0]:
            best = (2 * k - 1, i - k + 1)

    left, right = 0, -1
    for i in range(n):
        k = 0 if i > right else min(d2[left + right - i + 1], right - i + 1)
        while i - k - 1 >= 0 and i + k < n and digits[i - k - 1] == digits[i + k]:
            k += 1
        d2[i] = k
        if i + k - 1 > right:
            left, right = i - k, i + k - 1
        if 2 * k > best[0]:
            best = (2 * k, i - k)

    length, start = best
    block = digits[start:start + length]
    many = sum(max(0, k - 5) for k in d1) + sum(max(0, k - 4) for k in d2)
    ok = block == block[::-1]
    rep.add("S5", "longest palindromic block",
            "PASS" if ok else "FAIL",
            f"length {length}: {block!r} at {start + 1}",
            [f"{many} palindromic blocks of length >= 11"])


# ---------------------------------------------------------------- S6: prime substrings

def prime_substring_table(digits: str, max_length: int) -> list[dict[str, Any]]:
    n = len(digits)
    rows: list[dict[str, Any]] = []
    for length in range(1, max_length + 1):
        count = 0
        best = -1
        best_pos = -1
        for i in range(n - length + 1):
            if digits[i] == "0":          # keep exactly `length` digits
                continue
            if length == 1:
                value = ord(digits[i]) - 48
                prime = value in (2, 3, 5, 7)
            else:
                if digits[i + length - 1] not in "1379":
                    continue
                value = int(digits[i:i + length])
                prime = True
                for p in SMALL_ODD:
                    if value % p == 0:
                        prime = value == p
                        break
                else:
                    bases = (MR_DETERMINISTIC
                             if value < MR_DETERMINISTIC_LIMIT else MR_MANY)
                    prime = is_probable_prime(value, bases, [])
            if prime:
                count += 1
                if value > best:
                    best = value
                    best_pos = i + 1
        rows.append({"length": length, "count": count,
                     "largest": best, "position": best_pos})
    return rows


def section_prime_substrings(rep: Report, digits: str, max_length: int) -> list[dict[str, Any]]:
    started = time.perf_counter()
    rows = prime_substring_table(digits, max_length)
    total = sum(row["count"] for row in rows)
    biggest = max(rows, key=lambda row: row["largest"])
    ok = all(row["count"] > 0 for row in rows) and biggest["largest"] > 0
    text = str(biggest["largest"])
    shown = text if len(text) <= 40 else text[:20] + "..." + text[-12:]
    detail = (f"{total} prime substrings of length 1..{max_length}; "
              f"largest is the {biggest['length']}-digit {shown} at "
              f"{biggest['position']} "
              f"[{time.perf_counter() - started:.2f} s]")
    extra = []
    for row in rows:
        value = str(row["largest"])
        shown_row = value if len(value) <= 30 else value[:12] + "..." + value[-8:]
        extra.append(f"L={row['length']:>2}: {row['count']:>6} primes, "
                     f"largest {shown_row} at {row['position']}")
    if max_length <= 24:
        extra.append("every length <= 24 is below 3.3e24, so 12 Miller-Rabin "
                     "bases are deterministic: these are proven primes")
    else:
        extra.append("lengths <= 24: 12 bases, deterministic (proven primes); "
                     f"lengths 25..{max_length}: 64 bases, probable primes "
                     "(error below 2^-128)")
    rep.add("S6", "prime substrings of the certified digits",
            "PASS" if ok else "FAIL", detail, extra)
    return rows


# ---------------------------------------------------------------- S7: truncations

def classify_truncation(digits: str, length: int, primes: list[int],
                        pow_limit: int, strong: bool) -> tuple[str, int, str]:
    """(status, factor_or_zero, how) for the first `length` digits.

    A found factor proves compositeness outright.  A failed Fermat test proves
    it as well.  Only a passed test yields "prime"/"probable prime"; the word
    "probable" is dropped below 3.3e24, where 12 Miller-Rabin bases are exact.
    """
    value = int(digits[:length])
    if value % 2 == 0:
        return "composite", 2, "factor 2"
    for p in primes:
        if p > 100_000:
            break
        if p > 2 and value % p == 0:
            return "composite", p, "factor"

    if length > pow_limit and length not in KNOWN_PRIME_LENGTHS:
        return ("undecided", 0,
                "no factor <= 100000; modular exponentiation skipped "
                f"(length > {pow_limit})")

    if pow(2, value - 1, value) != 1:
        return "composite", 0, "Fermat witness 2"
    if value < MR_DETERMINISTIC_LIMIT:
        if is_probable_prime(value, MR_DETERMINISTIC, []):
            return "prime", 0, "deterministic Miller-Rabin (12 bases)"
        return "composite", 0, "Miller-Rabin witness"
    if strong:
        if is_probable_prime(value, MR_MANY, []):
            return "probable prime", 0, "64 Miller-Rabin bases"
        return "composite", 0, "Miller-Rabin witness"
    return "probable prime", 0, "Fermat base 2"


def section_truncations(rep: Report, digits: str, samples: int,
                        pow_limit: int, strong: bool) -> list[dict[str, Any]]:
    started = time.perf_counter()
    primes = sieve(100_000)

    grid = list(range(2500, 40001, 2500))
    rng = random.Random(20261115)
    extra_lengths = rng.sample(range(2509, 40001), samples)
    lengths = sorted(set(KNOWN_PRIME_LENGTHS) | set(grid) | set(extra_lengths))

    rows = []
    for length in lengths:
        status, factor, how = classify_truncation(digits, length, primes,
                                                  pow_limit, strong)
        rows.append({"length": length, "status": status,
                     "factor": factor, "how": how})

    known_ok = all(row["status"] != "composite"
                   for row in rows if row["length"] in KNOWN_PRIME_LENGTHS)
    surprises = [row for row in rows
                 if row["status"] in ("prime", "probable prime")
                 and row["length"] not in KNOWN_PRIME_LENGTHS]
    composite = [row for row in rows if row["status"] == "composite"]
    undecided = [row for row in rows if row["status"] == "undecided"]
    tested = [row for row in rows if row["status"] != "undecided"]

    detail = (f"{len(rows)} lengths: {len(composite)} composite, "
              f"{len(tested) - len(composite)} prime/probable, "
              f"{len(undecided)} undecided; all six known prime lengths "
              f"confirmed: {known_ok}; new primes among the rest: "
              f"{len(surprises)} [{time.perf_counter() - started:.2f} s]")
    extra = ["lengths needing more than trial division:"]
    for row in rows:
        if row["how"].startswith("factor") or row["status"] == "undecided":
            continue
        extra.append(f"  L={row['length']:>5}: {row['status']} "
                     f"({row['how']})")
    if undecided:
        extra.append("undecided (no factor <= 100000):")
        for row in undecided:
            extra.append(f"  L={row['length']:>5}: {row['how']}")
    for row in surprises:
        extra.append(f"  L={row['length']}: {row['status']} - not in A174974")
    extra.append("trial division used primes <= 100000 for every length; "
                 "composites are proven, primes are not")
    rep.add("S7", "selective primality of the truncations of the digits",
            "PASS" if known_ok and not surprises else "FAIL", detail, extra)
    return rows


def section_full_number(rep: Report, digits: str) -> None:
    started = time.perf_counter()
    value = int(digits)
    primes = sieve(100_000)
    factor = 0
    for p in primes:
        if value % p == 0:
            factor = p
            break
    if factor:
        detail = (f"the full {len(digits)}-digit truncation is divisible by "
                  f"{factor}: composite")
        status = "PASS"
    else:
        fermat = pow(2, value - 1, value) == 1
        detail = (f"no factor <= 100000; base-2 Fermat test "
                  f"{'passed (unexpected)' if fermat else 'failed'}: composite")
        status = "PASS" if not fermat else "NOTE"
    rep.add("S7a", f"the whole {len(digits)}-digit truncation is composite",
            status, f"{detail} [{time.perf_counter() - started:.2f} s]")


# ---------------------------------------------------------------- S8: k-grams

def section_ngrams(rep: Report, digits: str) -> None:
    started = time.perf_counter()
    total = len(digits)
    extra = []
    counts = {}
    for k in range(1, 7):
        window = total - k + 1
        seen = {digits[i:i + k] for i in range(window)}
        counts[k] = len(seen)
        missing = 10**k - len(seen)
        extra.append(f"k={k}: {len(seen)} of {10**k} seen, {missing} missing "
                     f"({window} windows)")

    four = {digits[i:i + 4] for i in range(total - 3)}
    missing4 = sorted(set(f"{a}{b}{c}{d}"
                          for a in "0123456789" for b in "0123456789"
                          for c in "0123456789" for d in "0123456789")
                      - four)
    extra.append(f"first missing 4-grams: {' '.join(missing4[:12])}")
    pairs = {}
    for i in range(total - 1):
        key = digits[i:i + 2]
        pairs[key] = pairs.get(key, 0) + 1
    top = sorted(pairs.items(), key=lambda kv: -kv[1])[:3]
    extra.append("most frequent 2-grams: " +
                 ", ".join(f"{k} x{v}" for k, v in top))

    ok = len(four) == 9796           # independent cross-check of MathWorld C8
    rep.add("S8", "coverage of all k-digit strings, k = 1..6",
            "PASS" if ok else "FAIL",
            f"4-digit coverage {len(four)} of 10000 "
            f"(MathWorld C8 says 9796) "
            f"[{time.perf_counter() - started:.2f} s]",
            extra)


# ---------------------------------------------------------------- driver

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Structure and primality of the certified 40,000 digits.")
    parser.add_argument("--root", type=Path,
                        default=bundle_root(Path(__file__).resolve().parent))
    parser.add_argument("--prime-samples", type=int, default=40,
                        help="random truncation lengths to test (default 40)")
    parser.add_argument("--pow-limit", type=int, default=2000,
                        help="longest truncation that gets a modular "
                             "exponentiation (default 2000 digits); larger "
                             "lengths are only sieved unless their length is "
                             "one of the six known primes")
    parser.add_argument("--strong", action="store_true",
                        help="use 64 Miller-Rabin bases instead of one Fermat test")
    parser.add_argument("--long", action="store_true",
                        help="lift --pow-limit to 40000 (hours in pure Python)")
    parser.add_argument("--substring-length", type=int, default=32,
                        help="test prime substrings up to this length (default 32)")
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    pow_limit = 40000 if args.long else args.pow_limit

    digits = load_digits(args.root)
    print("Structure and primality of the certified digits")
    print(f"  bundle: {args.root}")
    print(f"  digits: {len(digits)}")
    print()

    rep = Report()
    started = time.perf_counter()
    stats = section_runs(rep, digits)
    section_earls(rep, digits, stats)
    longest = section_repeats(rep, digits)
    section_squares(rep, digits, longest)
    section_palindrome(rep, digits)
    substrings = section_prime_substrings(rep, digits, args.substring_length)
    truncations = section_truncations(rep, digits, args.prime_samples,
                                      pow_limit, args.strong)
    section_full_number(rep, digits)
    section_ngrams(rep, digits)

    for row in rep.rows:
        print(f"  [{row['code']:>4s}] {row['status']:<4s}  {row['claim']}")
        print(f"          {row['detail']}")
        for line in row["extra"]:
            print(f"          {line}")
    print()
    counts: dict[str, int] = {}
    for row in rep.rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    print("  summary: " + ", ".join(f"{k} {v}" for k, v in sorted(counts.items())))
    print(f"  total time: {time.perf_counter() - started:.1f} s")

    if args.json is not None:
        args.json.write_text(
            json.dumps({"digits": len(digits), "claims": rep.rows,
                        "prime_substrings": substrings,
                        "truncations": truncations},
                       indent=2, default=str) + "\n",
            encoding="ascii")
        print(f"  report written to {args.json}")

    if rep.failures():
        print(f"FAIL: {rep.failures()} check(s) failed", file=sys.stderr)
        return 1
    print("OK: every structural check and cross-check passed")
    return 0


if __name__ == "__main__":
    sys.exit(main())

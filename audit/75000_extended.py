#!/usr/bin/env python3
"""Read-only extended MathWorld checks for the 75,000-digit certificate.

Usage:
    python audit/75000_extended.py --digits PATH --oeis-dir PATH \
        --max-seconds 300 --json PATH

The script never writes to the repository.  Primality beyond the published
6, 27, 57, 60, 1659, 2508 lengths is *sampled*, not exhaustive: a fast
small-prime sieve discards composites, then Fermat base 2 and (for passing
candidates) Miller-Rabin / BPSW are applied to a bounded number of lengths
within --max-seconds.  No APRCL/ECPP certificate is produced.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import time
from pathlib import Path

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)


def small_primes(limit: int) -> list[int]:
    sieve = bytearray([1]) * (limit + 1)
    sieve[:2] = b"\x00\x00"
    for i in range(2, int(limit**0.5) + 1):
        if sieve[i]:
            sieve[i * i :: i] = b"\x00" * (((limit - i * i) // i) + 1)
    return [i for i, v in enumerate(sieve) if v]


def prefix_candidates(digits: str, primes: list[int]) -> list[int]:
    """Lengths n (1-based) whose prefix is not divisible by any small prime."""
    residues = [0] * len(primes)
    candidates: list[int] = []
    for n, ch in enumerate(digits, 1):
        d = ord(ch) - 48
        for i, p in enumerate(primes):
            residues[i] = (residues[i] * 10 + d) % p
        if all(r != 0 for r in residues):
            candidates.append(n)
    return candidates


def probable_prime(n: int, deadline: float) -> dict[str, object]:
    """Fermat base 2, then a few MR bases and BPSW if time allows."""
    if n < 2:
        return {"fermat2": False}
    started = time.monotonic()
    if pow(2, n - 1, n) != 1:
        return {"fermat2": False, "seconds": round(time.monotonic() - started, 3)}
    result: dict[str, object] = {"fermat2": True}
    for base in (3, 5, 7):
        if time.monotonic() > deadline:
            break
        d, s = n - 1, 0
        while d % 2 == 0:
            d //= 2
            s += 1
        x = pow(base, d, n)
        if x in (1, n - 1):
            continue
        for _ in range(s - 1):
            x = x * x % n
            if x == n - 1:
                break
        else:
            result["miller_rabin"] = False
            break
    else:
        result["miller_rabin"] = True
    if time.monotonic() <= deadline:
        try:
            import sympy

            result["bpsw"] = bool(sympy.isprime(n))
        except Exception as exc:  # pragma: no cover - optional dependency
            result["bpsw"] = f"not run: {type(exc).__name__}"
    result["seconds"] = round(time.monotonic() - started, 3)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--digits", type=Path, required=True)
    parser.add_argument("--oeis-dir", type=Path, default=Path("verification/reports/oeis"))
    parser.add_argument("--max-seconds", type=float, default=300.0)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    raw = args.digits.read_bytes()
    digits = raw.decode("ascii").strip()
    deadline = time.monotonic() + args.max_seconds
    report: dict[str, object] = {
        "input": str(args.digits),
        "digit_count": len(digits),
        "sha256_canonical": hashlib.sha256((digits + "\n").encode()).hexdigest(),
        "sha256_as_read": hashlib.sha256(raw).hexdigest(),
        "sampled": True,
    }

    # 1. Pandigital / repeated patterns over the whole 75,000 digits.
    patterns = ["0123456789", "9876543210", "55555", "666666", "77777", "88888", "99999"]
    report["patterns"] = {
        p: {"first_15000": digits[:15000].find(p), "whole": digits.find(p)}
        for p in patterns
    }

    # 2. A225242: first run of d copies of digit d, for d = 1..9.
    earls: dict[int, int] = {}
    for d in range(1, 10):
        needle = str(d) * d
        pos = digits.find(needle)
        earls[d] = pos + 1 if pos >= 0 else None  # 1-based
    earls_ref: dict[int, int] = {}
    ref = args.oeis_dir / "b225242.txt"
    if ref.is_file():
        for line in ref.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 2 and not parts[0].startswith("#"):
                earls_ref[int(parts[0])] = int(parts[1])
    report["earls"] = {
        "computed_1based": earls,
        "oeis_a225242": earls_ref,
        "first_four_match": all(earls[d] == earls_ref.get(d) for d in range(1, 5)),
    }

    # 3. A229195: first position of n = 0..999 in the expansion.
    positions: dict[int, int] = {}
    for n in range(1000):
        pos = digits.find(str(n))
        positions[n] = pos + 1 if pos >= 0 else None
    a229195: dict[int, int] = {}
    ref = args.oeis_dir / "b229195.txt"
    if ref.is_file():
        for line in ref.read_text(encoding="utf-8").splitlines():
            parts = line.split()
            if len(parts) == 2 and not parts[0].startswith("#"):
                a229195[int(parts[0])] = int(parts[1])
    mismatches = [n for n, v in a229195.items() if positions.get(n) != v]
    report["a229195"] = {
        "checked_terms": len(a229195),
        "mismatches": mismatches[:20],
        "match": not mismatches,
    }

    # 4. Digit counts for the prefixes quoted by MathWorld and for 75,000.
    report["digit_counts"] = {
        str(k): [digits[:k].count(str(d)) for d in range(10)]
        for k in (10, 100, 1000, 10000, len(digits))
    }

    # 5. Primality of the whole 75,000-digit prefix: small factors first.
    primes = small_primes(1000)
    whole = int(digits)
    factor = next((p for p in primes if whole % p == 0), None)
    report["whole_number"] = {
        "last_digit": digits[-1],
        "small_factor": factor,
        "composite": factor is not None,
    }

    # 6. Prime truncations beyond 2,508: small-prime filter + sampled tests.
    candidates = [n for n in prefix_candidates(digits, primes) if n > 2508]
    report["candidates_after_2508"] = {
        "count": len(candidates),
        "first_20": candidates[:20],
        "method": "not divisible by any of the first 168 primes",
    }
    if candidates:
        step = max(1, len(candidates) // 10)
        sample = candidates[::step][:10]
        if candidates[0] not in sample:
            sample.insert(0, candidates[0])
        found: list[dict[str, object]] = []
        prefix = int(digits[: candidates[0] - 1]) if candidates[0] > 1 else 0
        cursor = candidates[0] - 1
        for n in candidates:
            if time.monotonic() > deadline:
                break
            while cursor < n:
                prefix = prefix * 10 + (ord(digits[cursor]) - 48)
                cursor += 1
            if n not in sample:
                continue
            verdict = probable_prime(prefix, deadline)
            found.append({"length": n, **verdict})
        report["prime_truncations_sampled"] = found
    report["seconds"] = round(time.monotonic() - (deadline - args.max_seconds), 2)

    text = json.dumps(report, indent=2, ensure_ascii=False)
    print(text[:12000])
    if args.json is not None:
        args.json.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

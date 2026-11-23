#!/usr/bin/env python3
"""Level A: verify the published certificate without recomputing anything.

This checker is deliberately small and self-contained.  It reads only

    golomb_dickman_40000_certified.txt
    golomb_dickman_40000_digits.txt
    b084945.txt

and uses only the Python standard library and exact integer arithmetic.
It does **not** import the producing program, does not read checkpoint
pickles, and does not use floating point anywhere.

What it establishes
-------------------
1. The three input files have the pinned SHA-256 digests.
2. The certificate parses to integers S, lam_lo, lam_hi with
   0 < lam_lo < lam_hi.
3. The interval [lam_lo, lam_hi] / 2^S does not cross a decimal cell:
   floor(10^D lam_lo / 2^S) == floor(10^D lam_hi / 2^S).
4. That common value, written with D digits, is the published digit
   string, and the standalone digits file is the same string.
5. The width satisfies (lam_hi - lam_lo) * 10^D < 2^S, i.e. the
   interval is narrower than one unit in the D-th decimal place.
6. The b-file has exactly D terms, indexed 0..D-1, each equal to the
   corresponding digit, plain ASCII, LF only, with a trailing blank line.
7. The first 102 digits equal the published prefix of OEIS A084945.

What it does not establish
--------------------------
It does not prove that lam really lies in the interval.  That is the
content of the producing computation (Level C) and of the mathematical
audit (Level B).  This checker verifies that the published artefacts are
internally consistent and that the digits are the correct truncation of
the published interval.

Usage
-----
    python verify_40000.py
    python verify_40000.py --root ../40000
    python verify_40000.py --json report.json
    python verify_40000.py --quiet

Exit code 0 means every check passed; 1 means at least one failed.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(200_000)

EXPECTED_D = 40_000

CERT_NAME = "golomb_dickman_40000_certified.txt"
DIGITS_NAME = "golomb_dickman_40000_digits.txt"
BFILE_NAME = "b084945.txt"

EXPECTED_SHA256 = {
    CERT_NAME: "8892c0715f1afbb271c9f07cc9658cea0f3ca83c2dda3ec7d23b447dc908de9c",
    DIGITS_NAME: "fbae757900983bd4fb6421c5f27bf9602af1a1bfc013e4c501bb9da2b5a65327",
    BFILE_NAME: "c73af643198da299d2e624e3c2f69d05439efcddbbefa7cec176ac63f993bed3",
}

KNOWN_PREFIX = (
    "6243299885435508709929363831008372441796426201805292869735519024"
    "95638088855113254462460276195539868869"
)


class CheckError(Exception):
    """A failed check, reported without a traceback."""


def _configure_stdio() -> None:
    """Never fail on a console that cannot encode a path (cp866/cp1251)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

def fail(message: str) -> None:
    raise CheckError(message)


def _normalise_lf(raw: bytes) -> bytes:
    """Canonical LF bytes: CRLF -> LF.  Bare CR is preserved for the check."""
    return raw.replace(b"\r\n", b"\n")


def sha256_file(path: Path) -> str:
    """SHA-256 of the file after LF normalisation.

    The published digest is defined over canonical LF bytes.  Hashing the raw
    bytes makes a Windows checkout with core.autocrlf=true fail even though
    the content is identical; that was the CRLF gap this build closes.
    """
    digest = hashlib.sha256()
    digest.update(_normalise_lf(path.read_bytes()))
    return digest.hexdigest()


def line_ending_report(path: Path) -> str:
    raw = path.read_bytes()
    crlf = raw.count(b"\r\n")
    cr = raw.count(b"\r") - crlf
    if cr:
        return f"CR x{cr} (mixed/bare CR)"
    if crlf:
        return f"CRLF x{crlf} (normalised to LF for hashing)"
    return "LF"


def read_ascii(path: Path, strict_lf: bool = False) -> str:
    raw = path.read_bytes()
    if strict_lf and b"\r" in raw:
        fail(f"{path.name}: contains CR (canonical form is LF only)")
    raw = _normalise_lf(raw)
    if raw.startswith(b"\xef\xbb\xbf"):
        fail(f"{path.name}: UTF-8 BOM is not allowed")
    if b"\x00" in raw:
        fail(f"{path.name}: NUL byte found")
    try:
        return raw.decode("ascii")
    except UnicodeDecodeError as exc:
        fail(f"{path.name}: not plain ASCII ({exc})")


def resolve_paths(start: Path) -> tuple[Path, Path, Path]:
    """Locate the three artefacts, in the repository or in the exported bundle.

    Repository layout puts everything in ``40000/``; the verification bundle
    puts the certificate in ``certificate/`` and the digit strings in
    ``digits/``.
    """
    candidates = [start, start / "40000", start.parent / "40000"]
    candidates += [*start.parents]
    candidates += [parent / "40000" for parent in start.parents]
    for candidate in candidates:
        if all((candidate / name).is_file() for name in EXPECTED_SHA256):
            return candidate / CERT_NAME, candidate / DIGITS_NAME, candidate / BFILE_NAME
    for base in (start, *start.parents):
        cert = base / "certificate" / CERT_NAME
        digits = base / "digits" / DIGITS_NAME
        bfile = base / "digits" / BFILE_NAME
        if cert.is_file() and digits.is_file() and bfile.is_file():
            return cert, digits, bfile
    fail(f"cannot find {CERT_NAME}, {DIGITS_NAME} and {BFILE_NAME} near {start}")
    raise AssertionError("unreachable")  # pragma: no cover


def parse_certificate(path: Path, strict_lf: bool = False) -> tuple[int, int, int, str]:
    text = read_ascii(path, strict_lf=strict_lf)
    lines = text.splitlines()
    if len(lines) < 4:
        fail(f"{path.name}: expected at least 4 lines, found {len(lines)}")

    match_s = re.search(r"\bS=(\d+)\b", lines[1])
    match_lo = re.search(r"\blam_lo=(\d+)\b", lines[1])
    match_hi = re.search(r"\blam_hi=(\d+)\b", lines[2])
    if not (match_s and match_lo and match_hi):
        fail(f"{path.name}: cannot parse S, lam_lo or lam_hi")

    scale_bits = int(match_s.group(1))
    lam_lo = int(match_lo.group(1))
    lam_hi = int(match_hi.group(1))

    if not (0 < lam_lo < lam_hi):
        fail(f"{path.name}: expected 0 < lam_lo < lam_hi")
    if not (EXPECTED_D * 3 < scale_bits < EXPECTED_D * 4):
        fail(f"{path.name}: S={scale_bits} is implausible for D={EXPECTED_D}")
    if not (lam_lo.bit_length() > scale_bits - 4):
        fail(f"{path.name}: lam_lo is not on the expected scale")

    digits_line = lines[3].strip()
    if not digits_line.startswith("0."):
        fail(f"{path.name}: fourth line must start with '0.'")
    digits = digits_line[2:]
    if len(digits) != EXPECTED_D:
        fail(f"{path.name}: expected {EXPECTED_D} digits, found {len(digits)}")
    if not digits.isdigit():
        fail(f"{path.name}: digit line contains a non-digit character")

    return scale_bits, lam_lo, lam_hi, digits


def decimal_position(width: int, scale_bits: int) -> tuple[int, str]:
    """Return k and a mantissa with width ~ mantissa * 10^-k.

    Uses exact integer comparisons only (no floats).  k is the smallest
    integer with width * 10^k >= 2^scale_bits, so
    10^-k <= width / 2^scale_bits < 10^(1-k).
    """
    two_s = 1 << scale_bits

    def reaches(k: int) -> bool:
        return width * 10**k >= two_s

    lo, hi = 0, scale_bits  # reaches(hi) is certainly true
    if not reaches(hi):
        fail("internal: width bound search failed")
    while lo < hi:
        mid = (lo + hi) // 2
        if reaches(mid):
            hi = mid
        else:
            lo = mid + 1
    k = lo
    # Mantissa with three decimals: floor(width * 10^k * 1000 / 2^S) / 1000
    milli = (width * 10**k * 1000) // two_s
    whole, frac = divmod(milli, 1000)
    if whole < 1 or whole > 9:
        fail("internal: mantissa out of range")
    return k, f"{whole}.{frac:03d}"


def check_bundle(
    cert_path: Path,
    digits_path: Path,
    bfile_path: Path,
    verify_hashes: bool = True,
    strict_lf: bool = False,
) -> dict[str, object]:
    paths = {CERT_NAME: cert_path, DIGITS_NAME: digits_path, BFILE_NAME: bfile_path}

    for path in (cert_path, digits_path, bfile_path):
        if not path.is_file():
            fail(f"missing file: {path}")

    hashes = {}
    endings = {}
    for name, expected in EXPECTED_SHA256.items():
        actual = sha256_file(paths[name])
        hashes[name] = actual
        endings[name] = line_ending_report(paths[name])
        if verify_hashes and actual != expected:
            fail(f"{name}: SHA-256 mismatch (expected {expected}, got {actual})")
    if strict_lf:
        for path in (cert_path, digits_path, bfile_path):
            if b"\r" in path.read_bytes():
                fail(f"{path.name}: contains CR; --strict-lf forbids it")

    scale_bits, lam_lo, lam_hi, cert_digits = parse_certificate(
        cert_path, strict_lf=strict_lf)

    scale = 10**EXPECTED_D
    lower = (lam_lo * scale) >> scale_bits
    upper = (lam_hi * scale) >> scale_bits
    if lower != upper:
        fail("the certified interval crosses a decimal boundary")

    proven = str(lower).zfill(EXPECTED_D)
    if proven != cert_digits:
        fail("certificate digits are not floor(10^D * lam_lo / 2^S)")

    standalone = read_ascii(digits_path, strict_lf=strict_lf).strip()
    if standalone != cert_digits:
        fail("digits file and certificate disagree")

    width = lam_hi - lam_lo
    if width * scale >= (1 << scale_bits):
        fail("interval width is not smaller than one unit in the D-th decimal place")
    k, mantissa = decimal_position(width, scale_bits)
    # width < 10^(1-k) = 10^(-(k-1)), so k-1-D extra digits are certain.
    guard_digits = k - 1 - EXPECTED_D

    btext = read_ascii(bfile_path, strict_lf=strict_lf)
    if "\t" in btext:
        fail("b-file contains a tab character")
    if not btext.endswith("\n\n"):
        fail("b-file does not end with a blank line")

    terms: list[tuple[int, int]] = []
    for line_number, line in enumerate(btext.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 2:
            fail(f"b-file line {line_number}: expected 'n value', got {line!r}")
        try:
            index, value = int(parts[0]), int(parts[1])
        except ValueError:
            fail(f"b-file line {line_number}: non-integer term")
        terms.append((index, value))

    if len(terms) != EXPECTED_D:
        fail(f"b-file has {len(terms)} terms, expected {EXPECTED_D}")
    for position, (index, value) in enumerate(terms):
        if index != position:
            fail(f"b-file index {index} at position {position}")
        if value != int(cert_digits[position]):
            fail(f"b-file term a({index}) does not match the certificate")

    if cert_digits[: len(KNOWN_PREFIX)] != KNOWN_PREFIX:
        fail("first 102 digits do not match OEIS A084945")

    return {
        "digits": EXPECTED_D,
        "scale_bits": scale_bits,
        "lam_lo": str(lam_lo),
        "lam_hi": str(lam_hi),
        "width_digits": len(str(width)),
        "width_log10_exponent": -k,
        "width_mantissa": mantissa,
        "guard_digits": guard_digits,
        "b_file_terms": len(terms),
        "sha256": hashes,
        "line_endings": endings,
        "line_ending_policy": "hash over LF-normalised bytes",
        "prefix_oeis": KNOWN_PREFIX,
    }


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(
        description="Level A: verify the 40,000-digit certificate (standard library only).",
    )
    parser.add_argument(
        "--root",
        type=Path,
        default=None,
        help="directory containing the three artefacts (default: search upward)",
    )
    parser.add_argument("--json", type=Path, default=None, help="write a JSON report here")
    parser.add_argument("--quiet", action="store_true", help="print only the final verdict")
    parser.add_argument(
        "--no-hash",
        action="store_true",
        help="do not require the pinned SHA-256 values (still prints them)",
    )
    parser.add_argument(
        "--strict-lf",
        action="store_true",
        help="also require canonical LF bytes on disk (CRLF is hashed "
             "correctly but rejected)",
    )
    args = parser.parse_args(argv)

    cert_path, digits_path, bfile_path = resolve_paths(
        args.root.resolve() if args.root else Path(__file__).resolve().parent
    )
    try:
        report = check_bundle(cert_path, digits_path, bfile_path,
                              verify_hashes=not args.no_hash,
                              strict_lf=args.strict_lf)
    except CheckError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"OK: {report['digits']} digits certified (Level A)")
        print(f"  certificate: {cert_path.parent.name}/{cert_path.name}")
        print(f"  scale: lam_lo/2^{report['scale_bits']} .. lam_hi/2^{report['scale_bits']}")
        print(
            "  width: "
            f"{report['width_mantissa']} x 10^{report['width_log10_exponent']}"
            f"  (< 10^{report['width_log10_exponent'] + 1}),"
            f" {report['guard_digits']} guard digits beyond the 40000th place"
        )
        print(f"  b-file: {report['b_file_terms']} terms, indices 0..{report['b_file_terms'] - 1}")
        print("  first 102 digits match OEIS A084945")
        if args.no_hash:
            print("  SHA-256: computed only, UNVERIFIED (--no-hash):")
        else:
            print("  SHA-256: MATCH (pinned in this script):")
        for name, digest in report["sha256"].items():
            print(f"    {digest}  {name}  [{report['line_endings'][name]}]")

    if args.json is not None:
        args.json.write_text(
            json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
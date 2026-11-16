#!/usr/bin/env python3
"""Level A for any digit count: verify a Golomb-Dickman interval certificate.

The certificate is a four-line text file:

    # comment
    # S=<bits> lam_lo=<integer>
    # lam_hi=<integer>
    0.<D digits>

This script checks, using only the standard library and exact integers:

 1. the certificate is plain ASCII with LF endings and no BOM;
 2. 0 < lam_lo < lam_hi and S is on the scale implied by D;
 3. floor(10^D lam_lo / 2^S) == floor(10^D lam_hi / 2^S), i.e. the
    interval does not cross a decimal cell;
 4. the fourth line equals that common value, and the standalone digits
    file equals it as well;
 5. (lam_hi - lam_lo) * 10^D < 2^S, i.e. the width is below one unit in
    the D-th decimal place; the guaranteed guard digits are reported;
 6. an optional b-file has exactly D terms, n = 0..D-1, each equal to the
    corresponding digit, LF only, trailing blank line;
 7. the first 102 digits equal the published prefix of OEIS A084945;
 8. optionally, the digits agree with a reference file (prefix comparison),
    and the SHA-256 of each input matches a pinned value.

It does not prove that lambda lies in the interval; that is the content of
the producing computation and of the mathematical audit.

Usage
-----
    python verify_certificate.py --cert ../50000/golomb_dickman_50000_certified.txt
    python verify_certificate.py --cert ... --bfile ... --compare ../40000/golomb_dickman_40000_digits.txt
    python verify_certificate.py --cert ... --sha256 76f4... --json report.json
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)

KNOWN_PREFIX = (
    "6243299885435508709929363831008372441796426201805292869735519024"
    "95638088855113254462460276195539868869"
)


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


class CheckError(Exception):
    pass


def fail(message: str) -> None:
    raise CheckError(message)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def write_report(path: Path, text: str) -> Path:
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path
    except OSError as exc:
        fallback = Path(tempfile.gettempdir()) / path.name
        fallback.write_text(text, encoding="utf-8", newline="\n")
        print(f"note: cannot write {path} ({exc}); saved {fallback}", file=sys.stderr)
        return fallback


def read_ascii_lf(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        fail(f"{path.name}: UTF-8 BOM is not allowed")
    if b"\x00" in raw:
        fail(f"{path.name}: NUL byte found")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        fail(f"{path.name}: not plain ASCII ({exc})")
    if "\r" in text:
        fail(f"{path.name}: contains CR (canonical form is LF only)")
    return text


def parse_certificate(path: Path) -> tuple[int, int, int, str]:
    lines = read_ascii_lf(path).splitlines()
    if len(lines) < 4:
        fail(f"{path.name}: expected at least 4 lines, found {len(lines)}")

    first = lines[0]
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

    digits_line = lines[3].strip()
    if not digits_line.startswith("0."):
        fail(f"{path.name}: fourth line must start with '0.'")
    digits = digits_line[2:]
    if not digits.isdigit():
        fail(f"{path.name}: digit line contains a non-digit character")

    # The filename usually carries the digit count; use it as a cross-check.
    match_name = re.search(r"(\d{4,})", path.name)
    if match_name and int(match_name.group(1)) != len(digits):
        fail(
            f"{path.name}: filename says {match_name.group(1)} digits, "
            f"certificate has {len(digits)}"
        )
    if not (len(digits) * 3 < scale_bits < len(digits) * 4):
        fail(f"{path.name}: S={scale_bits} is implausible for D={len(digits)}")
    if not (lam_lo.bit_length() >= scale_bits - 1):
        fail(f"{path.name}: lam_lo is not on the expected scale")

    return scale_bits, lam_lo, lam_hi, digits


def decimal_position(width: int, scale_bits: int) -> tuple[int, str]:
    """k and mantissa with width >= 10^-k, using exact integer comparisons."""
    two_s = 1 << scale_bits
    low, high = 0, scale_bits
    while low < high:
        mid = (low + high) // 2
        if width * 10**mid >= two_s:
            high = mid
        else:
            low = mid + 1
    k = low
    milli = (width * 10**k * 1000) // two_s
    whole, frac = divmod(milli, 1000)
    if whole < 1 or whole > 9:
        fail("internal: mantissa out of range")
    return k, f"{whole}.{frac:03d}"


def check_bfile(path: Path, digits: str) -> int:
    text = read_ascii_lf(path)
    if "\t" in text:
        fail(f"{path.name}: b-file contains a tab character")
    if not text.endswith("\n\n"):
        fail(f"{path.name}: b-file does not end with a blank line")
    terms = 0
    for line_number, line in enumerate(text.splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        parts = stripped.split()
        if len(parts) != 2:
            fail(f"{path.name} line {line_number}: expected 'n value', got {line!r}")
        try:
            index, value = int(parts[0]), int(parts[1])
        except ValueError:
            fail(f"{path.name} line {line_number}: non-integer term")
        if index != terms:
            fail(f"{path.name}: index {index} at position {terms}")
        if terms >= len(digits):
            fail(f"{path.name}: more than {len(digits)} terms")
        if value != int(digits[terms]):
            fail(f"{path.name}: term a({index}) does not match the digit string")
        terms += 1
    if terms != len(digits):
        fail(f"{path.name}: {terms} terms, expected {len(digits)}")
    return terms


def common_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    index = 0
    while index < limit and a[index] == b[index]:
        index += 1
    return index


def verify(
    cert_path: Path,
    digits_path: Path | None,
    bfile_path: Path | None,
    compare_path: Path | None,
    pinned: dict[str, str],
) -> dict[str, object]:
    scale_bits, lam_lo, lam_hi, cert_digits = parse_certificate(cert_path)
    D = len(cert_digits)

    scale = 10**D
    lower = (lam_lo * scale) >> scale_bits
    upper = (lam_hi * scale) >> scale_bits
    if lower != upper:
        fail("the certified interval crosses a decimal boundary")

    proven = str(lower).zfill(D)
    if proven != cert_digits:
        fail("certificate digits are not floor(10^D * lam_lo / 2^S)")

    hashes = {"certificate": sha256_file(cert_path)}
    if cert_path.name in pinned and hashes["certificate"] != pinned[cert_path.name]:
        fail(f"{cert_path.name}: SHA-256 mismatch (expected {pinned[cert_path.name]}, got {hashes['certificate']})")

    standalone = None
    if digits_path is not None:
        standalone = read_ascii_lf(digits_path).strip()
        if standalone != cert_digits:
            fail(f"{digits_path.name}: digits do not match the certificate")
        hashes["digits"] = sha256_file(digits_path)
        if digits_path.name in pinned and hashes["digits"] != pinned[digits_path.name]:
            fail(f"{digits_path.name}: SHA-256 mismatch")

    width = lam_hi - lam_lo
    if width * scale >= (1 << scale_bits):
        fail("interval width is not smaller than one unit in the D-th decimal place")
    k, mantissa = decimal_position(width, scale_bits)
    guard_digits = k - 1 - D

    terms = None
    if bfile_path is not None:
        terms = check_bfile(bfile_path, cert_digits)
        hashes["bfile"] = sha256_file(bfile_path)
        if bfile_path.name in pinned and hashes["bfile"] != pinned[bfile_path.name]:
            fail(f"{bfile_path.name}: SHA-256 mismatch")

    prefix_oeis = cert_digits[: len(KNOWN_PREFIX)] if D >= len(KNOWN_PREFIX) else None
    if prefix_oeis is not None and prefix_oeis != KNOWN_PREFIX:
        fail("first 102 digits do not match OEIS A084945")

    comparison = None
    if compare_path is not None:
        reference = compare_path.read_text(encoding="ascii").strip()
        matched = common_prefix(cert_digits, reference)
        comparison = {
            "file": str(compare_path),
            "reference_digits": len(reference),
            "common_prefix": matched,
        }
        if matched < min(len(reference), D):
            fail(
                f"digits disagree with {compare_path.name} after {matched} digits"
            )

    return {
        "digits": D,
        "scale_bits": scale_bits,
        "width_mantissa": mantissa,
        "width_exponent": -k,
        "guard_digits": guard_digits,
        "b_file_terms": terms,
        "oeis_prefix_checked": prefix_oeis is not None,
        "comparison": comparison,
        "sha256": hashes,
        "verdict": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(
        description="Verify a Golomb-Dickman interval certificate (any digit count)."
    )
    parser.add_argument("--cert", type=Path, required=True, help="certificate file")
    parser.add_argument("--digits-file", type=Path, default=None, help="standalone digits file")
    parser.add_argument("--bfile", type=Path, default=None, help="OEIS b-file to check")
    parser.add_argument("--compare", type=Path, default=None, help="reference digits file")
    parser.add_argument(
        "--sha256",
        action="append",
        default=[],
        metavar="NAME=HEX",
        help="pinned SHA-256 for an input file name (repeatable)",
    )
    parser.add_argument("--json", type=Path, default=None, help="write a JSON report")
    parser.add_argument("--quiet", action="store_true", help="print only the verdict")
    args = parser.parse_args(argv)

    pinned: dict[str, str] = {}
    for item in args.sha256:
        if "=" not in item:
            print(f"FAIL: --sha256 expects NAME=HEX, got {item!r}", file=sys.stderr)
            return 2
        name, value = item.split("=", 1)
        pinned[name] = value.strip().lower()

    cert_path = args.cert
    digits_path = args.digits_file
    bfile_path = args.bfile
    if digits_path is None:
        candidate = cert_path.with_name(cert_path.name.replace("_certified", "_digits"))
        digits_path = candidate if candidate.is_file() else None
    if bfile_path is None:
        candidate = cert_path.with_name("b084945.txt")
        bfile_path = candidate if candidate.is_file() else None

    try:
        report = verify(cert_path, digits_path, bfile_path, args.compare, pinned)
    except CheckError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if not args.quiet:
        print(f"OK: {report['digits']} digits certified")
        print(f"  certificate: {cert_path}")
        print(f"  scale: lam_lo/2^{report['scale_bits']} .. lam_hi/2^{report['scale_bits']}")
        print(
            f"  width: {report['width_mantissa']} x 10^{report['width_exponent']}"
            f"  ({report['guard_digits']} guard digits)"
        )
        if report["b_file_terms"] is not None:
            print(f"  b-file: {report['b_file_terms']} terms")
        else:
            print("  b-file: not provided (skipped)")
        print(f"  OEIS prefix: {'checked' if report['oeis_prefix_checked'] else 'skipped'}")
        if report["comparison"] is not None:
            comp = report["comparison"]
            print(
                f"  compared with {comp['file']}: "
                f"{comp['common_prefix']} leading digits agree"
            )
        print("  SHA-256: OK")

    if args.json is not None:
        write_report(args.json, json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

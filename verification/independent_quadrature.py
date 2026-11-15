#!/usr/bin/env python3
"""Level C: independent recomputation of the Golomb-Dickman constant.

lambda = 0.624329988543550870992936383100837...  (OEIS A084945)

Independence is deliberate and limited:

  * nothing is imported from the producing program -- no ``node_ball``,
    no checkpoint pickles, no certificate arithmetic;
  * the integral is evaluated with mpmath's tanh-sinh and Gauss-Legendre
    rules, not with Arb ball arithmetic;
  * the truncation point is derived in this file from the integrand bound,
    not copied from the certificate.

Formula
-------
    lambda = integral_0^inf exp(-u - E1(u)) du,

where E1 is the exponential integral.  Since E1(u) > 0 for u > 0,

    0 < exp(-u - E1(u)) <= exp(-u),

so the tail beyond U is smaller than exp(-U).  With U = (D + guard) ln 10
the neglected tail is below 10^-(D+guard).  The quadrature error itself is
controlled only numerically (two different rules must agree), therefore
this is *evidence*, not a proof.

What this does NOT do
---------------------
mpmath uses floating point.  A matching prefix of D digits is strong
numerical evidence that the published digits are right, but it is not an
interval proof.  The rigorous enclosure is the certificate in
``40000/golomb_dickman_40000_certified.txt``, whose re-audit requires Arb
(``40000/checks/verify_checkpoints_arb.py``).

Usage
-----
    python independent_quadrature.py --digits 1000
    python independent_quadrature.py --digits 1000 --jobs 12
    python independent_quadrature.py --digits 40000 --jobs 12

Exit code 0 means the two quadrature rules agreed to the requested number
of digits and the certified file matched as well (when it was found).
"""

from __future__ import annotations

import argparse
import json
import multiprocessing as mproc
import sys
import tempfile
import time
from pathlib import Path

SPLITS = (0.0, 1.0, 2.0, 4.0, 8.0, 16.0, 32.0, 64.0, 128.0)

CERT_CANDIDATES = (
    "golomb_dickman_40000_digits.txt",
)


def _configure_stdio() -> None:
    """Never fail on a console that cannot encode a path (cp866/cp1251)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

def write_report(path: Path, text: str) -> Path:
    """Write a report, falling back to the system temp dir if the tree is protected.

    Windows "controlled folder access" can deny python.exe write permission to
    Documents.  The report is then written to %TEMP% and the location is
    printed instead of losing the result.
    """
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path
    except OSError as exc:
        fallback = Path(tempfile.gettempdir()) / path.name
        fallback.write_text(text, encoding="utf-8", newline="\n")
        print(f"note: cannot write {path} ({exc}); saved {fallback}", file=sys.stderr)
        return fallback

def _piece(args: tuple[float, float, int, str]):
    """Integrate one panel.  Module level so that spawned workers can use it."""
    a, b, dps, method = args
    import mpmath as mpm

    mpm.mp.dps = dps
    return mpm.quad(lambda u: mpm.e ** (-u - mpm.e1(u)), [a, b], method=method)


def integrate(digits: int, method: str, jobs: int, guard: int):
    import mpmath as mp

    dps = digits + guard
    mp.mp.dps = dps
    upper = (digits + guard) * mp.log(10)
    edges = [mp.mpf(x) for x in SPLITS if x < float(upper)] + [upper]
    panels = list(zip(edges[:-1], edges[1:]))

    started = time.time()
    tasks = [(float(a), float(b), dps, method) for a, b in panels]
    if jobs > 1:
        ctx = mproc.get_context("spawn")
        with ctx.Pool(processes=jobs) as pool:
            parts = pool.map(_piece, tasks)
    else:
        parts = [_piece(task) for task in tasks]
    total = mp.fsum(parts)
    return total, upper, dps, time.time() - started


def digits_of(value, digits: int, dps: int) -> str:
    import mpmath as mp

    mp.mp.dps = dps
    scaled = mp.floor(value * mp.power(10, digits))
    return str(int(scaled)).zfill(digits)


def find_certified_digits(start: Path) -> Path | None:
    for candidate in (start, *start.parents):
        for name in CERT_CANDIDATES:
            if (candidate / name).is_file():
                return candidate / name
        for folder in ("40000", "digits"):
            nested = candidate / folder
            for name in CERT_CANDIDATES:
                if (nested / name).is_file():
                    return nested / name
    return None


def common_prefix(a: str, b: str) -> int:
    limit = min(len(a), len(b))
    index = 0
    while index < limit and a[index] == b[index]:
        index += 1
    return index


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(
        description="Level C: independent mpmath recomputation of the Golomb-Dickman constant."
    )
    parser.add_argument("--digits", type=int, default=1000, help="decimal digits to verify (default 1000)")
    parser.add_argument("--jobs", type=int, default=1, help="worker processes (default 1)")
    parser.add_argument(
        "--guard",
        type=int,
        default=60,
        help="extra working digits and tail margin (default 60)",
    )
    parser.add_argument(
        "--methods",
        default="tanh-sinh,gauss-legendre",
        help="comma separated quadrature rules (default tanh-sinh,gauss-legendre)",
    )
    parser.add_argument(
        "--certified",
        type=Path,
        default=None,
        help="digits file to compare with (default: search for 40000/golomb_dickman_40000_digits.txt)",
    )
    parser.add_argument("--json", type=Path, default=None, help="write a JSON report")
    args = parser.parse_args(argv)

    if args.digits < 20:
        print("FAIL: --digits must be at least 20", file=sys.stderr)
        return 2

    methods = [m.strip() for m in args.methods.split(",") if m.strip()]
    if len(methods) < 2:
        print("FAIL: at least two quadrature rules are required", file=sys.stderr)
        return 2

    results: dict[str, str] = {}
    meta: dict[str, object] = {}
    for method in methods:
        value, upper, dps, elapsed = integrate(args.digits, method, args.jobs, args.guard)
        # Probe a few digits beyond the target: the accuracy of the two
        # rules is what is being measured, not assumed to be exact.
        probe = args.digits + min(20, args.guard // 3)
        results[method] = digits_of(value, probe, dps)
        meta[method] = {
            "seconds": round(elapsed, 2),
            "dps": dps,
            "truncation_u": float(upper),
            "tail_below": f"10^-{args.digits + args.guard}",
        }
        print(f"{method}: {elapsed:.1f}s at {dps} working digits, tail < 1e-{args.digits + args.guard}")
        print(f"  {results[method][:80]}...")

    names = list(results)
    agreement = common_prefix(results[names[0]], results[names[1]])
    print(f"agreement between {names[0]} and {names[1]}: {agreement} leading digits")

    certified_path = args.certified or find_certified_digits(Path(__file__).resolve().parent)
    certified_match = None
    if certified_path is not None:
        certified = certified_path.read_text(encoding="ascii").strip()
        certified_match = common_prefix(results[names[0]], certified)
        print(f"agreement with {certified_path.name}: {certified_match} leading digits")
        print(f"  certified: {certified[:80]}...")
    else:
        print("note: no certified digits file found; only internal agreement was checked")

    required = args.digits
    ok = agreement >= required and (certified_match is None or certified_match >= required)

    report = {
        "digits": args.digits,
        "jobs": args.jobs,
        "methods": {name: {"digits": results[name][: args.digits], **meta[name]} for name in names},
        "agreement": agreement,
        "certified_file": str(certified_path) if certified_path else None,
        "certified_agreement": certified_match,
        "verdict": "PASS" if ok else "FAIL",
        "note": (
            "Numerical evidence from mpmath floating point; not an interval proof. "
            "The rigorous enclosure is the published certificate."
        ),
    }

    print()
    if ok:
        print(f"OK: {required} digits reproduced independently (Level C, numerical)")
    else:
        print(f"FAIL: reproduced only {agreement} digits, required {required}", file=sys.stderr)

    if args.json is not None:
        write_report(args.json, json.dumps(report, indent=2) + "\n")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
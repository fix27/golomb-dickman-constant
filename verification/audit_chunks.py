#!/usr/bin/env python3
"""Audit a checkpoint directory against its certificate.

The producing program saves, for every chunk of nodes, a 4-tuple

    (lo, hi, even, odd)

where ``even`` and ``odd`` are integer interval endpoints of the chunk's
contribution to the sum of the integrand, in units of 2^-S.

Checks
------
1. every chunk file parses to (int, int, (int, int), (int, int)) with
   lo < hi and even_lo <= even_hi, odd_lo <= odd_hi;
2. the index ranges are contiguous: no gaps, no overlaps;
3. T_lo = sum even_lo + odd_lo and T_hi = sum even_hi + odd_hi satisfy
   T_lo <= T_hi;
4. with the dyadic step h = m/2^shift, the identity

       lam_lo = floor(h T_lo) - B,    lam_hi = ceil(h T_hi) + C

   holds with B >= 0 and C >= 0, so the published interval contains the
   chunk-sum interval;
5. the corrections B and C are far below the published precision (they do
   not touch the first D-30 digits), and the chunk-sum width is the same
   order as the certificate width;
6. if the run plan is present, it is cross-checked: ``meta_v12.json`` must
   carry the same digit count D and scale S, its printed step ``h`` must
   round back to the recovered m/2^shift, and its K_L, K_R must bound the
   node range exactly.  The old ``meta.pkl`` format is only reported, not
   parsed, because its layout differs between pipeline versions.

When meta_v12.json is present, m comes from the recorded step h and is
therefore independent of lam_lo; then B and C are genuine consistency
checks (B = floor(h T_lo) - lam_lo).  Without it, m is recovered from
lam_lo and B = 1 carries little information; what remains informative is
the contiguity, the sign and scale of C, and the width agreement.  On the
40000-digit run, where only meta.pkl exists, this script recovers
m = 100859575 and C = 65673984721697, both exactly the values documented in
the producing plan -- which validates the procedure.

Usage
-----
    python audit_chunks.py --cert ../50000/golomb_dickman_50000_certified.txt \
                           --ckpt ../50000/gd_rigorous_ckpt_50000
    python audit_chunks.py --cert ... --ckpt ... --json report.json
"""

from __future__ import annotations

import argparse
import json
import pickle
import re
import sys
import tempfile
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from safe_pickle import UnsafePickleError, load_restricted  # noqa: E402

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


class AuditError(Exception):
    pass


def fail(message: str) -> None:
    raise AuditError(message)


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


def load_chunk(path: Path) -> tuple[int, int, int, int, int, int]:
    try:
        value = load_restricted(path)
    except UnsafePickleError as exc:
        fail(f"{path.name}: unsafe checkpoint ({exc})")
    if not isinstance(value, (tuple, list)) or len(value) != 4:
        fail(f"{path.name}: expected a 4-tuple (lo, hi, even, odd)")
    lo, hi, even, odd = value
    for name, pair in (("even", even), ("odd", odd)):
        if not isinstance(pair, (tuple, list)) or len(pair) != 2:
            fail(f"{path.name}: {name} is not a pair")
    numbers = [lo, hi, even[0], even[1], odd[0], odd[1]]
    if not all(type(x) is int for x in numbers):
        fail(f"{path.name}: non-integer entry")
    match = re.fullmatch(r"c_(-?\d+)\.pkl", path.name)
    if match is None:
        fail(f"{path.name}: unexpected checkpoint file name")
    if int(match.group(1)) != lo:
        fail(
            f"{path.name}: file name says start {match.group(1)}, "
            f"tuple says {lo}"
        )
    elo, ehi = int(even[0]), int(even[1])
    olo, ohi = int(odd[0]), int(odd[1])
    if not (lo < hi):
        fail(f"{path.name}: lo={lo} is not below hi={hi}")
    if not (elo <= ehi and olo <= ohi):
        fail(f"{path.name}: interval endpoints are reversed")
    return lo, hi, elo, ehi, olo, ohi


def decimal_exponent(value: int, scale_bits: int) -> tuple[int, str]:
    """Return k and mantissa with value/2^scale_bits = mantissa * 10^-k."""
    two_s = 1 << scale_bits
    low, high = 0, scale_bits
    while low < high:
        mid = (low + high) // 2
        if value * 10**mid >= two_s:
            high = mid
        else:
            low = mid + 1
    k = low
    milli = (value * 10**k * 1000) // two_s
    whole, frac = divmod(milli, 1000)
    return k, f"{whole}.{frac:03d}"


def parse_certificate(path: Path) -> tuple[int, int, int, int]:
    text = path.read_bytes().decode("ascii")
    lines = text.splitlines()
    S = int(re.search(r"\bS=(\d+)\b", lines[1]).group(1))
    lam_lo = int(re.search(r"\blam_lo=(\d+)\b", lines[1]).group(1))
    lam_hi = int(re.search(r"\blam_hi=(\d+)\b", lines[2]).group(1))
    D = len(lines[3].strip()) - 2
    return S, lam_lo, lam_hi, D


def check_plan(
    ckpt: Path,
    D: int,
    S: int,
    m: int,
    shift: int,
    first_index: int,
    last_index: int,
) -> dict[str, Any]:
    """Cross-check the recorded run plan when one is present."""
    plan: dict[str, Any] = {
        "meta_pkl": (ckpt / "meta.pkl").is_file(),
        "meta_v12": (ckpt / "meta_v12.json").is_file(),
        "h_checked": False,
    }
    meta_json = ckpt / "meta_v12.json"
    if not meta_json.is_file():
        return plan

    data = json.loads(meta_json.read_text(encoding="utf-8"))
    params = data.get("parameters", {})
    try:
        plan_D = int(params["D"])
        plan_S = int(params["S"])
    except (KeyError, TypeError, ValueError):
        fail("meta_v12.json: parameters.D or parameters.S is missing")
    if plan_D != D:
        fail(f"meta_v12.json: D={plan_D}, certificate has D={D}")
    if plan_S != S:
        fail(f"meta_v12.json: S={plan_S}, certificate has S={S}")

    try:
        h_text = str(params["h"])
    except KeyError:
        fail("meta_v12.json: parameters.h is missing")
    h = Fraction(Decimal(h_text))
    if h <= 0:
        fail(f"meta_v12.json: h={h_text} is not positive")
    m_from_h = round(h * (1 << shift))
    if m_from_h != m:
        fail(
            f"meta_v12.json h={h_text} gives m={m_from_h}, "
            f"but the certificate implies m={m}"
        )

    try:
        k_left = int(params["K_L"])
        k_right = int(params["K_R"])
    except (KeyError, TypeError, ValueError):
        fail("meta_v12.json: parameters.K_L or parameters.K_R is missing")
    # The plan stores the leftward extent K_L; the grid runs from -K_L to
    # K_R inclusive, i.e. the half-open interval [-K_L, K_R + 1).
    if (-k_left, k_right + 1) != (first_index, last_index):
        fail(
            f"meta_v12.json covers {k_left}..{k_right}, "
            f"chunks cover {first_index}..{last_index - 1}"
        )

    plan.update(
        {
            "h": h_text,
            "K_L": k_left,
            "K_R": k_right,
            "h_checked": True,
        }
    )
    return plan


def audit(ckpt: Path, cert: Path, shift: int) -> dict[str, Any]:
    S, lam_lo, lam_hi, D = parse_certificate(cert)

    files = sorted(ckpt.glob("c_*.pkl"))
    if not files:
        fail(f"{ckpt}: no chunk files (c_*.pkl)")

    t_lo = t_hi = 0
    ranges: list[tuple[int, int]] = []
    node_count = 0
    for path in files:
        lo, hi, elo, ehi, olo, ohi = load_chunk(path)
        ranges.append((lo, hi))
        t_lo += elo + olo
        t_hi += ehi + ohi
        node_count += hi - lo

    ranges.sort()
    gaps = [
        (ranges[i][1], ranges[i + 1][0])
        for i in range(len(ranges) - 1)
        if ranges[i][1] != ranges[i + 1][0]
    ]
    if gaps:
        fail(f"{len(gaps)} gap(s) or overlap(s) in the node ranges, first {gaps[0]}")
    if t_hi <= t_lo:
        fail("the chunk-sum intervals are empty: T_hi <= T_lo")

    m_recovered = ((lam_lo << shift) + t_lo // 2) // t_lo
    m = m_recovered
    step_source = "certificate (recovered from lam_lo)"
    meta_json = ckpt / "meta_v12.json"
    if meta_json.is_file():
        params = json.loads(meta_json.read_text(encoding="utf-8")).get("parameters", {})
        h_text = str(params.get("h", ""))
        if h_text:
            m = round(Fraction(Decimal(h_text)) * (1 << shift))
            step_source = "meta_v12.json (planned h)"
            if m != m_recovered:
                fail(
                    f"planned h={h_text} implies m={m}, but the certificate "
                    f"implies m={m_recovered}"
                )
    q_lo = (m * t_lo) >> shift
    q_hi = -((-m * t_hi) >> shift)
    B = q_lo - lam_lo
    C = lam_hi - q_hi
    if B < 0:
        fail(f"published lam_lo exceeds the chunk-sum lower bound (B = {B} < 0)")
    if C < 0:
        fail(f"published lam_hi is below the chunk-sum upper bound (C = {C} < 0)")
    if B > 10**6:
        fail(f"lower correction B = {B} is implausibly large")
    if C * 10 ** (D - 30) >= (1 << S):
        fail(f"upper correction C = {C} reaches the first D-30 digits")

    width_k, width_m = decimal_exponent((t_hi - t_lo) * m, S + shift)
    cert_k, cert_m = decimal_exponent(lam_hi - lam_lo, S)
    if abs(width_k - cert_k) > 1:
        fail(f"chunk-sum width 10^-{width_k} and certificate width 10^-{cert_k} disagree")

    plan = check_plan(ckpt, D, S, m, shift, ranges[0][0], ranges[-1][1])

    return {
        "digits": D,
        "scale_bits": S,
        "chunks": len(files),
        "nodes": node_count,
        "index_range": [ranges[0][0], ranges[-1][1] - 1],
        "index_range_half_open": [ranges[0][0], ranges[-1][1]],
        "gaps": 0,
        "step": {"numerator": m, "denominator": 1 << shift, "source": step_source},
        "B": B,
        "C": C,
        "chunk_width": f"{width_m} x 10^-{width_k}",
        "certificate_width": f"{cert_m} x 10^-{cert_k}",
        "plan": plan,
        "meta_present": plan["meta_pkl"] or plan["meta_v12"],
        "verdict": "PASS",
    }


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="Audit checkpoint chunks against a certificate.")
    parser.add_argument("--ckpt", type=Path, required=True, help="checkpoint directory")
    parser.add_argument("--cert", type=Path, required=True, help="certificate file")
    parser.add_argument("--shift", type=int, default=40, help="dyadic denominator exponent (default 40)")
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    try:
        report = audit(args.ckpt, args.cert, args.shift)
    except AuditError as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1
    except (json.JSONDecodeError, pickle.UnpicklingError, EOFError, OSError) as exc:
        print(f"FAIL: cannot read checkpoints or plan ({exc})", file=sys.stderr)
        return 1

    print(f"OK: {report['digits']} digits, checkpoint audit")
    print(f"  chunks: {report['chunks']} covering {report['nodes']} nodes")
    lo_i, hi_i = report["index_range"]
    print(
        f"  index range: {lo_i} .. {hi_i} ({report['nodes']} nodes, no gaps; "
        f"half-open {lo_i} .. {hi_i + 1})"
    )
    step = report["step"]
    print(f"  step: {step['numerator']} / {step['denominator']}  (from {step['source']})")
    print(f"  lower correction B = {report['B']}")
    print(f"  upper correction C = {report['C']}")
    print(f"  chunk-sum width: {report['chunk_width']}")
    print(f"  certificate width: {report['certificate_width']}")
    plan = report["plan"]
    if plan["meta_v12"]:
        print(
            f"  plan: meta_v12.json h = {plan['h']} matches the recovered step; "
            f"K_L={plan['K_L']}, K_R={plan['K_R']}"
        )
    elif plan["meta_pkl"]:
        print("  plan: meta.pkl present (old format, not parsed)")
    else:
        print("  plan: absent; the step was recovered from the certificate")

    if args.report is not None:
        lines = [
            f"Checkpoint audit for {report['digits']} digits",
            f"chunks: {report['chunks']}",
            f"nodes: {report['nodes']}",
            f"index range: {report['index_range'][0]} .. {report['index_range'][1]} "
            f"(half-open {report['index_range_half_open'][0]} .. "
            f"{report['index_range_half_open'][1]})",
            f"gaps/overlaps: {report['gaps']}",
            f"step: {step['numerator']} / {step['denominator']} (from {step['source']})",
            f"B: {report['B']}",
            f"C: {report['C']}",
            f"chunk-sum width: {report['chunk_width']}",
            f"certificate width: {report['certificate_width']}",
            f"meta.pkl present: {plan['meta_pkl']}",
            f"meta_v12.json present: {plan['meta_v12']}",
            f"plan step confirmed: {plan['h_checked']}",
            f"verdict: {report['verdict']}",
        ]
        write_report(args.report, "\n".join(lines) + "\n")
    if args.json is not None:
        write_report(args.json, json.dumps(report, indent=2) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

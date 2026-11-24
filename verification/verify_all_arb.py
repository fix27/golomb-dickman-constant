#!/usr/bin/env python3
"""Independent full Arb audit of every checkpoint node.

This is the check that the release plan calls mandatory.  It does *not* call
the producing program's node routine: the integrand

    G(t) = exp(-u - E1(u)) * u * (1 + exp(-t)),   u = exp(t - exp(-t)),

is evaluated here from Arb primitives, and E1 comes from Arb's own
``arb.expint(1)`` rather than from the Stieltjes continued fraction
used by ``golomb_dickman_26.py``.  Summation, directed rounding and the
fixed-point conversion are re-implemented as well.

What is checked
---------------
1. ``meta_v12.json``: presence, types, D/S against the certificate, the
   dyadic step, K_L/K_R against the actual coverage, chunk size.
2. every ``c_<lo>.pkl``: restricted unpickling, 4-tuple shape, integer
   types, ``lo < hi``, ordered interval pairs, file name == tuple start.
3. coverage: contiguous ``-K_L .. K_R`` inclusive, no gaps, no duplicates,
   node count ``K_L + K_R + 1``.
4. the certificate: ASCII, LF, exact decimal truncation, digits line.
5. with Arb available: every node recomputed, every chunk interval must
   intersect the saved interval (two correct enclosures of the same number
   must intersect), the total must intersect the published interval, and
   the published corrections must cover the recomputed discretisation and
   tail bounds.

Two correct enclosures of the same real number must intersect; that is a
necessary condition, not a tolerance.  A full PASS additionally requires
every recomputed chunk interval to be contained in the saved one.  If only
intersection can be established, the audit is reported as NOT_RUN -- never
as PASS.

Exit codes
----------
    0  PASS      all checks ran and passed
    1  FAIL      a check ran and found a discrepancy
    2  NOT_RUN   Arb (python-flint) is unavailable, the plan is missing,
                 or only a smoke subset was requested

A NOT_RUN is never reported as PASS.

Usage
-----
    python verify_all_arb.py --ckpt ../50000/gd_rigorous_ckpt_50000 \
                             --cert ../50000/golomb_dickman_50000_certified.txt
    python verify_all_arb.py ... --limit-chunks 4      # smoke test
    python verify_all_arb.py ... --structural-only     # no Arb needed
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import os
import re
import sys
import time
from decimal import Decimal
from fractions import Fraction
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
from safe_pickle import UnsafePickleError, load_restricted  # noqa: E402

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

CHUNK_RE = re.compile(r"c_(-?\d+)\.pkl\Z")
SHIFT = 40


class AuditFailure(Exception):
    """A check ran and failed."""


class NotRun(Exception):
    """A required check could not run."""


def fail(message: str) -> None:
    raise AuditFailure(message)


def not_run(message: str) -> None:
    raise NotRun(message)


# --------------------------------------------------------------------------
# Inputs
# --------------------------------------------------------------------------

def parse_certificate(path: Path) -> dict[str, Any]:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        fail("certificate: UTF-8 BOM is not allowed")
    if b"\r" in raw:
        fail("certificate: contains CR (canonical form is LF only)")
    try:
        text = raw.decode("ascii")
    except UnicodeDecodeError as exc:
        fail(f"certificate: not plain ASCII ({exc})")
    lines = text.split("\n")
    if len(lines) < 4:
        fail("certificate: fewer than four lines")
    head = lines[1]
    m_s = re.search(r"\bS=(\d+)\b", head)
    m_lo = re.search(r"\blam_lo=(\d+)\b", head)
    m_hi = re.search(r"\blam_hi=(\d+)\b", lines[2])
    if not (m_s and m_lo and m_hi):
        fail("certificate: cannot parse S, lam_lo, lam_hi")
    digits = lines[3].strip()
    if not digits.startswith("0.") or not digits[2:].isdigit():
        fail("certificate: fourth line is not 0.<digits>")
    digits = digits[2:]
    S = int(m_s.group(1))
    lo = int(m_lo.group(1))
    hi = int(m_hi.group(1))
    if not (0 < lo < hi):
        fail(f"certificate: need 0 < lam_lo < lam_hi, got {lo} / {hi}")
    if S < 64:
        fail(f"certificate: implausible scale S={S}")
    return {"S": S, "lo": lo, "hi": hi, "digits": digits, "D": len(digits)}


def load_plan(ckpt: Path) -> dict[str, Any]:
    meta = ckpt / "meta_v12.json"
    if not meta.is_file():
        not_run(f"{meta}: run plan is missing")
    try:
        data = json.loads(meta.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"{meta}: cannot read ({exc})")
    if data.get("format") != "gd-checkpoint-v12":
        fail(f"{meta}: unexpected format {data.get('format')!r}")
    params = data.get("parameters")
    if not isinstance(params, dict):
        fail(f"{meta}: parameters is not an object")
    required = ("D", "G", "h", "Ebits", "S", "K_L", "K_R")
    missing = [k for k in required if k not in params]
    if missing:
        fail(f"{meta}: missing parameters {missing}")
    try:
        plan = {
            "D": int(params["D"]),
            "G": int(params["G"]),
            "Ebits": int(params["Ebits"]),
            "S": int(params["S"]),
            "K_L": int(params["K_L"]),
            "K_R": int(params["K_R"]),
            "h_text": str(params["h"]),
            "chunk": int(data.get("chunk", 0)),
        }
    except (TypeError, ValueError) as exc:
        fail(f"{meta}: non-integer parameter ({exc})")
    if plan["D"] <= 0 or plan["S"] <= 0 or plan["Ebits"] <= 0:
        fail(f"{meta}: non-positive D/S/Ebits")
    if plan["Ebits"] >= plan["S"]:
        fail(f"{meta}: Ebits={plan['Ebits']} is not below S={plan['S']}")
    if plan["K_L"] <= 0 or plan["K_R"] <= 0:
        fail(f"{meta}: K_L/K_R must be positive")
    if plan["chunk"] <= 0:
        fail(f"{meta}: chunk size must be positive")
    h = Fraction(Decimal(plan["h_text"]))
    if h <= 0:
        fail(f"{meta}: h={plan['h_text']} is not positive")
    m = round(h * (1 << SHIFT))
    if m <= 0:
        fail(f"{meta}: h does not round to a positive numerator")
    if abs(h - Fraction(m, 1 << SHIFT)) > Fraction(1, 10**15):
        fail(f"{meta}: h={plan['h_text']} is not the dyadic {m}/2^{SHIFT}")
    plan.update({"m": m, "h": Fraction(m, 1 << SHIFT)})
    return plan


def load_chunks(ckpt: Path, plan: dict[str, Any]) -> list[dict[str, Any]]:
    files = sorted(ckpt.glob("c_*.pkl"))
    if not files:
        fail(f"{ckpt}: no c_*.pkl checkpoint files")
    chunks: list[dict[str, Any]] = []
    for path in files:
        match = CHUNK_RE.match(path.name)
        if match is None:
            fail(f"{path.name}: unexpected checkpoint name")
        try:
            value = load_restricted(path)
        except UnsafePickleError as exc:
            fail(f"{path.name}: unsafe checkpoint ({exc})")
        except OSError as exc:
            fail(f"{path.name}: cannot read ({exc})")
        if not isinstance(value, (tuple, list)) or len(value) != 4:
            fail(f"{path.name}: expected a 4-tuple (lo, hi, even, odd)")
        lo, hi, even, odd = value
        if not all(type(x) is int for x in (lo, hi)):
            fail(f"{path.name}: lo/hi are not integers")
        for label, pair in (("even", even), ("odd", odd)):
            if not isinstance(pair, (tuple, list)) or len(pair) != 2:
                fail(f"{path.name}: {label} is not a pair")
            if not all(type(x) is int for x in pair):
                fail(f"{path.name}: {label} has a non-integer endpoint")
            if pair[0] > pair[1]:
                fail(f"{path.name}: {label} endpoints are reversed")
        if lo != int(match.group(1)):
            fail(f"{path.name}: file name says {match.group(1)}, tuple says {lo}")
        if lo >= hi:
            fail(f"{path.name}: lo={lo} is not below hi={hi}")
        if lo < -plan["K_L"] or hi > plan["K_R"] + 1:
            fail(f"{path.name}: [{lo}, {hi}) is outside the plan")
        chunks.append(
            {
                "path": path.name,
                "lo": lo,
                "hi": hi,
                "even": (even[0], even[1]),
                "odd": (odd[0], odd[1]),
            }
        )
    return chunks


def audit_structure(
    cert: dict[str, Any], plan: dict[str, Any], chunks: list[dict[str, Any]]
) -> dict[str, Any]:
    if plan["D"] != cert["D"]:
        fail(f"plan D={plan['D']} != certificate D={cert['D']}")
    if plan["S"] != cert["S"]:
        fail(f"plan S={plan['S']} != certificate S={cert['S']}")
    expected_nodes = plan["K_L"] + plan["K_R"] + 1
    expected_chunks = math.ceil(expected_nodes / plan["chunk"])
    if len(chunks) != expected_chunks:
        fail(
            f"{len(chunks)} chunk files, plan implies {expected_chunks} "
            f"({expected_nodes} nodes / {plan['chunk']})"
        )

    chunks.sort(key=lambda c: c["lo"])
    seen: set[int] = set()
    duplicates = 0
    cursor = -plan["K_L"]
    for chunk in chunks:
        if chunk["lo"] in seen:
            duplicates += 1
        seen.add(chunk["lo"])
        if chunk["lo"] != cursor:
            fail(
                f"coverage breaks at {cursor}: next chunk starts at "
                f"{chunk['lo']} (gap or overlap)"
            )
        if chunk["hi"] - chunk["lo"] > plan["chunk"]:
            fail(
                f"{chunk['path']}: {chunk['hi'] - chunk['lo']} nodes "
                f"exceed the chunk size {plan['chunk']}"
            )
        cursor = chunk["hi"]
    if cursor != plan["K_R"] + 1:
        fail(f"coverage ends at {cursor}, plan ends at {plan['K_R'] + 1}")

    nodes = sum(c["hi"] - c["lo"] for c in chunks)
    if nodes != expected_nodes:
        fail(f"{nodes} nodes, plan implies {expected_nodes}")

    # Exact decimal truncation of the certificate (cheap, no Arb).
    S = cert["S"]
    D = cert["D"]
    scale = 10**D
    lo_digit = (scale * cert["lo"]) >> S
    hi_digit = (scale * cert["hi"]) >> S
    if lo_digit != hi_digit:
        fail("certificate: the interval crosses a decimal cell")
    if str(lo_digit).zfill(D) != cert["digits"]:
        fail("certificate: digit line does not equal the truncation")
    width_log10 = math.log10(cert["hi"] - cert["lo"]) - S * math.log10(2.0)

    return {
        "nodes": nodes,
        "chunks": len(chunks),
        "index_range": [-plan["K_L"], plan["K_R"]],
        "index_range_half_open": [-plan["K_L"], plan["K_R"] + 1],
        "duplicates": duplicates,
        "gaps": 0,
        "chunk_size": plan["chunk"],
        "step": f"{plan['m']}/2^{SHIFT}",
        "width_log10": width_log10,
        "guard_digits": -width_log10 - D,
    }


# --------------------------------------------------------------------------
# Arb part
# --------------------------------------------------------------------------

def _import_flint():
    try:
        import flint  # noqa: F401
        from flint import acb, arb, ctx
    except Exception as exc:  # pragma: no cover - environment dependent
        not_run(f"python-flint is not available ({exc})")
    if not hasattr(arb, "expint"):
        not_run("this python-flint build has no arb.expint")
    return flint, acb, arb, ctx


def _to_fixed(ctx, arb, x, scale_bits: int) -> tuple[int, int]:
    """Ball x -> integers [L, H] with x subset [L, H] * 2^-scale_bits."""
    old = ctx.prec
    try:
        ctx.prec = max(old, scale_bits + 128)
        sc = arb(1 << scale_bits)
        low = (x.lower() * sc).floor().lower().unique_fmpz()
        high = (x.upper() * sc).floor().upper().unique_fmpz()
        if low is None or high is None:
            fail("fixed-point conversion did not collapse")
        return int(low), int(high) + 1
    finally:
        ctx.prec = old


def _node_ball(acb, arb, h, k: int):
    """Rigorous enclosure of G(kh), independent of the producer's branches."""
    t = h * k
    em = (-t).exp()
    u = (t - em).exp()
    e1 = u.expint(1)  # Arb's own E_1, not the producer's continued fraction
    return (-u - e1).exp() * u * (1 + em)


def _floor_int(x) -> int:
    value = x.floor().unique_fmpz()
    if value is None:
        fail("floor is not unique")
    return int(value)


def _recompute_bounds(acb, arb, ctx, plan: dict[str, Any]) -> dict[str, Any]:
    """Recompute M, B_disc, tau_R, tau_L from the mathematical formulas."""
    ctx.prec = 512
    one = arb(1)
    e = one.exp()
    gam = arb.const_euler()
    d = arb(7) / 5
    c = d.cos()
    if not (c > 0):
        fail("cos d is not positive")
    a = 2 * c
    C1 = (gam + 2 + (e - 2) / 2).exp()
    M1 = C1 * (-a).exp() * (2 / a + 1 / (a * a))
    e2 = e * e
    em2 = arb(-2).exp()
    B2 = 2 * gam.exp() * (e2 * e2) * (2 * e2 + e2.exp() / 2).exp()
    M2 = 2 * B2
    th = d + em2 * d.sin()
    if not (th < arb.pi() / 2):
        fail("theta_max is not below pi/2")
    kap = th.cos()
    if not (kap > 0):
        fail("kappa is not positive")
    kp = kap * (-em2).exp()
    M3 = ((em2 - 2).exp()).exp() * (1 + em2) * (-kp * e2).exp() / kp
    M = M1 + M2 + M3

    h = arb(plan["m"]) / arb(1 << SHIFT)
    Bdisc = 2 * M / ((2 * arb.pi() * d / h).exp() - 1)
    tR = arb(plan["K_R"]) * h
    uR = (tR - (-tR).exp()).exp()
    tauR = (-uR).exp()
    tL = -arb(plan["K_L"]) * h
    uL = (tL - (-tL).exp()).exp()
    tauL = gam.exp() * uL * uL / 2

    def log10_upper(x) -> float:
        return float((x.upper().log() / arb(10).log()).upper())

    # Outward integer corrections, computed exactly as the paper defines them:
    # floor(tau * 2^S) + 1 from a rigorous upper bound.
    scale = arb(1 << plan["S"])

    def correction(x) -> int:
        return int((x.upper() * scale).floor().upper().unique_fmpz()) + 1

    return {
        "log10_M": log10_upper(M),
        "log10_Bdisc": log10_upper(Bdisc),
        "log10_tauR": log10_upper(tauR),
        "log10_tauL": log10_upper(tauL),
        "Bdisc": Bdisc,
        "tails": tauR + tauL,
        "T_R_int": correction(tauR),
        "T_L_int": correction(tauL),
        "B_int": correction(Bdisc),
    }


def _audit_one(
    chunk: dict[str, Any], m: int, S: int, Ebits: int, keep_intervals: bool
) -> dict[str, Any]:
    """Recompute one chunk in a fresh process; returns plain integers."""
    flint, acb, arb, ctx = _import_flint()
    ctx.prec = Ebits + 256
    h = arb(m) / arb(1 << SHIFT)
    even = arb(0)
    odd = arb(0)
    for k in range(chunk["lo"], chunk["hi"]):
        g = _node_ball(acb, arb, h, k)
        if not g.is_finite():
            fail(f"node k={k}: non-finite enclosure")
        if k & 1:
            odd = odd + g
        else:
            even = even + g
    r_lo_e, r_hi_e = _to_fixed(ctx, arb, even, S)
    r_lo_o, r_hi_o = _to_fixed(ctx, arb, odd, S)
    r_lo, r_hi = r_lo_e + r_lo_o, r_hi_e + r_hi_o
    s_lo = chunk["even"][0] + chunk["odd"][0]
    s_hi = chunk["even"][1] + chunk["odd"][1]
    if max(r_lo, s_lo) > min(r_hi, s_hi):
        fail(
            f"chunk {chunk['path']}: recomputed [{r_lo}, {r_hi}] and "
            f"saved [{s_lo}, {s_hi}] do not intersect"
        )
    contained = s_lo <= r_lo and r_hi <= s_hi
    digest = hashlib.sha256(
        f"{r_lo}|{r_hi}|{s_lo}|{s_hi}".encode("ascii")
    ).hexdigest()
    result = {
        "chunk": chunk["path"],
        "lo": chunk["lo"],
        "hi": chunk["hi"],
        "nodes": chunk["hi"] - chunk["lo"],
        "width_ratio": round((r_hi - r_lo) / max(1, s_hi - s_lo), 6),
        "contained": contained,
        "digest": digest,
        "python_flint": getattr(flint, "__version__", "unknown"),
    }
    if keep_intervals:
        result["recomputed"] = [r_lo, r_hi]
        result["saved"] = [s_lo, s_hi]
    # The caller needs the numbers in every case; the digest is only a receipt.
    result["_r_lo"] = r_lo
    result["_r_hi"] = r_hi
    result["_s_lo"] = s_lo
    result["_s_hi"] = s_hi
    return result


def audit_arb(
    cert: dict[str, Any],
    plan: dict[str, Any],
    chunks: list[dict[str, Any]],
    limit_chunks: int | None,
    jobs: int = 1,
    keep_intervals: bool = False,
) -> dict[str, Any]:
    flint, acb, arb, ctx = _import_flint()  # NOT_RUN before any plan work
    S = cert["S"]
    m = plan["m"]

    saved_lo = sum(c["even"][0] + c["odd"][0] for c in chunks)
    saved_hi = sum(c["even"][1] + c["odd"][1] for c in chunks)
    B = ((m * saved_lo) >> SHIFT) - cert["lo"]
    C = cert["hi"] - (-((-m * saved_hi) >> SHIFT))
    if B < 0:
        fail(f"published lam_lo exceeds the saved chunk sum (B={B})")
    if C < 0:
        fail(f"published lam_hi is below the saved chunk sum (C={C})")

    work = chunks if limit_chunks is None else chunks[:limit_chunks]
    started = time.time()
    if jobs <= 1:
        raw = [_audit_one(c, m, S, plan["Ebits"], keep_intervals) for c in work]
    else:
        from concurrent.futures import ProcessPoolExecutor, as_completed

        raw = []
        total = len(work)
        with ProcessPoolExecutor(max_workers=jobs) as pool:
            futures = [
                pool.submit(_audit_one, c, m, S, plan["Ebits"], keep_intervals)
                for c in work
            ]
            try:
                for done, future in enumerate(as_completed(futures), 1):
                    raw.append(future.result())
                    if done % 100 == 0 or done == total:
                        print(
                            f"  arb: {done}/{total} chunks, "
                            f"{time.time() - started:.0f}s",
                            file=sys.stderr,
                            flush=True,
                        )
            except BaseException:
                for future in futures:
                    future.cancel()
                raise

    raw.sort(key=lambda b: b["lo"])
    blocks = []
    total_lo = total_hi = 0
    saved_sum_lo = saved_sum_hi = 0
    checked_nodes = 0
    worst = 0.0
    flint_version = "unknown"
    contained_chunks = 0
    for item in raw:
        block = {
            "chunk": item["chunk"],
            "index_range": [item["lo"], item["hi"]],
            "nodes": item["nodes"],
            "width_ratio": item["width_ratio"],
            "contained": item["contained"],
            "digest": item["digest"],
        }
        if "recomputed" in item:
            block["recomputed"] = item["recomputed"]
            block["saved"] = item["saved"]
        blocks.append(block)
        total_lo += item["_r_lo"]
        total_hi += item["_r_hi"]
        saved_sum_lo += item["_s_lo"]
        saved_sum_hi += item["_s_hi"]
        checked_nodes += item["nodes"]
        worst = max(worst, item["width_ratio"])
        contained_chunks += int(item["contained"])
        flint_version = item["python_flint"]

    # The recomputed total must meet the published interval -- but only when
    # every chunk was recomputed.  A smoke subset is not a total.
    full = limit_chunks is None or limit_chunks >= len(chunks)
    if full and max(total_lo, cert["lo"]) > min(total_hi, cert["hi"]):
        fail(
            f"recomputed total [{total_lo}, {total_hi}] does not intersect "
            f"the certificate [{cert['lo']}, {cert['hi']}]"
        )

    bounds = _recompute_bounds(acb, arb, ctx, plan)
    scale = arb(1 << S)
    if not (_floor_int(bounds["Bdisc"] * scale) < B):
        fail(
            "lower correction B does not cover the discretisation bound "
            f"(log10 Bdisc={bounds['log10_Bdisc']:.4f})"
        )
    if not (_floor_int(bounds["tails"] * scale) < C):
        fail(
            "upper correction C does not cover the tail bounds "
            f"(log10 tauR={bounds['log10_tauR']:.4f}, "
            f"log10 tauL={bounds['log10_tauL']:.4f})"
        )

    width_log10 = math.log10(cert["hi"] - cert["lo"]) - S * math.log10(2.0)
    result = {
        "nodes_checked": checked_nodes,
        "chunks_checked": len(blocks),
        "blocks": blocks,
        "total": [total_lo, total_hi],
        "certificate_interval": [cert["lo"], cert["hi"]],
        "chunks_contained": contained_chunks,
        "all_chunks_contained": contained_chunks == len(blocks),
        "total_inside_saved": saved_sum_lo <= total_lo and total_hi <= saved_sum_hi,
        "cert_contains_total": cert["lo"] <= total_lo and total_hi <= cert["hi"],
        "B": B,
        "C": C,
        "log10_Bdisc": bounds["log10_Bdisc"],
        "log10_tauR": bounds["log10_tauR"],
        "log10_tauL": bounds["log10_tauL"],
        "log10_M": bounds["log10_M"],
        "width_log10": width_log10,
        "guard_digits": -width_log10 - cert["D"],
        "max_width_ratio": round(worst, 6),
        "seconds": round(time.time() - started, 1),
        "python_flint": flint_version,
    }
    if limit_chunks is not None and limit_chunks < len(chunks):
        result["smoke"] = (
            f"covered {checked_nodes} of "
            f"{sum(c['hi'] - c['lo'] for c in chunks)} nodes"
        )
    return result


# --------------------------------------------------------------------------
# CLI
# --------------------------------------------------------------------------

def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def run(
    ckpt: Path,
    cert_path: Path,
    *,
    structural_only: bool = False,
    limit_chunks: int | None = None,
    jobs: int = 1,
    keep_intervals: bool = False,
) -> dict[str, Any]:
    cert = parse_certificate(cert_path)
    plan = load_plan(ckpt)
    chunks = load_chunks(ckpt, plan)
    structure = audit_structure(cert, plan, chunks)
    report: dict[str, Any] = {
        "certificate": str(cert_path),
        "checkpoints": str(ckpt),
        "digits": cert["D"],
        "scale_bits": cert["S"],
        "python": sys.version.split()[0],
        "structure": structure,
        "arb": None,
        "status": PASS,
        "reason": "",
    }
    if structural_only:
        report["status"] = NOT_RUN
        report["reason"] = "structural-only run: the Arb node audit did not run"
        return report
    try:
        report["arb"] = audit_arb(
            cert, plan, chunks, limit_chunks, jobs, keep_intervals
        )
    except NotRun as exc:
        report["status"] = NOT_RUN
        report["reason"] = str(exc)
        return report
    if limit_chunks is not None and limit_chunks < len(chunks):
        report["status"] = NOT_RUN
        report["reason"] = report["arb"].get(
            "smoke", "smoke run: the full node set was not covered"
        )
        return report
    arb = report["arb"]
    if not arb["all_chunks_contained"]:
        report["status"] = NOT_RUN
        report["reason"] = (
            f"only intersection established: {arb['chunks_contained']} of "
            f"{arb['chunks_checked']} recomputed chunk intervals are contained "
            "in the saved intervals"
        )
    elif not arb["total_inside_saved"]:
        report["status"] = FAIL
        report["reason"] = "recomputed total is not inside the saved total"
    elif not arb["cert_contains_total"]:
        report["status"] = FAIL
        report["reason"] = "recomputed total is outside the published certificate"
    return report


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="Full independent Arb audit")
    parser.add_argument("--ckpt", type=Path, required=True)
    parser.add_argument("--cert", type=Path, required=True)
    parser.add_argument("--structural-only", action="store_true")
    parser.add_argument("--limit-chunks", type=int, default=None)
    parser.add_argument(
        "--keep-intervals",
        action="store_true",
        help="store the full per-chunk intervals in the JSON report "
             "(hundreds of megabytes at 50,000 digits)",
    )
    parser.add_argument(
        "--jobs",
        type=int,
        default=0,
        help="worker processes (0 = one per CPU minus one)",
    )
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    jobs = args.jobs
    if jobs <= 0:
        jobs = max(1, (os.cpu_count() or 2) - 1)
    try:
        report = run(
            args.ckpt,
            args.cert,
            structural_only=args.structural_only,
            limit_chunks=args.limit_chunks,
            jobs=jobs,
            keep_intervals=args.keep_intervals,
        )
    except NotRun as exc:
        report = {
            "certificate": str(args.cert),
            "checkpoints": str(args.ckpt),
            "python": sys.version.split()[0],
            "status": NOT_RUN,
            "reason": str(exc),
        }
    except AuditFailure as exc:
        report = {
            "certificate": str(args.cert),
            "checkpoints": str(args.ckpt),
            "python": sys.version.split()[0],
            "status": FAIL,
            "reason": str(exc),
        }

    status = report["status"]
    print(f"Arb audit: {status}")
    if report.get("reason"):
        print(f"  reason: {report['reason']}")
    if report.get("structure"):
        st = report["structure"]
        print(f"  nodes: {st['nodes']}, chunks: {st['chunks']}, chunk size: {st['chunk_size']}")
        print(
            f"  index range: {st['index_range'][0]} .. {st['index_range'][1]} "
            f"(half-open {st['index_range_half_open'][0]} .. "
            f"{st['index_range_half_open'][1]})"
        )
        print(f"  gaps/duplicates: {st['gaps']}/{st['duplicates']}")
        print(f"  width: 10^{st['width_log10']:.4f}, guard digits: {st['guard_digits']:.4f}")
    if report.get("arb"):
        a = report["arb"]
        print(f"  nodes checked: {a['nodes_checked']}, blocks: {a['chunks_checked']}")
        print(
            f"  chunks contained: {a['chunks_contained']}/{a['chunks_checked']}"
            f"  (all: {a['all_chunks_contained']})"
        )
        print(
            f"  total inside saved total: {a['total_inside_saved']}; "
            f"certificate contains total: {a['cert_contains_total']}"
        )
        print(f"  B = {a['B']}, C = {a['C']}")
        print(f"  log10 Bdisc = {a['log10_Bdisc']:.4f}")
        print(f"  log10 tauR  = {a['log10_tauR']:.4f}, log10 tauL = {a['log10_tauL']:.4f}")
        print(f"  max chunk width ratio (recomputed/saved): {a['max_width_ratio']}")
        print(f"  python-flint: {a['python_flint']}, seconds: {a['seconds']}")

    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.report is not None:
        lines = [f"Arb audit: {status}"]
        if report.get("reason"):
            lines.append(f"reason: {report['reason']}")
        lines.append(f"python: {report['python']}")
        if report.get("structure"):
            st = report["structure"]
            lines += [
                f"nodes: {st['nodes']}, chunks: {st['chunks']}, "
                f"chunk size: {st['chunk_size']}",
                f"index range: {st['index_range'][0]} .. {st['index_range'][1]} "
                f"(half-open {st['index_range_half_open'][0]} .. "
                f"{st['index_range_half_open'][1]})",
                f"gaps/duplicates: {st['gaps']}/{st['duplicates']}",
                f"width: 10^{st['width_log10']:.4f}, "
                f"guard digits: {st['guard_digits']:.4f}",
            ]
        if report.get("arb"):
            a = report["arb"]
            lines += [
                f"nodes checked: {a['nodes_checked']}, blocks: {a['chunks_checked']}",
                f"chunks contained: {a['chunks_contained']}/{a['chunks_checked']} "
                f"(all: {a['all_chunks_contained']})",
                f"total inside saved total: {a['total_inside_saved']}",
                f"certificate contains total: {a['cert_contains_total']}",
                f"B = {a['B']}",
                f"C = {a['C']}",
                f"log10 Bdisc = {a['log10_Bdisc']:.4f}",
                f"log10 tauR = {a['log10_tauR']:.4f}, "
                f"log10 tauL = {a['log10_tauL']:.4f}",
                f"max width ratio (recomputed/saved): {a['max_width_ratio']}",
                f"python-flint: {a['python_flint']}",
                f"seconds: {a['seconds']}",
            ]
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    return {PASS: 0, FAIL: 1, NOT_RUN: 2}[status]


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Turn an Arb audit report into a containment statement, or refuse.

``verify_all_arb.py`` also checks that each recomputed chunk interval is
*contained* in the saved one.  Containment is the strong statement:

    saved_lo <= recomputed_lo  and  recomputed_hi <= saved_hi

for every chunk, plus ``recomputed_total <= saved_total`` and
``certificate contains recomputed_total``.  Then the certificate arithmetic of
``audit_chunks.py`` (exact ``floor``/``ceil`` with ``B`` and ``C`` covering the
discretisation and tail bounds) places the published interval around the
rigorously recomputed total, so Arb's correctness plus the analytic bounds
prove that the constant lies in the published interval.

Intersection -- two enclosures of the same number must meet -- is necessary
but much weaker, and this script refuses to call it a proof.

This script only reads numbers; it never recomputes a node.  It accepts both
the compact report (per-chunk ``contained`` flags and digests) and the verbose
one written with ``--keep-intervals`` (full per-chunk intervals).

    python check_report_containment.py --report reports/arb_50000.json

Exit codes
----------
    0  PASS      containment holds everywhere
    1  FAIL      a recomputed interval is disjoint, or the totals are outside
    2  WEAK      intersections hold but containment fails somewhere, or the
                 report is partial; only the intersection claim is supported
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent))
import verify_all_arb as V  # noqa: E402

PASS, FAIL, WEAK = "PASS", "FAIL", "WEAK"


def _analyse_verbose(arb: dict[str, Any], cert: dict[str, Any]) -> dict[str, Any]:
    """Re-derive containment from stored per-chunk intervals."""
    disjoint: list[str] = []
    not_contained: list[dict[str, Any]] = []
    total_lo = total_hi = saved_lo = saved_hi = 0
    for block in arb["blocks"]:
        rec = block.get("recomputed")
        sav = block.get("saved")
        if not (isinstance(rec, list) and isinstance(sav, list)
                and len(rec) == 2 and len(sav) == 2):
            raise V.AuditFailure(f"{block.get('chunk')}: malformed interval record")
        if max(rec[0], sav[0]) > min(rec[1], sav[1]):
            disjoint.append(block["chunk"])
        elif not (sav[0] <= rec[0] and rec[1] <= sav[1]):
            not_contained.append(
                {
                    "chunk": block["chunk"],
                    "short_by": [max(0, rec[0] - sav[0]), max(0, sav[1] - rec[1])],
                }
            )
        total_lo += rec[0]
        total_hi += rec[1]
        saved_lo += sav[0]
        saved_hi += sav[1]
    return {
        "disjoint": disjoint,
        "not_contained": not_contained,
        "total_inside_saved": saved_lo <= total_lo and total_hi <= saved_hi,
        "cert_contains_total": cert["lo"] <= total_lo and total_hi <= cert["hi"],
    }


def analyse(report: dict[str, Any], cert: dict[str, Any] | None = None) -> dict[str, Any]:
    if report.get("status") == V.FAIL:
        return {
            "status": FAIL,
            "reason": report.get("reason") or "the audit report itself is FAIL",
            "blocks": 0,
        }
    arb = report.get("arb")
    if not arb or not arb.get("blocks"):
        raise V.NotRun("the report has no per-chunk results (structural-only run?)")
    structure = report.get("structure") or {}
    if structure.get("nodes") != arb.get("nodes_checked"):
        raise V.NotRun(
            f"partial audit: {arb.get('nodes_checked')} of "
            f"{structure.get('nodes')} nodes"
        )

    if cert is None:
        stored = arb.get("certificate_interval")
        if not (isinstance(stored, list) and len(stored) == 2):
            raise V.NotRun("no certificate interval in the report; pass --cert")
        cert = {"lo": stored[0], "hi": stored[1]}

    verbose = "recomputed" in (arb["blocks"][0] or {})
    if verbose:
        derived = _analyse_verbose(arb, cert)
    else:
        derived = {
            "disjoint": [],
            "not_contained": [
                {"chunk": block["chunk"], "short_by": None}
                for block in arb["blocks"]
                if block.get("contained") is False
            ],
            "total_inside_saved": bool(arb.get("total_inside_saved")),
            "cert_contains_total": bool(arb.get("cert_contains_total")),
        }

    blocks = len(arb["blocks"])
    if derived["disjoint"]:
        return {
            "status": FAIL,
            "reason": f"{len(derived['disjoint'])} recomputed chunk(s) are "
                      "disjoint from the saved interval",
            "disjoint": derived["disjoint"][:10],
            "blocks": blocks,
        }
    if derived["not_contained"]:
        return {
            "status": WEAK,
            "reason": (
                f"{len(derived['not_contained'])} of {blocks} chunks intersect "
                "but are not contained; only the intersection claim is supported"
            ),
            "blocks": blocks,
            "not_contained": derived["not_contained"][:10],
            "total_inside_saved": derived["total_inside_saved"],
            "cert_contains_total": derived["cert_contains_total"],
        }
    if not derived["total_inside_saved"]:
        return {
            "status": FAIL,
            "reason": "chunks are contained but their sum is not inside the saved total",
            "blocks": blocks,
        }
    if not derived["cert_contains_total"]:
        return {
            "status": FAIL,
            "reason": "the recomputed total is outside the published certificate",
            "blocks": blocks,
        }
    return {
        "status": PASS,
        "reason": (
            "every recomputed chunk interval is contained in the saved interval, "
            "and the recomputed total is contained in the certificate"
        ),
        "blocks": blocks,
        "total_inside_saved": True,
        "cert_contains_total": True,
    }


def main(argv: list[str] | None = None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    parser = argparse.ArgumentParser(description="Containment analysis of an Arb report")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--cert", type=Path, default=None,
                        help="certificate file (optional if the report stores its interval)")
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--show", type=int, default=10, help="how many failures to print")
    args = parser.parse_args(argv)

    try:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        cert = V.parse_certificate(args.cert) if args.cert is not None else None
        result = analyse(report, cert)
    except V.NotRun as exc:
        result = {"status": "NOT_RUN", "reason": str(exc)}
    except (V.AuditFailure, OSError, json.JSONDecodeError) as exc:
        result = {"status": FAIL, "reason": f"{type(exc).__name__}: {exc}"}

    status = result["status"]
    print(f"Containment: {status}")
    print(f"  reason: {result.get('reason', '')}")
    if "blocks" in result:
        print(f"  chunks analysed: {result['blocks']}")
    for item in result.get("not_contained", [])[: args.show]:
        short = item.get("short_by")
        suffix = f" short_by={short}" if short is not None else ""
        print(f"    not contained: {item['chunk']}{suffix}")
    for name in result.get("disjoint", [])[: args.show]:
        print(f"    disjoint: {name}")

    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8",
                             newline="\n")
    return {PASS: 0, FAIL: 1, WEAK: 2, "NOT_RUN": 2}[status]


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Run every verification level and report an honest aggregate status.

Statuses
--------
Each check reports exactly one of

    PASS      the check ran and succeeded;
    FAIL      the check ran and found a discrepancy;
    NOT_RUN   the check did not run (missing dependency or not requested).

``NOT_RUN`` is never treated as success.  The aggregate status is

    FAIL        at least one *required* check failed;
    INCOMPLETE  no required check failed, but at least one did not run;
    PASS        every required check ran and passed.

Only ``PASS`` exits with code 0.

Levels
------
    A (50,000)        certificate/digits/b-file, exact integer arithmetic
    A (40,000)        the previous result, unchanged
    B' (chunks)       checkpoint structure, coverage and exact sums
    Arb (50,000)      independent node-by-node Arb audit (required)
    B (math, 40,000)  mathematical pre-checks for the previous result
                      (optional: its Arb re-audit is a separate artefact)

The Arb level is a full node audit by default only when ``--full-arb`` is
given; otherwise it runs the structural preflight, which returns NOT_RUN,
so the aggregate stays INCOMPLETE.  That is deliberate: a release is not
PASS until the full Arb audit has actually run.

Usage
-----
    python run_all.py                     # fast; Arb level = NOT_RUN
    python run_all.py --full-arb --arb-jobs 11
    python run_all.py --arb-limit 8       # smoke subset, still NOT_RUN
    python run_all.py --arb-report reports/arb_50000.json
                                          # audit an existing report instead
                                          # of recomputing every node
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HEADER = "Golomb-Dickman constant: verification levels"
PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"


def _configure_stdio() -> None:
    """Never fail on a console that cannot encode a path (cp866/cp1251)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


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


def run(command: list[str], cwd: Path) -> tuple[int, str, float]:
    started = time.time()
    completed = subprocess.run(
        [sys.executable, "-u", *command],
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    return completed.returncode, output, time.time() - started


def status_from_exit(code: int) -> str:
    if code == 0:
        return PASS
    if code == 2:
        return NOT_RUN
    return FAIL


def reason_from_output(output: str, status: str) -> str:
    if status == PASS:
        return ""
    for line in output.splitlines():
        stripped = line.strip()
        if stripped.startswith(("FAIL:", "NOT_RUN:", "reason:")):
            return stripped
    for line in reversed(output.splitlines()):
        if line.strip():
            return line.strip()
    return ""


def aggregate(results: list[dict]) -> str:
    """PASS only when every required check ran and passed."""
    required = [r for r in results if r["required"]]
    if any(r["status"] == FAIL for r in required):
        return FAIL
    if any(r["status"] == NOT_RUN for r in required):
        return "INCOMPLETE"
    return PASS


def build_levels(args: argparse.Namespace) -> list[tuple[str, list[str], bool]]:
    cert_rel = "../50000/golomb_dickman_50000_certified.txt"
    if args.arb_report is not None:
        # Do not spend hours recomputing a node set that has already been
        # audited: re-check the saved report instead.  The containment
        # checker returns 0 only for a complete, fully contained audit.
        arb_level: tuple[str, list[str], bool] = (
            "Arb (50,000, saved report)",
            [
                "check_report_containment.py",
                "--report",
                str(args.arb_report),
                "--cert",
                cert_rel,
            ],
            True,
        )
    else:
        arb_command = ["verify_all_arb.py", "--ckpt", "../50000/gd_rigorous_ckpt_50000",
                       "--cert", cert_rel]
        if args.arb_limit is not None:
            arb_command += ["--limit-chunks", str(args.arb_limit)]
        elif not args.full_arb:
            arb_command.append("--structural-only")
        else:
            arb_command += ["--jobs", str(args.arb_jobs)]
        arb_level = ("Arb (50,000)", arb_command, True)

    levels: list[tuple[str, list[str], bool]] = [
        (
            "A (50,000)",
            [
                "verify_certificate.py",
                "--cert",
                "../50000/golomb_dickman_50000_certified.txt",
                "--sha256-manifest",
                "../50000/SHA256SUMS.txt",
                "--compare",
                "../40000/golomb_dickman_40000_digits.txt",
            ],
            True,
        ),
        ("A (40,000)", ["verify_40000.py"], True),
        (
            "B' (chunks)",
            [
                "audit_chunks.py",
                "--ckpt",
                "../50000/gd_rigorous_ckpt_50000",
                "--cert",
                "../50000/golomb_dickman_50000_certified.txt",
            ],
            True,
        ),
        arb_level,
        # The 40,000-digit mathematical audit is the previous result; its own
        # Arb re-audit is a separate artefact, so it is reported, not gating.
        ("B (math, 40,000)", ["level_b.py"], False),
    ]
    if args.digits > 0:
        levels.append(
            (
                "C (numerical)",
                [
                    "independent_quadrature.py",
                    "--digits",
                    str(args.digits),
                    "--jobs",
                    str(args.jobs),
                ],
                True,
            )
        )
    return levels


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description=HEADER)
    parser.add_argument("--digits", type=int, default=0,
                        help="also run the numerical Level C to this many digits")
    parser.add_argument("--jobs", type=int, default=1, help="Level C workers")
    parser.add_argument("--full-arb", action="store_true",
                        help="run the full independent Arb node audit (hours)")
    parser.add_argument("--arb-jobs", type=int, default=0,
                        help="Arb workers (0 = one per CPU minus one)")
    parser.add_argument("--arb-limit", type=int, default=None,
                        help="smoke subset of chunks (result stays NOT_RUN)")
    parser.add_argument("--arb-report", type=Path, default=None,
                        help="re-check an existing Arb JSON report instead of "
                             "recomputing every node (hours)")
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    here = Path(__file__).resolve().parent
    levels = build_levels(args)
    if not (here.parent / "50000" / "gd_rigorous_ckpt_50000").is_dir():
        # Without checkpoints, B' and a live Arb run are impossible; a saved
        # Arb report can still be re-checked.
        levels = [
            item for item in levels
            if not item[0].startswith("B'")
            and not (item[0].startswith("Arb") and args.arb_report is None)
        ]

    print(HEADER)
    print(f"python: {sys.version.split()[0]}")
    print(f"workdir: {here}")
    print()

    results = []
    for name, command, required in levels:
        code, output, elapsed = run(command, here)
        status = status_from_exit(code)
        reason = reason_from_output(output, status)
        results.append(
            {
                "level": name,
                "command": command,
                "required": required,
                "status": status,
                "exit_code": code,
                "reason": reason,
                "seconds": round(elapsed, 1),
            }
        )
        print(f"=== {name}: {' '.join(command)}")
        print(f"    status: {status} (exit {code}) in {elapsed:.1f}s")
        for line in output.strip().splitlines():
            print(f"    {line}")
        print()

    verdict = aggregate(results)
    required = [r for r in results if r["required"]]
    passed = sum(1 for r in required if r["status"] == PASS)
    failed = sum(1 for r in required if r["status"] == FAIL)
    skipped = sum(1 for r in required if r["status"] == NOT_RUN)
    print(f"overall: {verdict}")
    print(
        f"  required: {len(required)}  passed: {passed}  "
        f"failed: {failed}  not run: {skipped}"
    )
    optional = [r for r in results if not r["required"]]
    for item in optional:
        print(f"  optional {item['level']}: {item['status']}")
    if verdict == "INCOMPLETE":
        print("  a required check did not run; this is not a PASS")

    payload = {
        "verdict": verdict,
        "required_total": len(required),
        "passed": passed,
        "failed": failed,
        "not_run": skipped,
        "levels": results,
    }
    if args.report is not None:
        lines = [HEADER, f"verdict: {verdict}", ""]
        for result in results:
            mark = "required" if result["required"] else "optional"
            lines.append(
                f"[{result['status']:7}] {result['level']} ({mark}): "
                f"exit {result['exit_code']} in {result['seconds']}s"
            )
            if result["reason"]:
                lines.append(f"          {result['reason']}")
        write_report(args.report, "\n".join(lines) + "\n")
    if args.json is not None:
        write_report(args.json, json.dumps(payload, indent=2) + "\n")

    return 0 if verdict == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())

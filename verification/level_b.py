#!/usr/bin/env python3
"""Level B: audit the mathematics behind the certificate.

Level A checks that the published files are internally consistent.  It does
not check that the interval really contains the constant.  This script audits
the proof structure instead:

  1. checklist  -- meta parameters, chunk coverage, certificate arithmetic
                   and the b-file, with exact integer checks;
  2. plan       -- re-derive the discretisation bound B_disc and the two
                   truncation tails with an independent Decimal computation;
  3. methods    -- formula self-test: the continued fraction for the node
                   function G(u) against its asymptotics, and the closed form
                   against direct series summation;
  4. nodes      -- recompute 12 spread-out chunks (200 nodes each) from
                   scratch in Decimal and compare with the saved intervals.

Checkpoints are treated as a cache, never as proof: nothing here accepts a
saved ball because it is saved.  Every node value that is compared is
recomputed from the formula, and the comparison tolerance is printed.

What this still does not establish
----------------------------------
The rigorous inequalities (tail bounds, discretisation constant M, directed
rounding of every Arb operation) live in ``verify_checkpoints_arb.py``, which
needs python-flint/Arb.  If Arb is unavailable this script says so instead of
pretending the audit is complete.

Usage
-----
    python level_b.py
    python level_b.py --chunks 24 --json reports/level_b.json
    python level_b.py --checks ../40000/checks
"""

from __future__ import annotations

import argparse
import json
import subprocess
import tempfile
import sys
import time
from pathlib import Path

STEPS = (
    ("checklist", ["verify_checkpoints.py"]),
    ("plan", ["verify_nodes_decimal.py", "--plan"]),
    ("methods", ["verify_nodes_decimal.py", "--methods"]),
    ("nodes", ["verify_nodes_decimal.py", "--chunks", "12"]),
)


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

def _configure_stdio() -> None:
    """Never fail on a console that cannot encode a path (cp866/cp1251)."""
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

def find_checks(start: Path) -> Path | None:
    candidates = [
        start / "math_audit",
        start.parent / "40000" / "checks",
        start / "checks",
        start.parent / "checks",
    ]
    candidates += [p / "math_audit" for p in start.parents]
    candidates += [p / "40000" / "checks" for p in start.parents]
    for candidate in candidates:
        if (candidate / "verify_checkpoints.py").is_file():
            return candidate
    return None


def run_step(checks: Path, name: str, command: list[str], chunks: int) -> dict[str, object]:
    if name == "nodes":
        command = ["verify_nodes_decimal.py", "--chunks", str(chunks)]
    started = time.time()
    completed = subprocess.run(
        [sys.executable, "-u", *command],
        cwd=checks,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    elapsed = time.time() - started
    output = (completed.stdout or "") + (completed.stderr or "")
    tail = [line for line in output.splitlines() if line.strip()][-14:]
    return {
        "step": name,
        "command": " ".join(command),
        "exit_code": completed.returncode,
        "seconds": round(elapsed, 2),
        "output_tail": tail,
        "ok": completed.returncode == 0,
    }


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="Level B: audit the mathematics of the certificate.")
    parser.add_argument("--checks", type=Path, default=None, help="directory with the audit scripts")
    parser.add_argument("--chunks", type=int, default=12, help="chunks recomputed from scratch (default 12)")
    parser.add_argument("--json", type=Path, default=None, help="write a JSON report")
    parser.add_argument("--report", type=Path, default=None, help="write a text report")
    args = parser.parse_args(argv)

    here = Path(__file__).resolve().parent
    checks = args.checks.resolve() if args.checks else find_checks(here)
    if checks is None or not (checks / "verify_checkpoints.py").is_file():
        print("FAIL: cannot find the audit scripts (verify_checkpoints.py)", file=sys.stderr)
        print("      pass --checks DIR, or keep 40000/checks next to verification/", file=sys.stderr)
        return 2

    print(f"Level B: mathematical audit")
    print(f"  scripts: {checks}")
    print(f"  checkpoint policy: recompute, do not trust (trust_checkpoint=False)")
    print()

    results = []
    for name, command in STEPS:
        result = run_step(checks, name, command, args.chunks)
        results.append(result)
        status = "OK  " if result["ok"] else "FAIL"
        print(f"{status} {name:9s} {result['seconds']:7.2f}s  {' '.join(result['command'])}")
        for line in result["output_tail"]:
            print(f"       {line}")
        print()

    arb = checks / "verify_checkpoints_arb.py"
    arb_available = False
    if arb.exists():
        probe = subprocess.run(
            [sys.executable, "-c", "import flint"],
            capture_output=True,
            text=True,
        )
        arb_available = probe.returncode == 0

    failed = [r["step"] for r in results if not r["ok"]]
    verdict = "PASS" if not failed else "FAIL"
    print(f"Level B verdict: {verdict}")
    if not arb_available:
        print("  note: Arb (python-flint) is not importable here, so the rigorous")
        print("        interval re-audit (verify_checkpoints_arb.py) was NOT run.")
        print("        The certificate's enclosure itself is therefore still")
        print("        established only by the original production run.")

    report = {
        "level": "B",
        "checks_directory": str(checks),
        "checkpoint_policy": "recompute; saved intervals are a cache, not proof",
        "steps": results,
        "arb_available": arb_available,
        "arb_audit_run": False,
        "verdict": verdict,
    }

    if args.report is not None:
        lines = [f"Level B mathematical audit  ({verdict})", f"scripts: {checks}", ""]
        for result in results:
            lines.append(f"{result['step']}: exit {result['exit_code']} in {result['seconds']}s")
            lines.extend(f"    {line}" for line in result["output_tail"])
            lines.append("")
        if not arb_available:
            lines.append("Arb re-audit: NOT RUN (python-flint could not be imported)")
        write_report(args.report, "\n".join(lines) + "\n")
    if args.json is not None:
        write_report(args.json, json.dumps(report, indent=2) + "\n")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
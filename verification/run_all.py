#!/usr/bin/env python3
"""Run the three verification levels in order and summarise the verdicts.

    python run_all.py                     # Levels A and B (seconds)
    python run_all.py --digits 1000       # plus Level C at 1000 digits
    python run_all.py --digits 40000 --jobs 12

Level A  certificate/digits consistency, exact integer arithmetic;
         run for the current 50,000-digit certificate and the previous
         40,000-digit one.
Level B  mathematical audit: parameters, discretisation bound, tails,
         formula self-test, and a fresh recomputation of sample chunks.
Level B' checkpoint-sum audit of the 50,000-digit run (only when the
         checkpoints are present, i.e. in the full repository).
Level C  independent recomputation of the digits with mpmath and two
         different quadrature rules (numerical evidence, not a proof).

Exit code 0 only if every level that was run passed.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HEADER = "Golomb-Dickman constant: three-level verification"


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


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description=HEADER)
    parser.add_argument("--digits", type=int, default=0, help="also run Level C to this many digits (0 = skip)")
    parser.add_argument("--jobs", type=int, default=1, help="Level C worker processes")
    parser.add_argument("--report", type=Path, default=None, help="text report path")
    parser.add_argument("--json", type=Path, default=None, help="JSON report path")
    args = parser.parse_args(argv)

    here = Path(__file__).resolve().parent
    levels: list[tuple[str, list[str]]] = [
        (
            "A (50,000)",
            [
                "verify_certificate.py",
                "--cert",
                "../50000/golomb_dickman_50000_certified.txt",
                "--compare",
                "../40000/golomb_dickman_40000_digits.txt",
            ],
        ),
        ("A (40,000)", ["verify_40000.py"]),
        (
            "B' (chunks)",
            [
                "audit_chunks.py",
                "--ckpt",
                "../50000/gd_rigorous_ckpt_50000",
                "--cert",
                "../50000/golomb_dickman_50000_certified.txt",
            ],
        ),
        ("B", ["level_b.py"]),
    ]
    if not (here.parent / "50000" / "gd_rigorous_ckpt_50000").is_dir():
        levels = [item for item in levels if not item[0].startswith("B'")]
    if args.digits > 0:
        levels.append(("C", ["independent_quadrature.py", "--digits", str(args.digits), "--jobs", str(args.jobs)]))

    print(HEADER)
    print(f"python: {sys.version.split()[0]}")
    print(f"workdir: {here}")
    print()

    results = []
    for name, command in levels:
        code, output, elapsed = run(command, here)
        results.append({"level": name, "command": command, "exit_code": code, "seconds": round(elapsed, 1)})
        print(f"=== Level {name}: {' '.join(command)} -> exit {code} in {elapsed:.1f}s")
        for line in output.strip().splitlines():
            print(f"    {line}")
        print()

    failed = [r["level"] for r in results if r["exit_code"] != 0]
    verdict = "PASS" if not failed else "FAIL"
    print(f"overall: {verdict}")
    if "B" in [r["level"] for r in results]:
        print("  Level B cannot re-run the Arb enclosure on machines without python-flint;")
        print("  see reports/level_b.txt for the exact status on the machine that ran it.")

    if args.report is not None:
        lines = [HEADER, f"verdict: {verdict}", ""]
        for result in results:
            lines.append(f"Level {result['level']}: exit {result['exit_code']} in {result['seconds']}s")
        write_report(args.report, "\n".join(lines) + "\n")
    if args.json is not None:
        import json

        write_report(args.json, json.dumps({"verdict": verdict, "levels": results}, indent=2) + "\n")

    return 0 if not failed else 1


if __name__ == "__main__":
    raise SystemExit(main())
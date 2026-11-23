#!/usr/bin/env python3
"""Level B: full Arb node replay of the 40,000-digit certificate.

This script recomputes every chunk of the plan from scratch.  It does not
read a checkpoint directory, does not accept a saved node ball, and does not
use any value from the published certificate except D, G (default 30) and the
declared scale S -- which make_plan() must reproduce independently.

    python full_arb_replay_40000.py --jobs 16 --chunk 200
    python full_arb_replay_40000.py --cert ../golomb_dickman_40000_certified.txt

The full run is the expensive one (about the same wall time as production).
The comparison is:

  * the replay interval proves the same D digits;
  * its lower and upper endpoints agree with the published endpoints to
    better than one unit in the D-th decimal place;
  * the two intervals overlap;
  * S is reproduced by make_plan(D, G).

Exit codes: 0 PASS, 1 FAIL, 2 usage/import error.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _import_core():
    """The verification layer depends only on the core module."""
    for candidate in (ROOT, *ROOT.parents):
        if (candidate / "golomb_dickman_27.py").is_file():
            sys.path.insert(0, str(candidate))
            break
    import golomb_dickman_27 as core  # noqa: WPS433 (deliberate late import)
    return core


def main(argv=None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(
        description="Level B: recompute all Arb chunks and compare with the "
                    "published 40,000-digit certificate.")
    parser.add_argument(
        "--cert", type=Path,
        default=ROOT / "golomb_dickman_40000_certified.txt",
        help="published certificate (default: ../golomb_dickman_40000_certified.txt)")
    parser.add_argument("--jobs", type=int, default=0,
                        help="worker processes (0 = all CPUs)")
    parser.add_argument("--chunk", type=int, default=200,
                        help="nodes per chunk (default 200 -> 1209 chunks at D=40000)")
    parser.add_argument("--guard", type=int, default=30,
                        help="guard used by the production run (default 30)")
    parser.add_argument("--ladder", action="store_true",
                        help="enable the precision ladder (off: reproduce the "
                             "published interval width)")
    parser.add_argument("--json", type=Path, default=None,
                        help="write the JSON report here")
    args = parser.parse_args(argv)

    if not args.cert.is_file():
        print(f"FAIL: certificate not found: {args.cert}", file=sys.stderr)
        return 2
    try:
        core = _import_core()
    except Exception as exc:  # pragma: no cover - import diagnostics
        print(f"FAIL: cannot import golomb_dickman_27: {exc}", file=sys.stderr)
        return 2

    print(f"Level B: full Arb node replay")
    print(f"  certificate: {args.cert}")
    print(f"  policy: recompute every node; no checkpoint input")
    try:
        report = core.replay_certificate(
            str(args.cert), jobs=args.jobs, chunk=args.chunk,
            G=args.guard, precision_ladder=args.ladder)
    except Exception as exc:
        print(f"LEVEL B: FAIL ({type(exc).__name__}: {exc})", file=sys.stderr)
        return 1

    if args.json is not None:
        with open(args.json, "w", encoding="utf-8", newline="\n") as f:
            json.dump(report, f, indent=2, sort_keys=True)
            f.write("\n")
        print(f"  report: {args.json}")
    print(f"LEVEL B: PASS ({report['chunks']} chunks, {report['digits']} digits)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

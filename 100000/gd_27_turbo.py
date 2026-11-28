# -*- coding: utf-8 -*-
"""
golomb_dickman_28.py — accelerated wrapper around golomb_dickman_27.py

    python golomb_dickman_28.py certify --digits 100000 --jobs 24

Requires golomb_dickman_27.py in the same directory (v28 imports it and
patches three module-level functions).  Nothing in the mathematics, the
plan, the enclosures or the final certify() check changes.

What changes vs v27
-------------------

1. RS_M = 64  (was 32).  Measured minimum at D = 100000:
       RS_M 32 : 17.7 s   RS_M 48 : 15.6 s   RS_M 64 : 15.1 s
       RS_M 80 : 15.8 s   RS_M 96 : 16.1 s   RS_M 128 : 16.3 s
   ~15 % faster series_S at D >= 40000, small gain at D = 10000.

2. cf disabled for D > 5000: _heuristic_cf_min_u returns +inf.
   This is the big win.  At D = 100000 the continued-fraction branch
   costs ~300 s per node at u ~ 1.4e4, while series_S costs ~15 s.  The
   cf heuristic had been calibrated on D = 10000 where asym takes over
   before cf's region of usefulness; for D >= 20000 the cf window
   (u in [cf_min_u, u_asym)) is both wide and catastrophically slow.
   Series is the correct fallback there.

3. asym_K rewritten as a binary search on the convex function
       f(K) = lng + ln(K!) - (K+1)*xf - uf,
   O(log uf) instead of O(uf).  Called up to twice per right-side node;
   the previous O(uf) search cost ~1-2 ms per node for the largest uf,
   now negligible.  Same K returned (smallest valid one).

4. Default chunk size 500 instead of 100 (only in the fallback CLI;
   the v27 CLI is reused, so pass --chunk 500 explicitly).

GPU
---
python-flint / Arb has no CUDA or ROCm support.  The core operation is
arbitrary-precision interval arithmetic at 2^18 bits (332 000 bits for
D = 100000): big-integer multiplication and a single exp() at that
precision.  A GPU port would require
  * a CUDA implementation of big-integer multiplication (NTT),
  * a CUDA implementation of exp() to 332 000 bits,
  * certified rounding on the GPU,
  * and the entire routing / postcondition layer rewritten.
That is a months-long project, and it would not beat Arb: the single
largest operation is exp() at 332 000 bits, which Arb already computes
in ~35 ms on one core.  The full run is ~25-30 h wall time on 24 cores;
a GPU version would not beat that by enough to justify the effort.
CPU parallelism is already saturated at --jobs = ncpu.

What this file does NOT do
--------------------------
The wrapper does not change the checkpoint schema, the trust base, or
the certificate issuance policy.  It is still a strict run: every node
is recomputed in Arb, every chunk is re-verified, the assembled interval
is re-checked against OEIS A084945.  If you want an audit-only run with
old checkpoints, use v27 directly with --certify-mode audit.
"""

import math
import sys

# Import v27 as the base module.  golomb_dickman_27.py must be in the
# same directory (or on sys.path).
import golomb_dickman_27 as v27


# ---------------------------------------------------------------------------
# Patch 1: RS_M
# ---------------------------------------------------------------------------
v27.RS_M = 64


# ---------------------------------------------------------------------------
# Patch 2: disable cf for D > 5000
# ---------------------------------------------------------------------------
def _heuristic_cf_min_u(D):
    if D < 500:
        return 3000.0
    elif D < 5000:
        return 8000.0
    else:
        return float("inf")   # series (or asym) only

v27._heuristic_cf_min_u = _heuristic_cf_min_u


# ---------------------------------------------------------------------------
# Patch 3: binary-search asym_K
# ---------------------------------------------------------------------------
_orig_asym_K = v27.asym_K


def asym_K(xf, uf, lng, L_eps):
    """Same result as v27.asym_K, but O(log uf) instead of O(uf).

    Returns the smallest K in [0, min(ASYM_KMAX, uf-1)] such that
        lng + ln(K!) - (K+1)*xf - uf <= -L_eps - 3,
    or None if no such K exists.

    f(K) is strictly convex (second difference = ln((K+2)/(K+1)) > 0),
    with minimum at K* = round(uf) - 1 where d/dK = ln(K+1) - xf = 0.
    The set {K : f(K) <= threshold} is an interval [K1, K2]; the original
    linear scan returns K1 (it stops at the first hit).  Binary search
    returns the same K1.
    """
    if not (uf > 0.0) or not math.isfinite(uf) or uf > 1e15:
        return _orig_asym_K(xf, uf, lng, L_eps)

    top = min(v27.ASYM_KMAX, int(uf) - 1)
    if top < 0:
        return None
    threshold = -L_eps - 3.0

    def f(K):
        if K == 0:
            return lng - xf - uf
        return lng + math.lgamma(K + 1) - (K + 1) * xf - uf

    if f(0) <= threshold:
        return 0

    K_min = min(top, max(0, int(uf) - 1))
    if f(K_min) > threshold:
        return None

    lo, hi = 0, K_min   # invariant: f(lo) > thr, f(hi) <= thr
    while hi - lo > 1:
        mid = (lo + hi) // 2
        if f(mid) <= threshold:
            hi = mid
        else:
            lo = mid
    return hi


v27.asym_K = asym_K


# ---------------------------------------------------------------------------
# Re-exports for bench_nodes.py --file golomb_dickman_28.py
# (bench_nodes.py calls these by name on the loaded module object)
# ---------------------------------------------------------------------------
make_plan = v27.make_plan
solve_t = v27.solve_t
method_of = v27.method_of
node_ball = v27.node_ball
_est = v27._est
_heuristic_cf_min_u = v27._heuristic_cf_min_u
RS_M = v27.RS_M
ASYM_KMAX = v27.ASYM_KMAX


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    if hasattr(v27, "main") and callable(v27.main):
        # v27's CLI is still the entry point.  All of the patches above
        # live in v27's module globals (v27.asym_K, v27.RS_M,
        # v27._heuristic_cf_min_u), so v27's run_certificate uses them.
        v27.main()
    else:
        # Fallback: minimal CLI, certify only.
        import argparse
        ap = argparse.ArgumentParser(
            description="v28 accelerated wrapper for golomb_dickman_27")
        ap.add_argument("command", nargs="?", default="certify")
        ap.add_argument("--digits", type=int, default=100000)
        ap.add_argument("--guard", type=int, default=30)
        ap.add_argument("--jobs", type=int, default=0)
        ap.add_argument("--chunk", type=int, default=500)
        ap.add_argument("--ckpt", type=str, default=None)
        ap.add_argument("--out", type=str, default=None)
        ap.add_argument("--max-hours", type=float, default=0.0)
        ap.add_argument("--cf-min-u", type=float, default=None)
        ap.add_argument("--precision-ladder", action="store_true")
        a = ap.parse_args()

        if a.command != "certify":
            print("v28 fallback CLI only supports 'certify'; "
                  "run golomb_dickman_27.py for other commands",
                  file=sys.stderr)
            sys.exit(2)

        res = v27.run_certificate(
            D=a.digits, G=a.guard, jobs=a.jobs, chunk=a.chunk,
            ckpt=a.ckpt, out=a.out, max_hours=a.max_hours,
            cf_min_u=a.cf_min_u, precision_ladder=a.precision_ladder,
        )
        sys.exit(0 if res is not None else 1)
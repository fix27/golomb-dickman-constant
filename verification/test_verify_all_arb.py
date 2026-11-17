#!/usr/bin/env python3
"""Tests for the structural half of ``verify_all_arb.py``.

The Arb node audit itself needs ``python-flint`` and hours of CPU, so it is
exercised by the release run, not here.  What *can* be tested cheaply is the
part that decides whether a checkpoint set is even admissible:

  * the certificate parser (LF only, exact truncation, filename digits);
  * the run plan (format, dyadic step, K_L/K_R, chunk size);
  * chunk loading (restricted pickle, 4-tuple shape, name == start index);
  * coverage (contiguous, no gaps, no overlaps, exact node count).

Every fixture below is built in a temporary directory; nothing in the
repository is read or written.

Run with:

    python verification/test_verify_all_arb.py
    python verification/test_verify_all_arb.py -v
"""

from __future__ import annotations

import contextlib
import io
import json
import math
import pickle
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import verify_all_arb as V  # noqa: E402

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)


D = 20          # certificate digits
S = 70          # binary scale: must satisfy 3D < S < 4D and S >= 64
EBITS = 40      # node radius exponent, must be below S
M = 1_099_511_628  # dyadic numerator, h = M / 2^40
H_TEXT = f"{M / (1 << 40):.24e}"
THETA = math.pi / 4  # any value in (0.5, 0.8)


def truncate(value: int, scale_bits: int, digits: int) -> str:
    return str((value * 10**digits) >> scale_bits).zfill(digits)


def make_certificate(lo: int, hi: int) -> str:
    return (
        "# Golomb-Dickman test certificate\n"
        f"# S={S} lam_lo={lo}\n"
        f"# lam_hi={hi}\n"
        f"0.{truncate(lo, S, D)}\n"
    )


def make_plan(*, d: int = D, s: int = S, k_left: int = 2, k_right: int = 1,
              chunk: int = 2, h_text: str = H_TEXT, ebits: int = EBITS) -> dict:
    return {
        "format": "gd-checkpoint-v12",
        "chunk": chunk,
        "parameters": {
            "D": d,
            "G": 30,
            "h": h_text,
            "Ebits": ebits,
            "S": s,
            "K_L": k_left,
            "K_R": k_right,
        },
    }


class Fixture:
    """A minimal, internally consistent checkpoint set."""

    def __init__(self, root: Path, *, k_left: int = 2, k_right: int = 1,
                 chunk: int = 2, plan: dict | None = None,
                 lo: int | None = None, hi: int | None = None,
                 width: int = 5) -> None:
        self.root = root
        self.ckpt = root / "ckpt"
        self.ckpt.mkdir(parents=True, exist_ok=True)
        scale = 1 << S
        if lo is None:
            # Start from 0.6243299885... and slide until the whole interval
            # sits inside one decimal cell of the D-th place.
            lo = int(0.62432998854355087099 * scale)
            while truncate(lo, S, D) != truncate(lo + width, S, D):
                lo += 1
        self.lo = lo
        self.hi = hi if hi is not None else lo + width
        self.cert = root / "golomb_dickman_rd_certified.txt"
        self.cert.write_text(make_certificate(self.lo, self.hi), encoding="ascii",
                             newline="\n")
        (self.ckpt / "meta_v12.json").write_text(
            json.dumps(plan or make_plan(k_left=k_left, k_right=k_right, chunk=chunk),
                       indent=2) + "\n",
            encoding="utf-8", newline="\n")

    def chunk(self, lo: int, hi: int, *, even=(10, 20), odd=(30, 40)) -> None:
        path = self.ckpt / f"c_{lo}.pkl"
        with path.open("wb") as handle:
            pickle.dump((lo, hi, tuple(even), tuple(odd)), handle,
                        protocol=pickle.HIGHEST_PROTOCOL)

    def fill(self, k_left: int = 2, k_right: int = 1, chunk: int = 2) -> None:
        start = -k_left
        end = k_right + 1
        while start < end:
            stop = min(start + chunk, end)
            self.chunk(start, stop)
            start = stop


def structural(fixture: Fixture) -> dict:
    return V.run(fixture.ckpt, fixture.cert, structural_only=True)


class StructureHappyPath(unittest.TestCase):
    def test_accepts_a_consistent_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            report = structural(f)
            self.assertEqual(report["status"], V.NOT_RUN)  # no Arb in this test
            st = report["structure"]
            self.assertEqual(st["nodes"], 4)
            self.assertEqual(st["chunks"], 2)
            self.assertEqual(st["index_range"], [-2, 1])
            self.assertEqual(st["index_range_half_open"], [-2, 2])
            self.assertEqual(st["gaps"], 0)
            self.assertEqual(st["duplicates"], 0)
            self.assertEqual(st["step"], f"{M}/2^{V.SHIFT}")

    def test_reports_guard_digits_and_width(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            st = structural(f)["structure"]
            width = f.hi - f.lo
            expected = math.log10(width) - S * math.log10(2.0)
            self.assertAlmostEqual(st["width_log10"], expected, places=9)
            self.assertAlmostEqual(st["guard_digits"], -expected - D, places=9)


class StructureRejections(unittest.TestCase):
    def assert_fails(self, fixture: Fixture, needle: str) -> None:
        with self.assertRaises(V.AuditFailure) as ctx:
            structural(fixture)
        self.assertIn(needle, str(ctx.exception))

    def test_gap_in_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.chunk(-2, 0)
            f.chunk(1, 2)           # index 0 is not covered
            self.assert_fails(f, "coverage breaks")

    def test_overlap_in_coverage(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.chunk(-2, 0)
            f.chunk(-1, 2)          # overlaps at -1
            self.assert_fails(f, "coverage breaks")

    def test_missing_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.chunk(-2, 0)
            self.assert_fails(f, "chunk files")

    def test_chunk_larger_than_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # 8 nodes, chunk size 4 -> two files; the first carries 5 nodes.
            f = Fixture(Path(tmp),
                        plan=make_plan(k_left=4, k_right=3, chunk=4))
            f.chunk(-4, 1)
            f.chunk(1, 4)
            self.assert_fails(f, "exceed the chunk size")

    def test_chunk_name_disagrees_with_tuple(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            path = f.ckpt / "c_-2.pkl"
            with path.open("wb") as handle:
                pickle.dump((-1, 0, (10, 20), (30, 40)), handle)
            self.assert_fails(f, "file name says")

    def test_reversed_interval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            f.chunk(-2, 0, even=(20, 10))
            self.assert_fails(f, "reversed")

    def test_non_integer_endpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            # Booleans survive the restricted unpickler but are not integers.
            f.chunk(-2, 0, even=(True, False))
            self.assert_fails(f, "non-integer")

    def test_unsafe_pickle_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            (f.ckpt / "c_-2.pkl").write_bytes(b"cos\nsystem\n(S'echo pwned'\ntR.")
            self.assert_fails(f, "unsafe checkpoint")

    def test_plan_digit_count_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp), plan=make_plan(d=D + 1))
            f.fill()
            self.assert_fails(f, "plan D=")

    def test_plan_scale_mismatch(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp), plan=make_plan(s=S + 1))
            f.fill()
            self.assert_fails(f, "plan S=")

    def test_plan_step_is_not_dyadic(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp), plan=make_plan(h_text="0.001234567890123456789"))
            f.fill()
            self.assert_fails(f, "dyadic")

    def test_plan_does_not_cover_the_grid(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            # The plan starts at -3, but a chunk claims to start at -4.
            f = Fixture(Path(tmp), plan=make_plan(k_left=3, k_right=1))
            f.chunk(-4, -3)
            f.chunk(-3, -1)
            f.chunk(-1, 1)
            f.chunk(1, 2)
            self.assert_fails(f, "outside the plan")

    def test_plan_missing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            (f.ckpt / "meta_v12.json").unlink()
            with self.assertRaises(V.NotRun):
                structural(f)


class CertificateRejections(unittest.TestCase):
    def make(self, tmp: Path, text: str) -> Fixture:
        f = Fixture(tmp)
        f.fill()
        f.cert.write_text(text, encoding="utf-8", newline="")
        return f

    def test_crlf_certificate(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            raw = f.cert.read_bytes().replace(b"\n", b"\r\n")
            f.cert.write_bytes(raw)
            with self.assertRaises(V.AuditFailure) as ctx:
                structural(f)
            self.assertIn("CR", str(ctx.exception))

    def test_digits_do_not_match_the_interval(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            digits = truncate(f.lo, S, D)
            wrong = digits[:-1] + str((int(digits[-1]) + 1) % 10)
            text = make_certificate(f.lo, f.hi).replace(digits, wrong)
            f.cert.write_text(text, encoding="ascii", newline="\n")
            with self.assertRaises(V.AuditFailure) as ctx:
                structural(f)
            self.assertIn("digit line", str(ctx.exception))

    def test_interval_crosses_a_decimal_cell(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            # Slide a one-unit interval until it straddles a cell boundary.
            lo = f.lo
            while truncate(lo, S, D) == truncate(lo + 1, S, D):
                lo += 1
            f.lo, f.hi = lo, lo + 1
            f.cert.write_text(make_certificate(lo, lo + 1), encoding="ascii",
                              newline="\n")
            with self.assertRaises(V.AuditFailure) as ctx:
                structural(f)
            self.assertIn("decimal cell", str(ctx.exception))


class ContainmentAnalysis(unittest.TestCase):
    """``check_report_containment.analyse`` needs no Arb, only a report."""

    cert = {"lo": 0, "hi": 1_000_000, "S": S, "D": D}

    @staticmethod
    def report(blocks: list[dict], *, nodes: int | None = None) -> dict:
        return {
            "status": "PASS",
            "structure": {"nodes": nodes if nodes is not None else 2},
            "arb": {
                "nodes_checked": nodes if nodes is not None else 2,
                "chunks_checked": len(blocks),
                "blocks": blocks,
            },
        }

    def test_compact_report_flags_are_honoured(self) -> None:
        import check_report_containment as C

        report = {
            "status": "PASS",
            "structure": {"nodes": 2},
            "arb": {
                "nodes_checked": 2,
                "chunks_checked": 2,
                "chunks_contained": 2,
                "all_chunks_contained": True,
                "total_inside_saved": True,
                "cert_contains_total": True,
                "certificate_interval": [0, 1_000_000],
                "blocks": [
                    {"chunk": "c_1.pkl", "contained": True, "digest": "00"},
                    {"chunk": "c_3.pkl", "contained": True, "digest": "00"},
                ],
            },
        }
        self.assertEqual(C.analyse(report)["status"], C.PASS)

        report["arb"]["blocks"][1]["contained"] = False
        report["arb"]["all_chunks_contained"] = False
        self.assertEqual(C.analyse(report)["status"], C.WEAK)

    def test_verbose_report_is_recomputed(self) -> None:
        import check_report_containment as C

        blocks = [
            {"chunk": "c_1.pkl", "recomputed": [100, 200], "saved": [90, 300]},
            {"chunk": "c_3.pkl", "recomputed": [300, 400], "saved": [250, 450]},
        ]
        result = C.analyse(self.report(blocks), self.cert)
        self.assertEqual(result["status"], C.PASS)

    def test_intersection_only_is_weak(self) -> None:
        import check_report_containment as C

        blocks = [
            {"chunk": "c_1.pkl", "recomputed": [100, 200], "saved": [90, 300]},
            {"chunk": "c_3.pkl", "recomputed": [300, 700], "saved": [250, 650]},
        ]
        result = C.analyse(self.report(blocks), self.cert)
        self.assertEqual(result["status"], C.WEAK)
        self.assertEqual(result["not_contained"][0]["chunk"], "c_3.pkl")

    def test_disjoint_chunks_fail(self) -> None:
        import check_report_containment as C

        blocks = [
            {"chunk": "c_1.pkl", "recomputed": [100, 200], "saved": [90, 300]},
            {"chunk": "c_3.pkl", "recomputed": [700, 800], "saved": [250, 650]},
        ]
        result = C.analyse(self.report(blocks), self.cert)
        self.assertEqual(result["status"], C.FAIL)
        self.assertEqual(result["disjoint"], ["c_3.pkl"])

    def test_total_outside_certificate_fails(self) -> None:
        import check_report_containment as C

        blocks = [
            {"chunk": "c_1.pkl", "recomputed": [600_000, 700_000],
             "saved": [500_000, 800_000]},
        ]
        result = C.analyse(self.report(blocks), {"lo": 0, "hi": 500_000})
        self.assertEqual(result["status"], C.FAIL)
        self.assertIn("outside the published certificate", result["reason"])

    def test_partial_audit_is_not_analysed(self) -> None:
        import check_report_containment as C

        blocks = [{"chunk": "c_1.pkl", "recomputed": [100, 200], "saved": [90, 300]}]
        report = self.report(blocks)
        report["structure"]["nodes"] = 4  # only 2 nodes were recomputed
        with self.assertRaises(V.NotRun):
            C.analyse(report, self.cert)

    def test_structural_only_report_is_not_analysed(self) -> None:
        import check_report_containment as C

        with self.assertRaises(V.NotRun):
            C.analyse({"status": "NOT_RUN", "arb": None}, self.cert)


class CommandLine(unittest.TestCase):
    def run_main(self, argv: list[str]) -> tuple[int, str]:
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = V.main(argv)
        return code, out.getvalue()

    def test_structural_only_exits_2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.fill()
            code, out = self.run_main([
                "--ckpt", str(f.ckpt), "--cert", str(f.cert), "--structural-only",
            ])
            self.assertEqual(code, 2)
            self.assertIn("NOT_RUN", out)
            self.assertIn("half-open", out)

    def test_failure_exits_1(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            f = Fixture(Path(tmp))
            f.chunk(-2, 0)  # incomplete coverage
            code, out = self.run_main(["--ckpt", str(f.ckpt), "--cert", str(f.cert)])
            self.assertEqual(code, 1)
            self.assertIn("FAIL", out)


if __name__ == "__main__":
    unittest.main(verbosity=2)

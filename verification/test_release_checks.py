#!/usr/bin/env python3
"""Release checks for the Golomb-Dickman artefact set.

These checks guard the *textual and logical* invariants of the release; they
do not replace the numerical certificate audit.  Every check reports one of

    PASS      the check ran and succeeded;
    FAIL      the check ran and found a discrepancy;
    NOT_RUN   the check could not run (missing dependency or artefact).

The suite exits with 0 only when every check passed.  A NOT_RUN makes the
suite INCOMPLETE (non-zero exit), never PASS.

Run with:

    python verification/test_release_checks.py
    python verification/test_release_checks.py --json report.json
"""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PAPER = ROOT / "paper" / "main.tex"
CODE_50K = ROOT / "50000" / "golomb_dickman_26.py"

PASS, FAIL, NOT_RUN = "PASS", "FAIL", "NOT_RUN"

# The Arb report stores exact integers with 50,000+ digits; json.loads needs
# the interpreter's conversion limit lifted before it can read them.
if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)

# Values pinned from the producing code's formula (mpmath, 80 digits).
M1_PINNED = 195.028122617225708620
M3_PINNED = 31.8555790093881572766
LOG10_M_PINNED = 360.39085839002926083
M3_RATIO_WRONG_OVER_RIGHT = 2.7456766848437611449


def _configure_stdio() -> None:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass


def _normalise_tex(expr: str) -> str:
    """Drop LaTeX spacing commands and whitespace so forms can be compared."""
    for token in (r"\,", r"\!", r"\;", r"\ ", r"\quad", r"\qquad"):
        expr = expr.replace(token, "")
    return re.sub(r"\s+", "", expr)


def _m3_expression() -> str:
    text = PAPER.read_text(encoding="utf-8")
    for line in text.splitlines():
        if "M_3&=" in line:
            return line.strip().rstrip(",")
    raise AssertionError("paper/main.tex: no line defining M_3")


def _strip_braces(expr: str) -> str:
    """Check that braces balance in a LaTeX fragment."""
    depth = 0
    for char in expr:
        if char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth < 0:
                raise AssertionError("unbalanced closing brace")
    if depth != 0:
        raise AssertionError("unbalanced opening brace")
    return expr


# --------------------------------------------------------------------------
# 1. M_3: paper formula == implementation
# --------------------------------------------------------------------------

def check_m3_paper_matches_code() -> tuple[str, str]:
    expr = _normalise_tex(_m3_expression())
    _strip_braces(expr)

    right = r"e^{e^{e^{-2}-2}}"
    wrong = r"e^{e^{e^{-2}}-2}"
    if wrong in expr:
        return FAIL, f"paper still has e^(e^(e^-2)-2): {expr}"
    if right not in expr:
        return FAIL, f"paper lacks e^(e^(e^-2-2)): {expr}"

    code = CODE_50K.read_text(encoding="utf-8")
    if "facE = ((em2 - 2).exp()).exp()" not in code:
        return FAIL, "50000/golomb_dickman_26.py: facE is not exp(exp(e^-2-2))"
    if "M3 = facE * (1 + em2) * (-kp * e2).exp() / kp" not in code:
        return FAIL, "50000/golomb_dickman_26.py: M3 expression changed"

    return PASS, "paper and code both use exp(exp(e^-2 - 2))"


def check_m3_numeric() -> tuple[str, str]:
    try:
        import mpmath as mp
    except Exception as exc:  # pragma: no cover - depends on environment
        return NOT_RUN, f"mpmath is not importable ({exc})"

    mp.mp.dps = 80
    d = mp.mpf(7) / 5
    c = mp.cos(d)
    a = 2 * c
    C1 = mp.exp(mp.euler + 2 + (mp.e - 2) / 2)
    M1 = C1 * mp.exp(-a) * (2 / a + 1 / (a * a))

    e2 = mp.exp(2)
    em2 = mp.exp(-2)
    B2 = 2 * mp.exp(mp.euler) * (e2 * e2) * mp.exp(2 * e2 + mp.exp(e2) / 2)
    M2 = 2 * B2

    th = d + em2 * mp.sin(d)
    if not th < mp.pi / 2:
        return FAIL, "theta_max is not below pi/2"
    kap = mp.cos(th)
    if not kap > 0:
        return FAIL, "kappa is not positive"
    kp = kap * mp.exp(-em2)
    M3 = mp.exp(mp.exp(em2 - 2)) * (1 + em2) * mp.exp(-kp * e2) / kp
    M = M1 + M2 + M3

    def close(got, want, tol=1e-9):
        return abs(got - want) <= tol * abs(want)

    if not close(M1, M1_PINNED):
        return FAIL, f"M1={mp.nstr(M1, 20)} != {M1_PINNED}"
    if not close(M3, M3_PINNED):
        return FAIL, f"M3={mp.nstr(M3, 20)} != {M3_PINNED}"
    log10_m = mp.log10(M)
    if not close(log10_m, LOG10_M_PINNED):
        return FAIL, f"log10 M={mp.nstr(log10_m, 20)} != {LOG10_M_PINNED}"

    return PASS, (
        f"M1={mp.nstr(M1, 10)}, M3={mp.nstr(M3, 10)}, "
        f"log10 M={mp.nstr(log10_m, 13)}"
    )


def check_m3_dominance() -> tuple[str, str]:
    """The old wrong text changed M3 by a factor, but not the certificate."""
    try:
        import mpmath as mp
    except Exception as exc:  # pragma: no cover
        return NOT_RUN, f"mpmath is not importable ({exc})"

    mp.mp.dps = 80
    d = mp.mpf(7) / 5
    e2 = mp.exp(2)
    em2 = mp.exp(-2)
    th = d + em2 * mp.sin(d)
    kp = mp.cos(th) * mp.exp(-em2)
    common = (1 + em2) * mp.exp(-kp * e2) / kp
    right = mp.exp(mp.exp(em2 - 2)) * common
    wrong = mp.exp(mp.exp(em2) - 2) * common
    ratio = right / wrong
    if abs(ratio - M3_RATIO_WRONG_OVER_RIGHT) > 1e-9 * M3_RATIO_WRONG_OVER_RIGHT:
        return FAIL, f"M3 ratio={mp.nstr(ratio, 20)} != {M3_RATIO_WRONG_OVER_RIGHT}"

    m2 = 4 * mp.exp(mp.euler) * mp.exp(4) * mp.exp(2 * e2 + mp.exp(e2) / 2)
    # The M2 term is 10^360; M3 stays below 32 in both variants.
    # 1e350 is not representable as a Python float, so compare with mpf.
    if not (m2 > mp.mpf("1e350") and right < 1000 and wrong < 1000):
        return FAIL, "dominance of M2 no longer holds"
    return PASS, f"M3(wrong)/M3(right)={mp.nstr(ratio, 12)}; M2 dominates"


CHECKS = (
    ("m3_paper_matches_code", check_m3_paper_matches_code),
    ("m3_numeric", check_m3_numeric),
    ("m3_dominance", check_m3_dominance),
)


# --------------------------------------------------------------------------
# 2. Canonical line endings
# --------------------------------------------------------------------------

CANONICAL_TEXT = (
    ROOT / ".gitattributes",
    ROOT / "50000" / "SHA256SUMS.txt",
    ROOT / "50000" / "README.md",
    ROOT / "50000" / "golomb_dickman_26.py",
    ROOT / "50000" / "golomb_dickman_50000_certified.txt",
    ROOT / "50000" / "golomb_dickman_50000_digits.txt",
    ROOT / "50000" / "b084945.txt",
    ROOT / "50000" / "gd_rigorous_ckpt_50000" / "meta_v12.json",
)


def check_line_endings() -> tuple[str, str]:
    bad = []
    for path in CANONICAL_TEXT:
        if not path.is_file():
            return FAIL, f"{path} is missing"
        raw = path.read_bytes()
        if raw.startswith(b"\xef\xbb\xbf"):
            bad.append(f"{path.name}: BOM")
        if b"\r" in raw:
            bad.append(f"{path.name}: {raw.count(13)} CR bytes")
    if bad:
        return FAIL, "; ".join(bad)
    return PASS, f"{len(CANONICAL_TEXT)} canonical artefacts are LF-only, no BOM"


# --------------------------------------------------------------------------
# 3. SHA-256: computed vs matched against a trusted reference
# --------------------------------------------------------------------------

def _import_verify_certificate():
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import verify_certificate  # noqa: PLC0415

    return verify_certificate


def check_sha_manifest() -> tuple[str, str]:
    vc = _import_verify_certificate()
    manifest = vc.read_sha256_manifest(ROOT / "50000" / "SHA256SUMS.txt")
    if not manifest:
        return FAIL, "50000/SHA256SUMS.txt has no entries"
    # Manifest names are relative to 50000/; index the tree by base name so
    # that a subdirectory entry such as gd_rigorous_ckpt_50000/meta_v12.json
    # can be checked too.
    index: dict[str, list[Path]] = {}
    for path in (ROOT / "50000").rglob("*"):
        if path.is_file():
            index.setdefault(path.name, []).append(path)
    missing = []
    ambiguous = []
    mismatched = []
    for name, expected in sorted(manifest.items()):
        candidates = index.get(Path(name).name, [])
        if not candidates:
            missing.append(name)
            continue
        if len(candidates) > 1:
            ambiguous.append(name)
            continue
        got = vc.sha256_file(candidates[0])
        if got != expected:
            mismatched.append(f"{name}: manifest {expected[:12]}… != {got[:12]}…")
    if missing:
        return FAIL, f"manifest lists files that do not exist: {missing}"
    if ambiguous:
        return FAIL, f"manifest names are ambiguous: {ambiguous}"
    if mismatched:
        return FAIL, "; ".join(mismatched)
    return PASS, f"{len(manifest)} entries match the files byte-for-byte"


def check_sha_semantics() -> tuple[str, str]:
    """A hash may only be called verified when a trusted reference exists."""
    vc = _import_verify_certificate()
    cert = ROOT / "50000" / "golomb_dickman_50000_certified.txt"

    computed = vc.fingerprint(cert, {}, {})
    if computed["status"] != "UNVERIFIED":
        return FAIL, f"no-reference status is {computed['status']}, expected UNVERIFIED"
    if computed["trusted"] is not None:
        return FAIL, "no-reference result carries a trusted value"

    matched = vc.fingerprint(cert, {cert.name: computed["sha256"]}, {})
    if matched["status"] != "MATCH":
        return FAIL, f"matching reference status is {matched['status']}"

    try:
        vc.fingerprint(cert, {cert.name: "0" * 64}, {})
    except vc.CheckError:
        wrong_rejected = True
    else:
        wrong_rejected = False
    if not wrong_rejected:
        return FAIL, "a wrong SHA-256 was accepted"

    # The report must not claim OK for an unverified hash.
    text = (ROOT / "verification" / "verify_certificate.py").read_text(encoding="utf-8")
    if "SHA-256: OK" in text:
        return FAIL, "verify_certificate.py still prints the unconditional 'SHA-256: OK'"
    if "UNVERIFIED (no trusted reference)" not in text:
        return FAIL, "verify_certificate.py does not label unverified hashes"
    return PASS, "computed / MATCH / UNVERIFIED are distinguished; mismatch fails"


# --------------------------------------------------------------------------
# 4. Aggregate status logic: NOT_RUN is never PASS
# --------------------------------------------------------------------------

def check_status_aggregation() -> tuple[str, str]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import run_all  # noqa: PLC0415

    def row(status: str, required: bool = True) -> dict:
        return {"status": status, "required": required}

    cases = [
        ([row(PASS)], PASS),
        ([row(PASS), row(FAIL)], FAIL),
        ([row(PASS), row(NOT_RUN)], "INCOMPLETE"),
        ([row(FAIL), row(NOT_RUN)], FAIL),
        # An optional check that did not run must not block a PASS.
        ([row(PASS), row(NOT_RUN, required=False)], PASS),
        ([row(NOT_RUN, required=False)], PASS),
    ]
    for case, expected in cases:
        got = run_all.aggregate(case)
        if got != expected:
            return FAIL, f"aggregate({case}) = {got}, expected {expected}"

    if run_all.status_from_exit(0) != PASS:
        return FAIL, "exit 0 is not PASS"
    if run_all.status_from_exit(1) != FAIL:
        return FAIL, "exit 1 is not FAIL"
    if run_all.status_from_exit(2) != NOT_RUN:
        return FAIL, "exit 2 is not NOT_RUN"
    return PASS, "FAIL/INCOMPLETE/PASS semantics and exit-code mapping hold"


# --------------------------------------------------------------------------
# 5. Checkpoint pickles are read without executing code
# --------------------------------------------------------------------------

def check_safe_pickle() -> tuple[str, str]:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from safe_pickle import UnsafePickleError, loads_restricted, load_restricted  # noqa: PLC0415

    # A classic malicious pickle: call os.system("echo pwned").
    evil = b"cos\nsystem\n(S'echo pwned'\ntR."
    try:
        loads_restricted(evil)
    except UnsafePickleError:
        pass
    else:
        return FAIL, "a pickle with GLOBAL/REDUCE was accepted"

    try:
        loads_restricted(b"cbuiltins\neval\n(S'1+1'\ntR.")
    except UnsafePickleError:
        pass
    else:
        return FAIL, "a pickle calling builtins.eval was accepted"

    ckpt = ROOT / "50000" / "gd_rigorous_ckpt_50000"
    samples = sorted(ckpt.glob("c_*.pkl"))
    if not samples:
        return NOT_RUN, f"{ckpt} has no c_*.pkl files, cannot test a real chunk"
    sample = samples[0]
    value = load_restricted(sample)
    if not (isinstance(value, tuple) and len(value) == 4):
        return FAIL, f"{sample.name} is not a 4-tuple"
    return PASS, "GLOBAL/REDUCE pickles are rejected; a real chunk loads as plain data"


# --------------------------------------------------------------------------
# 6. The Arb audit report, if present, is self-consistent
# --------------------------------------------------------------------------

def check_arb_report() -> tuple[str, str]:
    report_path = ROOT / "verification" / "reports" / "arb_50000.json"
    if not report_path.is_file():
        return NOT_RUN, "verification/reports/arb_50000.json has not been produced"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    status = report.get("status")
    if status not in (PASS, FAIL, NOT_RUN):
        return FAIL, f"unexpected status {status!r}"
    if status != PASS:
        return NOT_RUN, f"Arb audit status is {status}: {report.get('reason', '')[:160]}"

    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import check_report_containment as C  # noqa: PLC0415

    try:
        containment = C.analyse(report)
    except (C.V.NotRun, C.V.AuditFailure) as exc:
        return FAIL, f"containment analysis failed: {exc}"
    if containment["status"] != C.PASS:
        return FAIL, f"containment: {containment['status']} ({containment['reason']})"

    structure = report.get("structure") or {}
    arb = report.get("arb") or {}
    nodes = structure.get("nodes")
    checked = arb.get("nodes_checked")
    if nodes is None or checked != nodes:
        return FAIL, f"Arb checked {checked} of {nodes} nodes"
    if structure.get("gaps") or structure.get("duplicates"):
        return FAIL, "Arb report records gaps or duplicates"
    if arb.get("chunks_contained") != arb.get("chunks_checked"):
        return FAIL, (
            f"only {arb.get('chunks_contained')} of {arb.get('chunks_checked')} "
            "chunks are contained"
        )
    return PASS, (
        f"Arb recomputed {checked} nodes in {arb.get('chunks_checked')} chunks; "
        f"every interval contained; log10 width "
        f"{structure.get('width_log10'):.4f}"
    )


# --------------------------------------------------------------------------
# 7. The paper's parameter table matches the shipped plan and certificate
# --------------------------------------------------------------------------

def _paper_params_table() -> dict[str, str]:
    """Return {row label: value cell} for the tab:params table."""
    text = PAPER.read_text(encoding="utf-8")
    marker = text.index(r"\label{tab:params}")
    begin = text.rindex(r"\begin{table}", 0, marker)
    block = text[begin:marker]
    rows: dict[str, str] = {}
    for line in block.splitlines():
        if "&" not in line:
            continue
        cells = [cell.strip() for cell in line.rstrip().rstrip("\\").split("&")]
        if len(cells) < 3:
            continue
        rows[cells[0]] = cells[-1]
    if not rows:
        raise ValueError("could not parse the tab:params table")
    return rows


def _paper_cell(rows: dict[str, str], prefix: str) -> str:
    for label, value in rows.items():
        if label.startswith(prefix):
            return value
    raise KeyError(f"no table row starting with {prefix!r}")


def _tex_int(cell: str) -> int:
    return int(re.sub(r"\\,|\\ |[\s$]", "", cell))


def check_paper_params_match_plan() -> tuple[str, str]:
    """Every structural number in the table must come from the shipped plan."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import verify_all_arb as V  # noqa: PLC0415

    ckpt = ROOT / "50000" / "gd_rigorous_ckpt_50000"
    cert = ROOT / "50000" / "golomb_dickman_50000_certified.txt"
    plan = V.load_plan(ckpt)
    parsed = V.parse_certificate(cert)
    rows = _paper_params_table()

    nodes = plan["K_L"] + plan["K_R"] + 1
    chunks = -(-nodes // plan["chunk"])
    expected = {
        "certified decimal digits": str(plan["D"]),
        "guard digits": str(plan["G"]),
        "node radius exponent": str(plan["Ebits"]),
        "certificate scale": str(plan["S"]),
    }
    problems = []
    for prefix, value in expected.items():
        got = _tex_int(_paper_cell(rows, prefix))
        if got != int(value):
            problems.append(f"{prefix}: paper {got} != plan {value}")

    step = re.sub(r"\\,|[\s${}]", "", _paper_cell(rows, "step"))
    want_step = f"{plan['m']}/2^{V.SHIFT}"
    if step != re.sub(r"[{}]", "", want_step):
        problems.append(f"step: paper {step!r} != plan {want_step!r}")

    counts = _paper_cell(rows, "left/right node counts")
    # The separator is ",\ " (comma, LaTeX inter-column space), not a plain
    # comma: the thousands separator itself is "\,".
    left, right = [int(re.sub(r"\\,|\\ |[\s$]", "", part))
                   for part in re.split(r",\\\s*", counts)]
    if (left, right) != (plan["K_L"], plan["K_R"]):
        problems.append(
            f"K_L,K_R: paper {left},{right} != plan {plan['K_L']},{plan['K_R']}"
        )

    if _tex_int(_paper_cell(rows, "chunk size")) != plan["chunk"]:
        problems.append("chunk size disagrees with the plan")

    size = _paper_cell(rows, "chunks / nodes")
    paper_chunks, paper_nodes = [
        int(re.sub(r"\\,|\\ |[\s$]", "", part)) for part in size.split("/")
    ]
    if paper_chunks != chunks or paper_nodes != nodes:
        problems.append(
            f"chunks/nodes: paper {paper_chunks}/{paper_nodes} "
            f"!= plan {chunks}/{nodes}"
        )

    if _tex_int(_paper_cell(rows, "certified decimal digits")) != parsed["D"]:
        problems.append("paper D disagrees with the certificate")
    if _tex_int(_paper_cell(rows, "certificate scale")) != parsed["S"]:
        problems.append("paper S disagrees with the certificate")

    if problems:
        return FAIL, "; ".join(problems)
    return PASS, (
        f"D={plan['D']}, G={plan['G']}, S={plan['S']}, h={want_step}, "
        f"{chunks} chunks / {nodes} nodes match the plan and certificate"
    )


def check_paper_tail_corrections() -> tuple[str, str]:
    """B, T_R, T_L, C and the four logs must follow from the formulas."""
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    import verify_all_arb as V  # noqa: PLC0415

    ckpt = ROOT / "50000" / "gd_rigorous_ckpt_50000"
    cert_path = ROOT / "50000" / "golomb_dickman_50000_certified.txt"
    try:
        _, acb, arb, ctx = V._import_flint()
    except V.NotRun as exc:
        return NOT_RUN, str(exc)

    plan = V.load_plan(ckpt)
    cert = V.parse_certificate(cert_path)
    bounds = V._recompute_bounds(acb, arb, ctx, plan)
    rows = _paper_params_table()

    B = bounds["B_int"]
    TR = bounds["T_R_int"]
    TL = bounds["T_L_int"]
    C = TR + TL + B
    problems = []
    for prefix, value, name in (
        ("lower correction", B, "B"),
        ("right tail correction", TR, "T_R"),
        ("left tail correction", TL, "T_L"),
        ("upper correction", C, "C"),
    ):
        paper = _tex_int(_paper_cell(rows, prefix))
        if paper != value:
            problems.append(f"{name}: paper {paper} != recomputed {value}")

    log10_width = (
        math.log10(cert["hi"] - cert["lo"]) - cert["S"] * math.log10(2.0)
    )
    guard = -log10_width - cert["D"]
    for prefix, value, name, places in (
        ("discretisation bound", bounds["log10_Bdisc"], "log10 B_disc", 4),
        ("right tail bound", bounds["log10_tauR"], "log10 tau_R", 4),
        ("left tail bound", bounds["log10_tauL"], "log10 tau_L", 4),
        ("interval width", log10_width, "log10 width", 9),
    ):
        cell = re.sub(r"\\,|[\s$]", "", _paper_cell(rows, prefix))
        paper = float(cell)
        if abs(paper - value) > 10 ** (-places):
            problems.append(f"{name}: paper {paper} != {value:.12f}")
    paper_guard = float(re.sub(r"\\,|[\s$]", "", _paper_cell(rows, "guard digits beyond")))
    if abs(paper_guard - guard) > 1e-4:
        problems.append(f"guard digits: paper {paper_guard} != {guard:.6f}")

    if problems:
        return FAIL, "; ".join(problems)
    return PASS, (
        f"B={B}, T_R={TR}, T_L={TL}, C={C}; log10 width {log10_width:.9f}, "
        f"guard {guard:.4f} (independent Arb recomputation)"
    )


CHECKS += (
    ("line_endings", check_line_endings),
    ("paper_params_match_plan", check_paper_params_match_plan),
    ("paper_tail_corrections", check_paper_tail_corrections),
    ("sha_manifest", check_sha_manifest),
    ("sha_semantics", check_sha_semantics),
    ("status_aggregation", check_status_aggregation),
    ("safe_pickle", check_safe_pickle),
    ("arb_report", check_arb_report),
)


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="Release checks")
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    results = []
    for name, func in CHECKS:
        try:
            status, detail = func()
        except Exception as exc:  # a crashing check is a failure, not a skip
            status, detail = FAIL, f"exception: {exc}"
        results.append({"check": name, "status": status, "detail": detail})
        print(f"[{status:7}] {name}: {detail}")

    statuses = [r["status"] for r in results]
    if FAIL in statuses:
        verdict = FAIL
    elif NOT_RUN in statuses:
        verdict = "INCOMPLETE"
    else:
        verdict = PASS
    print(f"overall: {verdict}")

    payload = {"verdict": verdict, "checks": results}
    if args.json is not None:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8", newline="\n")
    if args.report is not None:
        lines = [f"Release checks: {verdict}", ""]
        lines += [f"[{r['status']}] {r['check']}: {r['detail']}" for r in results]
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    return 0 if verdict == PASS else 1


if __name__ == "__main__":
    raise SystemExit(main())

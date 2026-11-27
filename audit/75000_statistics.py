#!/usr/bin/env python3
"""Statistical and structural analysis of the 75,000-digit lambda expansion.

Read-only with respect to the certificate.  Everything is computed from the
standalone digit file; optional plots are written to a separate directory.

Usage:
    python audit/75000_statistics.py \
        --digits golomb_dickman_75000_digits.txt \
        --json <temp>/stats75.json \
        --plots audit/plots

The script deliberately reports p-values without claiming that a finite
string proves normality.  Normality of the Golomb--Dickman constant remains
an open problem; all tests below are descriptive/numerical evidence only.
"""

from __future__ import annotations

import argparse
import hashlib
import heapq
import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
from scipy import stats

if hasattr(sys, "set_int_max_str_digits"):
    sys.set_int_max_str_digits(1_000_000)


def canonical_hash(digits: str) -> str:
    return hashlib.sha256((digits + "\n").encode("ascii")).hexdigest()


def chi2_p(observed: np.ndarray, expected: float, df: int) -> dict[str, object]:
    stat = float(np.sum((observed - expected) ** 2 / expected))
    return {
        "chi2": round(stat, 6),
        "df": df,
        "p": float(stats.chi2.sf(stat, df)),
    }


# ---------------------------------------------------------------------------
# 1. Frequency and deviation analysis
# ---------------------------------------------------------------------------

def frequency_tests(arr: np.ndarray) -> dict[str, object]:
    out: dict[str, object] = {}
    for n in (10, 100, 1_000, 10_000, len(arr)):
        counts = np.bincount(arr[:n], minlength=10)
        expected = n / 10
        z = (counts - expected) / math.sqrt(expected * 0.9)
        info = chi2_p(counts, expected, 9)
        info.update(
            {
                "counts": counts.tolist(),
                "max_abs_z": round(float(np.max(np.abs(z))), 4),
                "max_z_digit": int(np.argmax(np.abs(z))),
            }
        )
        out[str(n)] = info
    return out


# ---------------------------------------------------------------------------
# 2. Serial tests, runs, entropy
# ---------------------------------------------------------------------------

def ngram_values(arr: np.ndarray, k: int) -> np.ndarray:
    vals = np.zeros(len(arr) - k + 1, dtype=np.int64)
    for j in range(k):
        vals = vals * 10 + arr[j : len(arr) - k + 1 + j].astype(np.int64)
    return vals


def serial_tests(arr: np.ndarray) -> dict[str, object]:
    out: dict[str, object] = {}
    for k in (1, 2, 3, 4):
        vals = ngram_values(arr, k)
        bins = 10**k
        counts = np.bincount(vals, minlength=bins)
        expected = len(vals) / bins
        info = chi2_p(counts, expected, bins - 1)
        info.update(
            {
                "window_count": int(len(vals)),
                "expected_per_cell": round(float(expected), 4),
                "min_cell": int(counts.min()),
                "max_cell": int(counts.max()),
            }
        )
        if k >= 3:
            info["chi2_note"] = "large-df approximation; expected cell count is small"
        out[f"k={k}"] = info
    return out


def _up_down_runs(b: np.ndarray) -> int:
    ud = (b[1:] > b[:-1]).astype(np.int8)
    mask = b[1:] != b[:-1]
    s = ud[mask]
    return 1 + int(np.count_nonzero(s[1:] != s[:-1]))


def runs_test(arr: np.ndarray, simulations: int = 200) -> dict[str, object]:
    def one(cat: np.ndarray, label: str) -> dict[str, object]:
        n1 = int(np.count_nonzero(cat == 1))
        n2 = int(np.count_nonzero(cat == 0))
        changes = int(np.count_nonzero(cat[1:] != cat[:-1]))
        runs = changes + 1
        n = n1 + n2
        mean = 1 + (2 * n1 * n2) / n
        var = (2 * n1 * n2 * (2 * n1 * n2 - n1 - n2)) / (n * n * (n - 1))
        z = (runs - mean) / math.sqrt(var)
        return {
            "kind": label,
            "n1": n1,
            "n2": n2,
            "runs": runs,
            "expected_runs": round(mean, 3),
            "z": round(z, 4),
            "p_two_sided": float(2 * stats.norm.sf(abs(z))),
        }

    b = arr.astype(np.int16)
    observed = _up_down_runs(b)
    # Ties make the closed-form Wald--Wolfowitz variance invalid; calibrate
    # the null distribution by simulation of uniform decimal digits.
    rng = np.random.default_rng(20261128)
    sample = np.array(
        [_up_down_runs(rng.integers(0, 10, len(b)).astype(np.int16)) for _ in range(simulations)],
        dtype=float,
    )
    mean, sd = float(sample.mean()), float(sample.std(ddof=1))
    z = (observed - mean) / sd
    ud_info = {
        "kind": "up/down (Monte Carlo null, ties removed)",
        "runs": observed,
        "simulated_mean": round(mean, 3),
        "simulated_sd": round(sd, 3),
        "simulations": simulations,
        "z": round(z, 4),
        "p_two_sided": float(2 * stats.norm.sf(abs(z))),
    }
    equal = (b[1:] == b[:-1]).astype(np.int8)
    return {"up_down": ud_info, "equal_unequal": one(equal, "equal/unequal")}


def entropy_tests(arr: np.ndarray) -> dict[str, object]:
    n = len(arr)
    out: dict[str, object] = {}
    for k in (1, 2, 3, 4, 5):
        vals = ngram_values(arr, k)
        counts = np.bincount(vals, minlength=10**k).astype(float)
        p = counts[counts > 0] / len(vals)
        h = float(-np.sum(p * np.log2(p)))
        # Miller--Madow bias correction for unseen cells
        observed_cells = int(np.count_nonzero(counts))
        h_mm = h + (10**k - observed_cells) / (2 * len(vals) * math.log(2))
        out[f"k={k}"] = {
            "entropy_bits_per_block": round(h, 6),
            "entropy_bits_per_digit": round(h / k, 6),
            "corrected_bits_per_digit": round(h_mm / k, 6),
            "max_bits_per_digit": round(math.log2(10), 6),
            "deficit_bits_per_digit": round(math.log2(10) - h / k, 6),
            "observed_cells": observed_cells,
        }
    return out


# ---------------------------------------------------------------------------
# 3. Autocorrelation and spectrum
# ---------------------------------------------------------------------------

def autocorrelation(arr: np.ndarray, max_lag: int = 500) -> dict[str, object]:
    x = arr.astype(float) - 4.5
    denom = float(np.dot(x, x))
    rs = np.array([float(np.dot(x[:-lag], x[lag:])) / denom for lag in range(1, max_lag + 1)])
    sigma = 1 / math.sqrt(len(x))
    top = np.argsort(np.abs(rs))[-10:][::-1]
    return {
        "max_lag": max_lag,
        "sigma": round(sigma, 6),
        "three_sigma": round(3 * sigma, 6),
        "max_abs_r": round(float(np.max(np.abs(rs))), 6),
        "max_abs_lag": int(np.argmax(np.abs(rs))) + 1,
        "count_beyond_3sigma": int(np.count_nonzero(np.abs(rs) > 3 * sigma)),
        "count_beyond_bonferroni": int(np.count_nonzero(np.abs(rs) > sigma * math.sqrt(2 * math.log(max_lag / 0.05)))),
        "top_lags": [
            {"lag": int(i + 1), "r": round(float(rs[i]), 6)} for i in top
        ],
        "series": [round(float(v), 6) for v in rs],
    }


def spectral(arr: np.ndarray) -> dict[str, object]:
    x = arr.astype(float) - 4.5
    power = np.abs(np.fft.rfft(x))[1:] ** 2
    mean = float(np.mean(power))
    top = np.argsort(power)[-10:][::-1]
    return {
        "mean_power": round(mean, 3),
        "top_peaks": [
            {
                "frequency_bin": int(i + 1),
                "period": round(len(x) / (i + 1), 3),
                "power_over_mean": round(float(power[i] / mean), 3),
            }
            for i in top
        ],
    }


# ---------------------------------------------------------------------------
# 4. Pattern search: KMP, suffix automaton, Manacher, monotone runs
# ---------------------------------------------------------------------------

def kmp_all(text: str, pattern: str, limit: int = 20) -> dict[str, object]:
    pi = [0] * len(pattern)
    j = 0
    for i in range(1, len(pattern)):
        while j and pattern[i] != pattern[j]:
            j = pi[j - 1]
        if pattern[i] == pattern[j]:
            j += 1
        pi[i] = j
    hits: list[int] = []
    j = 0
    for i, ch in enumerate(text):
        while j and ch != pattern[j]:
            j = pi[j - 1]
        if ch == pattern[j]:
            j += 1
        if j == len(pattern):
            hits.append(i - len(pattern) + 1)
            j = pi[j - 1]
            if len(hits) >= limit:
                break
    return {"pattern": pattern, "count_up_to_limit": len(hits), "first_0based": hits[:limit]}


def longest_repeat(text: str) -> dict[str, object]:
    """Longest repeated substring by doubling hash + binary search.

    A suffix automaton gave wrong occurrence counts on this input, so the
    simpler (and independently verifiable) rolling-hash method is used.
    The final answer is re-counted with str.count, so a hash collision
    cannot be reported as a result.
    """
    mod1, mod2, base = 1_000_000_007, 1_000_000_009, 10
    n = len(text)
    h1 = [0] * (n + 1)
    h2 = [0] * (n + 1)
    for i, ch in enumerate(text):
        d = ord(ch) - 48
        h1[i + 1] = (h1[i] * base + d) % mod1
        h2[i + 1] = (h2[i] * base + d) % mod2

    def duplicate_at(length: int) -> int | None:
        p1 = pow(base, length, mod1)
        p2 = pow(base, length, mod2)
        seen: dict[tuple[int, int], int] = {}
        for i in range(n - length + 1):
            j = i + length
            key = (
                (h1[j] - h1[i] * p1) % mod1,
                (h2[j] - h2[i] * p2) % mod2,
            )
            if key in seen:
                return i
            seen[key] = i
        return None

    lo, hi, best = 1, n - 1, 0
    while lo <= hi:
        mid = (lo + hi) // 2
        if duplicate_at(mid) is not None:
            best = mid
            lo = mid + 1
        else:
            hi = mid - 1
    if best == 0:
        return {"length": 0, "occurrences": 0, "first_0based": None, "substring": ""}
    pos = duplicate_at(best)
    assert pos is not None
    sub = text[pos : pos + best]
    positions = [i for i in range(n - best + 1) if text.startswith(sub, i)]
    return {
        "length": best,
        "occurrences": len(positions),
        "first_0based": positions[0],
        "all_positions_0based": positions[:20],
        "substring": sub,
        "method": "double modular rolling hash; result re-counted exactly",
    }


def longest_palindrome(text: str) -> dict[str, object]:
    n = len(text)
    best_len, best_center = 0, 0
    # odd
    for center in range(n):
        l = r = center
        while l >= 0 and r < n and text[l] == text[r]:
            l -= 1
            r += 1
        cur = r - l - 1
        if cur > best_len:
            best_len, best_center = cur, l + 1
    # even
    for center in range(n - 1):
        l, r = center, center + 1
        while l >= 0 and r < n and text[l] == text[r]:
            l -= 1
            r += 1
        cur = r - l - 1
        if cur > best_len:
            best_len, best_center = cur, l + 1
    return {
        "length": best_len,
        "start_0based": best_center,
        "palindrome": text[best_center : best_center + best_len],
    }


def monotone_runs(arr: np.ndarray) -> dict[str, object]:
    out: dict[str, object] = {}
    for strict in (True, False):
        for direction in ("increasing", "decreasing"):
            best = cur = 1
            best_at = cur_at = 0
            for i in range(1, len(arr)):
                a, b = int(arr[i - 1]), int(arr[i])
                ok = (b > a if strict else b >= a) if direction == "increasing" else (b < a if strict else b <= a)
                cur = cur + 1 if ok else 1
                if cur > best:
                    best, best_at = cur, i - cur + 1
            out[f"{'strict' if strict else 'weak'}_{direction}"] = {
                "length": best,
                "start_0based": best_at,
            }
    return out


# ---------------------------------------------------------------------------
# 5. Compression and PPM-style entropy estimation
# ---------------------------------------------------------------------------

def huffman_bits(data: bytes) -> dict[str, object]:
    counts = np.bincount(np.frombuffer(data, dtype=np.uint8), minlength=256)
    heap = [(int(c), i) for i, c in enumerate(counts) if c > 0]
    heapq.heapify(heap)
    total = 0
    while len(heap) > 1:
        w1, _ = heapq.heappop(heap)
        w2, _ = heapq.heappop(heap)
        total += w1 + w2
        heapq.heappush(heap, (w1 + w2, -1))
    return {
        "bits": total,
        "bits_per_symbol": round(total / len(data), 6),
        "bytes_equivalent": round(total / 8, 2),
    }


def ppm_cross_entropy(digits: str, order: int, alpha: float = 1.0) -> float:
    counts: dict[tuple[str, ...], list[int]] = {}
    total_bits = 0.0
    for t in range(order, len(digits)):
        ctx = tuple(digits[t - order : t]) if order else ()
        row = counts.setdefault(ctx, [0] * 10)
        denom = sum(row) + 10 * alpha
        prob = (row[int(digits[t])] + alpha) / denom
        total_bits += -math.log2(prob)
        row[int(digits[t])] += 1
    return total_bits / (len(digits) - order)


def compression_tests(digits: str) -> dict[str, object]:
    import bz2
    import lzma
    import zlib

    raw = digits.encode("ascii")
    out: dict[str, object] = {
        "raw_bytes": len(raw),
        "entropy_lower_bound_bytes": round(len(raw) * math.log2(10) / 8, 2),
        "huffman": huffman_bits(raw),
    }
    for name, fn in (
        ("zlib9", lambda b: zlib.compress(b, 9)),
        ("bz2", bz2.compress),
        ("lzma", lzma.compress),
    ):
        packed = fn(raw)
        out[name] = {
            "bytes": len(packed),
            "ratio_to_raw": round(len(packed) / len(raw), 6),
            "bits_per_digit": round(8 * len(packed) / len(raw), 6),
        }
    out["ppm_adaptive_bits_per_digit"] = {
        f"order={m}": round(ppm_cross_entropy(digits, m), 6) for m in (0, 1, 2, 3)
    }
    return out


# ---------------------------------------------------------------------------
# 6. de Bruijn graph / subword complexity
# ---------------------------------------------------------------------------

def subword_complexity(arr: np.ndarray) -> dict[str, object]:
    out: dict[str, object] = {}
    for k in (1, 2, 3, 4, 5, 6):
        vals = ngram_values(arr, k)
        distinct = int(np.unique(vals).size)
        windows = int(len(vals))
        cells = 10**k
        item = {
            "windows": windows,
            "distinct": distinct,
            "cells": cells,
            "expected_distinct_if_uniform": min(cells, windows),
            "collisions": windows - distinct,
        }
        if cells <= windows:
            item["missing_cells"] = cells - distinct
        out[f"k={k}"] = item
    return out


# ---------------------------------------------------------------------------
# 7. Random walk and box-counting dimension
# ---------------------------------------------------------------------------

def random_walk(arr: np.ndarray) -> dict[str, object]:
    steps = arr.astype(np.int64) * 2 - 9  # -9, -7, ..., 9; mean zero
    pos = np.cumsum(steps)
    scales = [8, 16, 32, 64, 128, 256, 512]
    counts = []
    span = max(1, int(max(abs(pos.min()), abs(pos.max()))))
    for s in scales:
        x_cell = (np.arange(len(pos)) * s // len(pos)).tolist()
        y_cell = (pos * s // span).tolist()
        counts.append(len(set(zip(x_cell, y_cell))))
    slope, _ = np.polyfit(np.log([1 / s for s in scales]), np.log(counts), 1)
    dimension = -slope
    return {
        "step_mapping": "2*d-9 (integer, mean zero)",
        "endpoint": int(pos[-1]),
        "minimum": int(pos.min()),
        "maximum": int(pos.max()),
        "rms_displacement": round(float(math.sqrt(np.mean(pos.astype(float) ** 2))), 3),
        "zero_crossings": int(np.count_nonzero(np.signbit(pos[1:]) != np.signbit(pos[:-1]))),
        "box_counting": {
            "scales": scales,
            "occupied_cells": counts,
            "estimated_dimension": round(float(dimension), 4),
        },
    }


# ---------------------------------------------------------------------------
# 8. Continued fractions and rational approximations
# ---------------------------------------------------------------------------

def continued_fraction(digits: str, terms: int = 80) -> dict[str, object]:
    n = int(digits)
    m = 10 ** len(digits)
    n0, m0 = n, m
    partials: list[int] = [0]  # a_0 = 0 because 0 < lambda < 1
    p_prev, p = 1, 0
    q_prev, q = 0, 1
    best: dict[str, object] | None = None
    for _ in range(terms):
        if n == 0:
            break
        a = m // n
        partials.append(a)
        p_prev, p = p, a * p + p_prev
        q_prev, q = q, a * q + q_prev
        rem = m - a * n
        m, n = n, rem
        if 0 < q <= 10**6:
            err10 = math.log10(abs(n0 * q - p * m0)) - math.log10(m0) - math.log10(q)
            if best is None or err10 < best["log10_error"]:
                best = {
                    "numerator_digits": len(str(p)),
                    "denominator": q,
                    "log10_error": err10,
                }
    logs = [math.log(a) for a in partials[2:] if a > 0]
    khinchin = math.exp(sum(logs) / len(logs)) if logs else None
    return {
        "partial_quotients": partials[:20],
        "terms_computed": len(partials),
        "largest_partial_quotient": max(partials) if partials else None,
        "geometric_mean_partial_quotient": round(khinchin, 6) if khinchin else None,
        "khinchin_constant": 2.6854520010,
        "best_approximation_with_q_le_1e6": best,
    }


# ---------------------------------------------------------------------------
# 9. NIST-like bit tests, next-digit baselines, comparisons
# ---------------------------------------------------------------------------

def nist_like_bits(arr: np.ndarray) -> dict[str, object]:
    bits = (arr % 2).astype(np.int8)
    n = len(bits)
    ones = int(bits.sum())
    z = (ones - n / 2) / math.sqrt(n / 4)
    block = 128
    nb = n // block
    props = bits[: nb * block].reshape(nb, block).mean(axis=1)
    chi = 4 * block * float(np.sum((props - 0.5) ** 2))
    # runs on bits
    n1, n2 = ones, n - ones
    runs = 1 + int(np.count_nonzero(bits[1:] != bits[:-1]))
    mean = 1 + 2 * n1 * n2 / n
    var = 2 * n1 * n2 * (2 * n1 * n2 - n1 - n2) / (n * n * (n - 1))
    zr = (runs - mean) / math.sqrt(var)
    csum = np.cumsum(bits.astype(float) * 2 - 1)
    return {
        "monobit": {"ones": ones, "z": round(z, 4), "p": float(2 * stats.norm.sf(abs(z)))},
        "block_frequency_128": {
            "blocks": nb,
            "chi2": round(chi, 3),
            "df": nb,
            "p": float(stats.chi2.sf(chi, nb)),
        },
        "runs": {"runs": runs, "expected": round(mean, 2), "z": round(zr, 4), "p": float(2 * stats.norm.sf(abs(zr)))},
        "cumulative_sums": {
            "max_abs": float(np.max(np.abs(csum))),
            "threshold_95pct": round(1.36 * math.sqrt(n), 2),
            "within_95pct": bool(np.max(np.abs(csum)) < 1.36 * math.sqrt(n)),
        },
    }


def block_anomalies(arr: np.ndarray, block: int = 100) -> dict[str, object]:
    n_blocks = len(arr) // block
    ps: list[float] = []
    max_chi = 0.0
    for b in range(n_blocks):
        counts = np.bincount(arr[b * block : (b + 1) * block], minlength=10)
        info = chi2_p(counts, block / 10, 9)
        ps.append(float(info["p"]))
        max_chi = max(max_chi, float(info["chi2"]))
    ps_arr = np.array(ps)
    return {
        "block_size": block,
        "blocks": n_blocks,
        "count_p_below_0_01": int(np.count_nonzero(ps_arr < 0.01)),
        "expected_at_alpha_0_01": round(n_blocks * 0.01, 2),
        "minimum_p": round(float(ps_arr.min()), 6),
        "maximum_chi2": round(max_chi, 4),
    }


def berlekamp_massey(bits: list[int]) -> int:
    """Linear complexity over GF(2) of the parity-bit sequence."""
    c = [1]
    b = [1]
    L, m = 0, 1
    for n in range(len(bits)):
        if len(c) <= L:
            c.extend([0] * (L + 1 - len(c)))
        d = bits[n]
        for i in range(1, L + 1):
            d ^= c[i] & bits[n - i]
        if d:
            t = c[:]
            if len(b) + m > len(c):
                c.extend([0] * (len(b) + m - len(c)))
            for i, value in enumerate(b):
                c[i + m] ^= value
            if 2 * L <= n:
                L = n + 1 - L
                b = t
                m = 1
            else:
                m += 1
    return L


def next_bit_baseline(digits: str, train_frac: float = 13 / 15) -> dict[str, object]:
    cut = int(len(digits) * train_frac)
    train, test = digits[:cut], digits[cut:]
    tb = [int(ch) & 1 for ch in train]
    eb = [int(ch) & 1 for ch in test]
    majority = 1 if sum(tb) > len(tb) / 2 else 0
    acc_majority = sum(b == majority for b in eb) / len(eb)
    table = {0: {0: 0, 1: 0}, 1: {0: 0, 1: 0}}
    for i in range(1, len(tb)):
        table[tb[i - 1]][tb[i]] += 1
    correct = 0
    for i in range(1, len(eb)):
        row = table[eb[i - 1]]
        guess = 1 if row[1] > row[0] else 0
        correct += guess == eb[i]
    return {
        "majority_bit": majority,
        "majority_accuracy": round(acc_majority, 6),
        "markov1_accuracy": round(correct / (len(eb) - 1), 6),
        "linear_complexity_sample_bits": 2_000,
        "linear_complexity_first_2000": berlekamp_massey([int(ch) & 1 for ch in digits[:2000]]),
        "linear_complexity_target": 1_000,
    }


def next_digit_baselines(digits: str, train_frac: float = 13 / 15) -> dict[str, object]:
    cut = int(len(digits) * train_frac)
    train, test = digits[:cut], digits[cut:]
    majority = max("0123456789", key=train.count)
    acc_majority = test.count(majority) / len(test)

    def markov(order: int) -> float:
        table: dict[str, dict[str, int]] = {}
        for i in range(order, len(train)):
            ctx = train[i - order : i]
            table.setdefault(ctx, {})[train[i]] = table.setdefault(ctx, {}).get(train[i], 0) + 1
        correct = 0
        for i in range(order, len(test)):
            ctx = test[i - order : i]
            row = table.get(ctx)
            guess = max(row, key=row.get) if row else majority
            correct += guess == test[i]
        return correct / (len(test) - order)

    # Multiclass perceptron on one-hot previous digit + bias.
    rng = np.random.default_rng(20261128)
    w = rng.normal(0, 0.01, (10, 11))
    x_train = np.zeros((len(train) - 1, 11), dtype=float)
    x_train[np.arange(len(train) - 1), np.frombuffer(train[:-1].encode("ascii"), dtype=np.uint8) - 48] = 1
    x_train[:, 10] = 1
    y_train = np.frombuffer(train[1:].encode("ascii"), dtype=np.uint8) - 48
    for i in range(len(x_train)):
        scores = x_train[i] @ w.T
        pred = int(np.argmax(scores))
        if pred != y_train[i]:
            w[pred] -= 0.1 * x_train[i]
            w[y_train[i]] += 0.1 * x_train[i]
    x_test = np.zeros((len(test) - 1, 11), dtype=float)
    x_test[np.arange(len(test) - 1), np.frombuffer(test[:-1].encode("ascii"), dtype=np.uint8) - 48] = 1
    x_test[:, 10] = 1
    y_test = np.frombuffer(test[1:].encode("ascii"), dtype=np.uint8) - 48
    acc_perceptron = float(np.mean(np.argmax(x_test @ w.T, axis=1) == y_test))
    return {
        "train_digits": len(train),
        "test_digits": len(test),
        "chance": 0.1,
        "majority_digit": majority,
        "majority_accuracy": round(acc_majority, 6),
        "markov1_accuracy": round(markov(1), 6),
        "markov2_accuracy": round(markov(2), 6),
        "perceptron_accuracy": round(acc_perceptron, 6),
    }


def comparisons(lambda_digits: str, n: int = 10_000) -> dict[str, object]:
    import mpmath as mp

    prev = mp.mp.dps
    mp.mp.dps = n + 40
    strings: dict[str, str] = {}
    for name, value in (
        ("pi", mp.pi - 3),
        ("e", mp.e - 2),
        ("sqrt2", mp.sqrt(2) - 1),
    ):
        s = mp.nstr(value, n + 10, strip_zeros=False)
        strings[name] = "".join(ch for ch in s.split(".", 1)[1][:n] if ch.isdigit())
    mp.mp.dps = prev
    rng = random.Random(20261128)
    strings["prng_seed_20261128"] = "".join(str(rng.randrange(10)) for _ in range(n))
    strings["lambda"] = lambda_digits[:n]

    out: dict[str, object] = {"digits_compared": n}
    for name, s in strings.items():
        a = np.frombuffer(s.encode("ascii"), dtype=np.uint8) - 48
        counts = np.bincount(a, minlength=10)
        x = a.astype(float) - 4.5
        r1 = float(np.dot(x[:-1], x[1:]) / np.dot(x, x))
        packed = __import__("zlib").compress(s.encode("ascii"), 9)
        out[name] = {
            "chi2_p": chi2_p(counts, n / 10, 9)["p"],
            "entropy_bits_per_digit": round(
                float(-np.sum(counts[counts > 0] / n * np.log2(counts[counts > 0] / n))), 6
            ),
            "lag1_autocorr": round(r1, 6),
            "zlib_bits_per_digit": round(8 * len(packed) / n, 6),
        }
    ref = np.frombuffer(strings["lambda"].encode("ascii"), dtype=np.uint8).astype(float) - 4.5
    corr: dict[str, float] = {}
    for name, s in strings.items():
        if name == "lambda":
            continue
        v = np.frombuffer(s.encode("ascii"), dtype=np.uint8).astype(float) - 4.5
        corr[name] = round(float(np.corrcoef(ref, v)[0, 1]), 6)
    out["cross_correlation_with_lambda"] = corr
    return out


# ---------------------------------------------------------------------------
# 10. Plots
# ---------------------------------------------------------------------------

def make_plots(digits: str, out_dir: Path) -> dict[str, str]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    arr = np.frombuffer(digits.encode("ascii"), dtype=np.uint8) - 48
    paths: dict[str, str] = {}

    steps = arr.astype(np.int64) * 2 - 9
    pos = np.cumsum(steps)
    fig, ax = plt.subplots(figsize=(10, 3.2))
    ax.plot(pos, lw=0.25, color="#2457a6")
    ax.set_title("Lambda digits: integer random walk (step = 2d-9)")
    ax.set_xlabel("digit position")
    ax.set_ylabel("position")
    fig.tight_layout()
    p = out_dir / "walk.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths["walk"] = p.as_posix()

    trans = np.zeros((10, 10), dtype=int)
    for a, b in zip(arr[:-1], arr[1:]):
        trans[a, b] += 1
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    im = ax.imshow(trans, cmap="viridis")
    ax.set_title("Digit-to-digit transition counts")
    ax.set_xlabel("next digit")
    ax.set_ylabel("current digit")
    fig.colorbar(im, ax=ax, shrink=0.8)
    fig.tight_layout()
    p = out_dir / "transitions.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths["transitions"] = p.as_posix()

    x = arr.astype(float) - 4.5
    lags = np.arange(1, 201)
    rs = np.array([float(np.dot(x[:-l], x[l:]) / np.dot(x, x)) for l in lags])
    fig, ax = plt.subplots(figsize=(9, 3.2))
    ax.plot(lags, rs, lw=0.8, color="#7a3db8")
    ax.axhline(3 / math.sqrt(len(x)), color="red", lw=0.8, ls="--", label="3 sigma")
    ax.axhline(-3 / math.sqrt(len(x)), color="red", lw=0.8, ls="--")
    ax.set_title("Digit-value autocorrelation, lags 1..200")
    ax.set_xlabel("lag")
    ax.set_ylabel("r")
    ax.legend(loc="upper right")
    fig.tight_layout()
    p = out_dir / "autocorr.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    paths["autocorr"] = p.as_posix()
    return paths


# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--digits", type=Path, default=Path("golomb_dickman_75000_digits.txt"))
    parser.add_argument("--json", type=Path, default=None)
    parser.add_argument("--plots", type=Path, default=None)
    parser.add_argument("--no-heavy", action="store_true", help="skip CF, comparisons, plots")
    args = parser.parse_args(argv)

    started = time.monotonic()
    digits = args.digits.read_text(encoding="ascii").strip()
    if not digits.isdigit() or len(digits) < 10_000:
        raise SystemExit("digit file must contain at least 10,000 ASCII digits")
    arr = np.frombuffer(digits.encode("ascii"), dtype=np.uint8) - 48
    report: dict[str, object] = {
        "input": str(args.digits),
        "digit_count": len(digits),
        "sha256_canonical": canonical_hash(digits),
    }

    report["frequency"] = frequency_tests(arr)
    report["serial"] = serial_tests(arr)
    report["runs"] = runs_test(arr)
    report["entropy"] = entropy_tests(arr)
    report["autocorrelation"] = autocorrelation(arr)
    report["spectral"] = spectral(arr)
    report["patterns"] = {
        "kmp": [
            kmp_all(digits, p)
            for p in (
                "0123456789",
                "9876543210",
                "6243299885",
                "77777",
                "55555",
                "666666",
                "1891192031",
                "05224342250",
            )
        ],
        "longest_repeat": longest_repeat(digits),
        "longest_palindrome": longest_palindrome(digits),
        "monotone_runs": monotone_runs(arr),
    }
    report["compression"] = compression_tests(digits)
    report["subword_complexity"] = subword_complexity(arr)
    report["random_walk"] = random_walk(arr)
    report["nist_like_bits"] = nist_like_bits(arr)
    report["block_anomalies"] = block_anomalies(arr)
    report["next_digit_baselines"] = next_digit_baselines(digits)
    report["next_bit_baseline"] = next_bit_baseline(digits)
    if not args.no_heavy:
        report["continued_fraction"] = continued_fraction(digits)
        report["comparisons_10000_digits"] = comparisons(digits)
        if args.plots is not None:
            report["plots"] = make_plots(digits, args.plots)
    report["seconds"] = round(time.monotonic() - started, 2)

    text = json.dumps(report, indent=2, ensure_ascii=False)
    if args.json is not None:
        # write_bytes avoids platform-dependent CRLF translation: every text
        # artefact in this repository is required to be canonical LF.
        args.json.write_bytes((text + "\n").encode("utf-8"))
    print(f"OK: {len(digits)} digits analysed in {report['seconds']} s")
    print(json.dumps({k: report[k] for k in ("frequency", "runs", "next_digit_baselines")}, indent=2)[:3000])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

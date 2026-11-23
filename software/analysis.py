"""
analysis.py - session-level grip analysis on top of the app's filters.py and metrics.py.

Input: the raw session CSV written by grip_test.save_session() and by the website's "Raw CSV" export:
    hand,trial,test,time_ms,force_kg

Adds to what metrics.py already gives (peak, time to peak, RFD, fatigue index, asymmetry):
    sustained force   best mean force over any 1 s window, and mean force over the 30 s hold
    impulse           force-time integral from onset (N*s)
    fatigue indices   three common definitions, because papers do not agree on one:
                        FI_peak_last1s  (peak - mean of final 1 s) / peak     (same as metrics.fatigue_index_pct)
                        decline_rate    slope of force from peak to end of hold, % of peak per second
                        endurance_ratio mean of last 5 s / mean of first 5 s after the peak
    left/right        best of each hand, L/R ratio, dominant-hand asymmetry index, CV across trials

All numbers are computed on the filtered curve (4th-order zero-phase Butterworth, as in the app).
Forces are only as good as the calibration: until G3 they are datasheet-scaled estimates.
"""
from __future__ import annotations

import csv
import io
import json
import math
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import filters  # noqa: E402  (repo root, Samuel's module: imported, not modified)
import metrics  # noqa: E402

HOLD_MS = 30_000


def load_session_csv(text: str) -> dict:
    """{(hand, trial, test): [readings]} with time restarting at 0 for each trial."""
    trials = defaultdict(list)
    for r in csv.DictReader(io.StringIO(text)):
        key = (r["hand"].strip().lower(), int(r["trial"]), r["test"].strip().lower())
        trials[key].append({"time_ms": int(float(r["time_ms"])), "force_kg": float(r["force_kg"])})
    out = {}
    for key, rs in trials.items():
        rs.sort(key=lambda x: x["time_ms"])
        t0 = rs[0]["time_ms"]
        out[key] = [{"time_ms": x["time_ms"] - t0, "force_kg": x["force_kg"]} for x in rs]
    return out


def _mean(xs):
    return sum(xs) / len(xs) if xs else None


def best_window_mean(readings, window_ms=1000):
    """Highest mean force over any window of `window_ms` (two-pointer scan). None if the trial is shorter."""
    if not readings or readings[-1]["time_ms"] - readings[0]["time_ms"] < window_ms:
        return None
    best, j, total = -math.inf, 0, 0.0
    for i, r in enumerate(readings):
        total += r["force_kg"]
        while r["time_ms"] - readings[j]["time_ms"] > window_ms:
            total -= readings[j]["force_kg"]
            j += 1
        if r["time_ms"] - readings[0]["time_ms"] >= window_ms:
            best = max(best, total / (i - j + 1))
    return best


def impulse_n_s(readings, start_ms=None, end_ms=None):
    """Trapezoid integral of force (N) over time (s) between start_ms (default: onset) and end_ms."""
    if len(readings) < 2:
        return None
    start = metrics.find_onset(readings)["time_ms"] if start_ms is None else start_ms
    end = readings[-1]["time_ms"] if end_ms is None else end_ms
    pts = [r for r in readings if start <= r["time_ms"] <= end]
    return sum((b["time_ms"] - a["time_ms"]) / 1000 * (a["force_kg"] + b["force_kg"]) / 2 * metrics.G
               for a, b in zip(pts, pts[1:])) if len(pts) >= 2 else None


def hold_metrics(readings, hold_ms=HOLD_MS):
    """Metrics for the sustained (fatigue) squeeze, measured from onset over `hold_ms`."""
    peak = metrics.find_peak(readings)
    onset = metrics.find_onset(readings)["time_ms"]
    end = onset + hold_ms
    in_hold = [r for r in readings if onset <= r["time_ms"] <= end]
    after_peak = [r for r in in_hold if r["time_ms"] >= peak["time_ms"]]
    out = {"peak_kg": peak["force_kg"], "hold_complete": bool(readings) and readings[-1]["time_ms"] >= end - 50,
           "mean_hold_kg": _mean([r["force_kg"] for r in in_hold]),
           "best_1s_kg": best_window_mean(readings), "impulse_n_s": impulse_n_s(readings, onset, end),
           "fi_peak_last1s_pct": metrics.fatigue_index_pct(readings, squeeze_ms=hold_ms),
           "decline_rate_pct_per_s": None, "endurance_ratio_pct": None}
    if len(after_peak) >= 3 and peak["force_kg"] > 0:
        xs = [r["time_ms"] / 1000 for r in after_peak]
        ys = [r["force_kg"] for r in after_peak]
        slope, _ = metrics.fit_line(xs, ys)
        out["decline_rate_pct_per_s"] = -slope / peak["force_kg"] * 100
        t_peak = peak["time_ms"]
        first = [r["force_kg"] for r in after_peak if r["time_ms"] <= t_peak + 5000]
        last = [r["force_kg"] for r in after_peak if r["time_ms"] >= end - 5000]
        if first and last and _mean(first) > 0 and end - 5000 > t_peak + 5000:
            out["endurance_ratio_pct"] = _mean(last) / _mean(first) * 100
    return out


def trial_summary(readings, test):
    smooth = filters.filter_readings(readings)
    m = metrics.trial_metrics(smooth)
    m["peak_raw_kg"] = max(r["force_kg"] for r in readings)   # filtered peak can ring above this (see tests)
    m["rate_hz"] = filters.estimate_rate_hz(readings)
    m["best_1s_kg"] = best_window_mean(smooth)
    m["impulse_n_s"] = impulse_n_s(smooth)
    if test == "fatigue":
        m.update(hold_metrics(smooth))
    return m


def cv_pct(values):
    if len(values) < 2 or _mean(values) == 0:
        return None
    mu = _mean(values)
    return math.sqrt(sum((v - mu) ** 2 for v in values) / (len(values) - 1)) / mu * 100


def left_right(per_trial: dict, dominant: str | None = None):
    """Best maximal trial per hand, ratio, asymmetry, repeatability."""
    best, peaks = {}, defaultdict(list)
    for (hand, trial, test), m in per_trial.items():
        if test != "max":
            continue
        peaks[hand].append(m["peak_kg"])
        if hand not in best or m["peak_kg"] > best[hand]["peak_kg"]:
            best[hand] = {"trial": trial, **m}
    out = {"best": best, "cv_pct": {h: cv_pct(v) for h, v in peaks.items()}, "ratio_l_over_r": None,
           "weaker_pct": None, "asymmetry_index_pct": None, "dominant": dominant}
    if "left" in best and "right" in best:
        ratio, weaker = metrics.asymmetry(best["left"]["peak_kg"], best["right"]["peak_kg"])
        out["ratio_l_over_r"], out["weaker_pct"] = ratio, weaker
        if dominant in ("left", "right"):
            d = best[dominant]["peak_kg"]
            nd = best["left" if dominant == "right" else "right"]["peak_kg"]
            out["asymmetry_index_pct"] = (d - nd) / d * 100 if d > 0 else None   # + = dominant stronger
    return out


def analyze_session(trials: dict, dominant: str | None = None, calibration: str = "estimated") -> dict:
    per = {k: trial_summary(v, k[2]) for k, v in sorted(trials.items())}
    return {"calibration": calibration,
            "note": "Forces are datasheet-scaled estimates until the G3 known-mass calibration."
            if calibration != "measured" else "Forces use a measured calibration.",
            "trials": [{"hand": h, "trial": t, "test": test, **m} for (h, t, test), m in per.items()],
            "left_right": left_right(per, dominant)}


def _num(x, d=2):
    return "" if x is None or (isinstance(x, float) and not math.isfinite(x)) else round(x, d)


def summary_csv(result: dict) -> str:
    cols = ["hand", "trial", "test", "peak_kg", "peak_raw_kg", "time_to_peak_ms", "rfd_n_per_s", "best_1s_kg", "impulse_n_s",
            "mean_hold_kg", "fi_peak_last1s_pct", "decline_rate_pct_per_s", "endurance_ratio_pct", "rate_hz"]
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(cols)
    for t in result["trials"]:
        w.writerow([t.get(c) if c in ("hand", "trial", "test") else _num(t.get(c)) for c in cols])
    lr = result["left_right"]
    w.writerow(["left_right_ratio", _num(lr["ratio_l_over_r"], 3)])
    w.writerow(["weaker_hand_pct", _num(lr["weaker_pct"], 1)])
    w.writerow(["asymmetry_index_pct", _num(lr["asymmetry_index_pct"], 1)])
    return buf.getvalue()


def summary_json(result: dict) -> str:
    def clean(o):
        if isinstance(o, float):
            return None if not math.isfinite(o) else round(o, 4)
        if isinstance(o, dict):
            return {k: clean(v) for k, v in o.items()}
        if isinstance(o, list):
            return [clean(v) for v in o]
        return o
    return json.dumps(clean(result), indent=1)

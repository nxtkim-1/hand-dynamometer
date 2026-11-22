"""
Analysis tests on [SIMULATED] traces with known answers: hand-built shapes where peak, sustained force,
impulse and fatigue can be worked out by hand, plus synthetic sessions run end to end through the CLI.
"""
import json
import math
import subprocess
import sys
from pathlib import Path

import pytest

import analysis as A
from synthetic_cell import CellModel, squeeze_profile

SOFTWARE = Path(__file__).resolve().parent.parent


def flat(kg, seconds, rate=50):
    return [{"time_ms": int(i * 1000 / rate), "force_kg": kg} for i in range(int(seconds * rate) + 1)]


def linear_decline(peak, end, seconds, rate=50, lead_s=1.0):
    """Zero for lead_s, a jump to `peak`, then a straight decline to `end` over `seconds`."""
    rs = [{"time_ms": int(i * 1000 / rate), "force_kg": 0.0} for i in range(int(lead_s * rate))]
    n = int(seconds * rate)
    for i in range(n + 1):
        rs.append({"time_ms": int((lead_s + i / rate) * 1000), "force_kg": peak + (end - peak) * i / n})
    return rs


def test_best_1s_window_on_a_plateau():
    rs = flat(0, 1) + [{"time_ms": 1000 + r["time_ms"], "force_kg": 30.0} for r in flat(30, 2)][1:]
    assert A.best_window_mean(rs) == pytest.approx(30.0)
    assert A.best_window_mean(flat(5, 0.5)) is None            # shorter than the window


def test_impulse_of_a_constant_force():
    # 20 kg for 2 s = 20 * 9.81 N * 2 s = 392.4 N*s
    assert A.impulse_n_s(flat(20, 2), start_ms=0) == pytest.approx(392.4, rel=1e-6)


def test_hold_metrics_on_a_linear_decline():
    rs = linear_decline(peak=40, end=20, seconds=30)            # onset at 1 s, falls 0.6667 kg/s
    h = A.hold_metrics(rs)
    assert h["peak_kg"] == 40 and h["hold_complete"]
    assert h["mean_hold_kg"] == pytest.approx(30, abs=0.05)
    assert h["decline_rate_pct_per_s"] == pytest.approx(20 / 30 / 40 * 100, rel=1e-3)   # 1.667 %/s
    # final second averages 20.33 kg -> (40 - 20.33)/40
    assert h["fi_peak_last1s_pct"] == pytest.approx((40 - 20.333) / 40 * 100, abs=0.2)
    # first 5 s mean 38.33, last 5 s mean 21.67 -> 56.5 %
    assert h["endurance_ratio_pct"] == pytest.approx(21.667 / 38.333 * 100, abs=0.3)
    assert h["impulse_n_s"] == pytest.approx(30 * 30 * 9.81, rel=0.002)


def test_incomplete_hold_is_reported():
    h = A.hold_metrics(linear_decline(40, 30, seconds=12))
    assert not h["hold_complete"]


def session_csv(dominant="right", right_peak=34.0, left_peak=31.0, rate=10, seed=4):
    """A full simulated protocol through the synthetic cell, written like the website's raw CSV."""
    model = CellModel(rate_hz=rate, noise_counts=70, seed=seed)
    rows = ["hand,trial,test,time_ms,force_kg"]
    other = "left" if dominant == "right" else "right"
    for trial in (1, 2, 3):
        for hand in (dominant, other):
            peak = (right_peak if hand == "right" else left_peak) * (1 - 0.02 * (trial - 1))
            for line in model.stream(squeeze_profile(peak, 5, rate, "max")):
                t, _, _, kg = line.split(",")
                rows.append(f"{hand},{trial},max,{t},{kg}")
    for line in model.stream(squeeze_profile(right_peak if dominant == "right" else left_peak, 32, rate, "hold")):
        t, _, _, kg = line.split(",")
        rows.append(f"{dominant},1,fatigue,{t},{kg}")
    return "\n".join(rows) + "\n"


def test_full_session_left_right_and_fatigue():
    trials = A.load_session_csv(session_csv())
    assert len(trials) == 7
    res = A.analyze_session(trials, dominant="right")
    lr = res["left_right"]
    # firmware prints force with the datasheet factor, the model's true factor is 44100: forces read 2.7 % high
    scale = 44_100 / 42_952
    assert lr["best"]["right"]["trial"] == 1 and lr["best"]["left"]["trial"] == 1
    # profile peaks at 0.971 x 34 kg (rise x hold-decay at 10 Hz sampling); filtered peak may ring up to ~2.5 % above
    best_r = lr["best"]["right"]
    assert best_r["peak_raw_kg"] == pytest.approx(0.971 * 34 * scale, rel=0.01)
    assert 0 <= best_r["peak_kg"] / best_r["peak_raw_kg"] - 1 < 0.025
    assert lr["ratio_l_over_r"] == pytest.approx(31 / 34, abs=0.03)
    assert lr["asymmetry_index_pct"] == pytest.approx((34 - 31) / 34 * 100, abs=3)
    fat = next(t for t in res["trials"] if t["test"] == "fatigue")
    assert fat["rate_hz"] == pytest.approx(10, abs=0.1) and fat["rfd_n_per_s"] is None   # 10 Hz -> RFD n/a
    assert 35 < fat["fi_peak_last1s_pct"] < 55 and fat["endurance_ratio_pct"] < 85
    assert "estimates" in res["note"]


def test_exports_are_valid_and_have_no_nans():
    res = A.analyze_session(A.load_session_csv(session_csv()), dominant="right")
    data = json.loads(A.summary_json(res))
    assert len(data["trials"]) == 7
    csv_text = A.summary_csv(res)
    assert csv_text.splitlines()[0].startswith("hand,trial,test,peak_kg")
    assert "nan" not in csv_text.lower() and "left_right_ratio" in csv_text


def test_analyze_session_cli(tmp_path):
    raw = tmp_path / "p01_raw.csv"
    raw.write_text(session_csv(dominant="left", right_peak=30, left_peak=33))
    out = subprocess.run([sys.executable, str(SOFTWARE / "analyze_session.py"), str(raw), "--dominant", "left", "--plot"],
                         capture_output=True, text=True, timeout=180)
    assert out.returncode == 0, out.stderr
    assert "datasheet-scaled" in out.stdout
    for suffix in ("_analysis.json", "_analysis.csv", "_curves.png"):
        assert (tmp_path / f"p01_raw{suffix}").exists()
    data = json.loads((tmp_path / "p01_raw_analysis.json").read_text())
    assert data["left_right"]["asymmetry_index_pct"] > 0          # dominant (left) is the stronger hand here


@pytest.mark.parametrize("rate, limit_pct", [(10, 2.5), (50, 2.0), (80, 0.5)])
def test_filter_overshoot_on_fast_squeeze_is_characterised(rate, limit_pct):
    """
    [SIMULATED] Known limitation of filters.filter_readings (Samuel's module): on a fast rise the zero-phase
    Butterworth rings, so the filtered peak sits slightly ABOVE the highest raw sample. Measured over 20 seeds:
    up to ~2.1 % at 10 Hz, ~1.5 % at 50 Hz, ~0.2 % at 80 Hz. This test pins the size so a change is noticed.
    """
    import filters
    worst = 0.0
    for seed in range(1, 21):
        model = CellModel(rate_hz=rate, seed=seed)
        rs = [{"time_ms": int(l.split(",")[0]) - 1234, "force_kg": float(l.split(",")[3])}
              for l in model.stream(squeeze_profile(34.0, 5, rate, "max"))]
        raw = max(r["force_kg"] for r in rs)
        worst = max(worst, max(r["force_kg"] for r in filters.filter_readings(rs)) / raw - 1)
    assert worst * 100 < limit_pct

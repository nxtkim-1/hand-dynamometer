"""
Pipeline tests. Every dataset here is [SIMULATED] by software/synthetic_cell.py, whose true parameters are
known, so the tests can check that the pipeline recovers them. Passing says the code is right, not that
the device is accurate.
"""
import subprocess
import sys
from pathlib import Path

import pytest

import pipeline as P
from synthetic_cell import CellModel, staircase

SOFTWARE = Path(__file__).resolve().parent.parent
# the G3 plate plan from docs/HANDOFF.md, in kg (lb x 0.45359237); top step 72.5 lb = 32.9 kg < 34 kg limit
PLAN_KG = [x * 0.45359237 for x in (0, 5, 10, 17.5, 25, 35, 45, 55, 65, 72.5)]


# ---------------------------------------------------------------- parsing

def test_parse_firmware_boot_comments_and_data():
    model = CellModel(seed=3)
    lines = model.stream([0.0] * 5, boot=True) + ["# tared", "garbage", "12,abc,3,1.0", ""]
    parsed = P.parse_firmware_lines(lines)
    assert len(parsed.samples) == 5
    assert parsed.calibration == "estimated"
    assert parsed.skipped == ["t_ms,raw,net,force_kg", "garbage", "12,abc,3,1.0"]
    assert "# tared" in parsed.comments


def test_parse_simulator_two_column_format():
    parsed = P.parse_firmware_lines(["0,1.25", "20,2.50", "40,nan"])
    assert [s.force_kg for s in parsed.samples] == [1.25, 2.5]
    assert parsed.samples[0].net is None and parsed.skipped == ["40,nan"]


# ---------------------------------------------------------------- stream checks

def test_rate_at_10hz_flags_rfd_impossible():
    parsed = P.parse_firmware_lines(CellModel(rate_hz=10).stream([0.0] * 100))
    rep = P.check_stream(parsed.samples)
    assert rep.rate_hz == pytest.approx(10, abs=0.05)
    assert not rep.rfd_possible and rep.dropouts == 0 and rep.restarts == 0
    assert any("RFD" in p for p in rep.problems())


def test_rate_at_80hz_with_integer_millis():
    parsed = P.parse_firmware_lines(CellModel(rate_hz=80).stream([0.0] * 400))
    rep = P.check_stream(parsed.samples)
    assert rep.rate_hz == pytest.approx(80, abs=0.3) and rep.rfd_possible


def test_dropout_and_nano_restart_are_detected():
    model = CellModel()
    lines = model.stream([0.0] * 20, start_ms=1000)
    lines += model.stream([0.0] * 20, start_ms=4000)      # 1 s of missing samples
    lines += model.stream([0.0] * 20, start_ms=50)        # clock went back: the Nano rebooted
    rep = P.check_stream(P.parse_firmware_lines(lines).samples)
    assert rep.dropouts == 1 and rep.longest_gap_ms >= 1000
    assert rep.restarts == 1
    assert any("re-tares" in p for p in rep.problems())


def test_rest_stats_recover_noise_and_drift():
    model = CellModel(noise_counts=70, drift_counts_per_s=5.0, seed=11)
    samples = P.parse_firmware_lines(model.stream([0.0] * 600)).samples   # 60 s at rest
    rs = P.rest_stats(samples)
    assert rs.sd_net == pytest.approx(70, rel=0.15)
    assert rs.drift_counts_per_s == pytest.approx(5.0, abs=1.0)
    assert rs.noise_kg == pytest.approx(70 / 42952, rel=0.15)        # about 1.6 g, matches the bench note


# ---------------------------------------------------------------- calibration

def test_fit_recovers_true_counts_per_kg_from_g3_staircase():
    model = CellModel(true_counts_per_kg=44_100, seed=5)
    points, _ = staircase(model, PLAN_KG, runs=3)
    fit = P.fit_calibration(points, source="simulated")
    assert fit.counts_per_kg == pytest.approx(44_100, rel=0.003)
    assert abs(fit.intercept_counts) < 300
    assert fit.n_points == 3 * (len(PLAN_KG) * 2 - 1) and fit.n_runs == 3
    assert fit.range_kg == (0.0, pytest.approx(32.885, abs=0.01))
    # hysteresis model: +-300 counts at FS -> about 2 x 300 x 0.33 = 197 counts at the top common mass
    assert fit.hysteresis_pct_fs == pytest.approx(100 * 2 * 300 * (65 * 0.45359237 / 100) / (44_100 * 100), rel=0.25)
    assert fit.repeatability_pct_fs < 0.01
    assert fit.source == "simulated" and "SIMULATED" in fit.report()


def test_fit_matches_old_calibrate_maths_on_example_file():
    """Same numbers as the previous numpy implementation of calibrate.py (np.polyfit)."""
    np = pytest.importorskip("numpy")
    text = (SOFTWARE.parent / "data" / "example_calibration_points.csv").read_text()
    rows = P.read_points_csv(text)
    fit = P.fit_calibration(rows, source="simulated")
    m = np.array([r["mass_kg"] for r in rows])
    c = np.array([r["net_counts"] for r in rows])
    slope, intercept = np.polyfit(m, c, 1)
    assert fit.counts_per_kg == pytest.approx(slope, rel=1e-9)
    assert fit.intercept_counts == pytest.approx(intercept, abs=1e-6)
    resid = c - (slope * m + intercept)
    assert fit.nonlinearity_pct_fs == pytest.approx(100 * np.max(np.abs(resid)) / abs(slope * 100), rel=1e-9)


def test_curvature_check_flags_a_bent_cell_but_not_a_straight_one():
    straight = P.fit_calibration(staircase(CellModel(nonlinearity=0.0, hysteresis_counts_fs=0, seed=2), PLAN_KG)[0], "simulated")
    bent = P.fit_calibration(staircase(CellModel(nonlinearity=0.05, hysteresis_counts_fs=0, seed=2), PLAN_KG)[0], "simulated")
    assert not straight.curvature_significant
    assert bent.curvature_significant and bent.curvature_counts_per_kg2 > 0


def test_lb_template_and_unfilled_rows():
    text = "mass_lb,net_counts,direction,run\n0,10,up,1\n10,195000,up,1\n25,,up,1\n"
    rows = P.read_points_csv(text)
    assert len(rows) == 2 and rows[1]["mass_kg"] == pytest.approx(4.5359237)


@pytest.mark.parametrize("points, msg", [
    ([{"mass_kg": 0, "net_counts": 0, "direction": "up", "run": 1}] * 3, "at least 4"),
    ([{"mass_kg": m, "net_counts": m, "direction": "up", "run": 1} for m in (0, 0, 5, 5)], "3 different"),
])
def test_fit_rejects_bad_input(points, msg):
    with pytest.raises(ValueError, match=msg):
        P.fit_calibration(points, source="measured")


def test_source_must_be_declared_honestly():
    with pytest.raises(ValueError, match="measured"):
        P.fit_calibration([], source="calibrated")


def test_apply_calibration_rescales_old_recordings():
    model = CellModel(true_counts_per_kg=44_100, noise_counts=0, nonlinearity=0, hysteresis_counts_fs=0)
    fit = P.fit_calibration(staircase(model, PLAN_KG, runs=1)[0], "simulated")
    samples = P.parse_firmware_lines(model.stream([20.0] * 5)).samples
    # the firmware printed force with the datasheet factor (wrong by 44100/42952); the new fit fixes it
    assert samples[0].force_kg == pytest.approx(20 * 44_100 / 42_952, rel=1e-3)
    assert P.apply_calibration(samples, fit) == pytest.approx([20.0] * 5, abs=0.01)


# ---------------------------------------------------------------- units

@pytest.mark.parametrize("value, frm, to, want", [
    (1, "kg", "N", 9.81), (9.81, "N", "kg", 1), (1, "kg", "lb", 2.2046226), (75, "lb", "kg", 34.019428),
    (100, "N", "lb", 100 / 9.81 * 2.2046226218),   # G = 9.81, same as metrics.G
])
def test_convert(value, frm, to, want):
    assert P.convert(value, frm, to) == pytest.approx(want, rel=1e-6)


def test_convert_rejects_unknown_unit():
    with pytest.raises(ValueError):
        P.convert(1, "kg", "stone")


# ---------------------------------------------------------------- session log

def test_session_log_round_trip_keeps_metadata():
    log = P.SessionLog(calibration="estimated", counts_per_kg=42952, source="simulated", label="hold_left", rate_hz=10)
    for s in P.parse_firmware_lines(CellModel().stream([0, 5, 10])).samples:
        log.add(s)
    meta, samples = P.SessionLog.read(log.to_csv())
    assert meta["calibration"] == "estimated" and meta["source"] == "simulated" and meta["rate_hz"] == 10
    assert [s.net for s in samples] == [s.net for s in log.samples]


def test_session_log_refuses_vague_labels():
    with pytest.raises(ValueError):
        P.SessionLog(calibration="calibrated", counts_per_kg=1, source="device")
    with pytest.raises(ValueError):
        P.SessionLog(calibration="estimated", counts_per_kg=1, source="real")


# ---------------------------------------------------------------- calibrate.py CLI

def test_calibrate_cli_end_to_end(tmp_path):
    points, _ = staircase(CellModel(seed=9), PLAN_KG, runs=2)
    csv = tmp_path / "pts.csv"
    csv.write_text("mass_kg,net_counts,direction,run\n" +
                   "".join(f"{p['mass_kg']},{p['net_counts']},{p['direction']},{p['run']}\n" for p in points))
    out = subprocess.run([sys.executable, str(SOFTWARE / "calibrate.py"), str(csv), "--source", "simulated"],
                         cwd=tmp_path, capture_output=True, text=True, timeout=120)
    assert out.returncode == 0, out.stderr
    assert "source: SIMULATED" in out.stdout and "COUNTS_PER_KG" in out.stdout
    assert (tmp_path / "calibration_fit.png").exists() and (tmp_path / "calibration_residuals.png").exists()

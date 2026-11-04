"""Metrics are checked on curves whose correct answer is known in advance."""
import metrics


def line_curve(rate_hz, slope_kg_per_s, seconds=2):
    """A force that rises in a perfectly straight line from t = 0."""
    dt = 1000 // rate_hz
    return [{"time_ms": i * dt, "force_kg": slope_kg_per_s * i * dt / 1000}
            for i in range(int(seconds * rate_hz))]


def test_rfd_of_straight_line_equals_its_slope():
    curve = line_curve(50, slope_kg_per_s=10)        # 10 kg/s = 98.1 N/s
    assert abs(metrics.rfd_n_per_s(curve) - 10 * metrics.G) < 0.5


def test_rfd_is_none_when_sampling_is_too_slow():
    curve = line_curve(10, slope_kg_per_s=10)        # only 3 points in 200 ms
    assert metrics.rfd_n_per_s(curve) is None


def test_peak_and_time_to_peak():
    curve = [{"time_ms": t, "force_kg": f} for t, f in
             [(0, 0), (20, 0), (40, 5), (60, 30), (80, 20)]]
    assert metrics.find_peak(curve)["force_kg"] == 30
    assert metrics.time_to_peak_ms(curve) == 20      # onset at 40 ms, peak at 60 ms


def test_fatigue_index_of_known_decline():
    # 30 kg at onset, then 15 kg for the rest of the 30 s -> 50 % decline
    curve = [{"time_ms": t, "force_kg": 30 if t == 0 else 15} for t in range(0, 32000, 20)]
    assert abs(metrics.fatigue_index_pct(curve) - 50) < 0.01


def test_asymmetry_known_values_and_zero_force():
    ratio, weaker = metrics.asymmetry(30, 40)
    assert abs(ratio - 0.75) < 1e-9 and abs(weaker - 25) < 1e-9
    assert metrics.asymmetry(0, 40) == (None, None)  # no crash when a hand produced nothing

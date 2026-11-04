"""The filter must adapt to the real sample rate and must not shift the curve in time."""
import math

import filters


def squeeze(rate_hz, seconds=5):
    dt = 1000 / rate_hz
    out = []
    for i in range(int(seconds * rate_hz)):
        t = i * dt / 1000
        f = 0.0 if t < 0.5 else 34 * (1 - math.exp(-(t - 0.5) / 0.15))
        out.append({"time_ms": round(i * dt), "force_kg": f})
    return out


def test_estimate_rate_hz():
    assert round(filters.estimate_rate_hz(squeeze(50))) == 50
    assert round(filters.estimate_rate_hz(squeeze(10))) == 10
    assert round(filters.estimate_rate_hz(squeeze(80))) == 80


def test_filter_does_not_shift_the_rise():
    """Zero-phase: the moment force first passes 50 % must not move."""
    raw = squeeze(50)
    smooth = filters.filter_readings(raw)
    def t_half(c):
        return next(r["time_ms"] for r in c if r["force_kg"] >= 17)
    assert abs(t_half(smooth) - t_half(raw)) <= 20   # within one sample


def test_original_curve_is_not_changed():
    raw = squeeze(50)
    before = [dict(r) for r in raw]
    filters.filter_readings(raw)
    assert raw == before


def test_slow_and_short_inputs_do_not_crash():
    assert len(filters.filter_readings(squeeze(10))) == 50    # 10 Hz: cutoff lowered automatically
    short = squeeze(50, seconds=0.2)
    assert filters.filter_readings(short)[3]["force_kg"] == round(short[3]["force_kg"], 3)

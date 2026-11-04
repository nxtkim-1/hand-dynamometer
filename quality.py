"""
quality.py - Decide whether a maximal trial looks valid.
Labels: good, false_start, slip, submaximal
Two methods:
  - rule_check: fixed thresholds written by hand
  - ml_check:   a Random Forest trained by train_quality.py
"""

import statistics
from pathlib import Path

import metrics

MODEL_PATH = Path(__file__).parent / "models" / "quality_model.joblib"
FEATURE_NAMES = ["baseline_frac", "rise_time_ms", "dip_frac", "hold_cv", "peak_kg"]

_model = None  

def first_time_above(readings, level):
    for r in readings:
        if r["force_kg"] >= level:
            return r["time_ms"]
    return readings[-1]["time_ms"]

def extract_features(readings):
    """Five numbers that describe the shape of one curve."""
    peak = metrics.find_peak(readings)["force_kg"]
    if peak <= 0:
        return {name: 0.0 for name in FEATURE_NAMES}

    # 1. How much force was already there before the squeeze?
    start_ms = readings[0]["time_ms"]
    baseline = [r["force_kg"] for r in readings if r["time_ms"] - start_ms <= 300]
    baseline_frac = statistics.mean(baseline) / peak

    # 2. How long did it take to go from 10% to 90% of the peak?
    rise_time_ms = (first_time_above(readings, 0.9 * peak)
                    - first_time_above(readings, 0.1 * peak))

    # 3-4. During the hold (above 80% of peak), how far and how much did it wobble?
    above = [i for i, r in enumerate(readings) if r["force_kg"] >= 0.8 * peak]
    hold = [r["force_kg"] for r in readings[above[0]: above[-1] + 1]]
    dip_frac = (peak - min(hold)) / peak
    hold_cv = statistics.pstdev(hold) / statistics.mean(hold)

    return {"baseline_frac": baseline_frac, "rise_time_ms": rise_time_ms,
            "dip_frac": dip_frac, "hold_cv": hold_cv, "peak_kg": peak}


def rule_check(features):
    if features["baseline_frac"] > 0.10:
        return "false_start"
    if features["dip_frac"] > 0.25:
        return "slip"
    if features["rise_time_ms"] > 600:
        return "submaximal"
    return "good"

def ml_check(features):
    global _model
    if _model is None:
        import joblib
        _model = joblib.load(MODEL_PATH)
    import pandas as pd
    row = pd.DataFrame([features])[FEATURE_NAMES]
    return _model.predict(row)[0]

def check_trial(readings):
    """Use the trained model if it exists, otherwise the rules."""
    features = extract_features(readings)
    if MODEL_PATH.exists():
        try:
            return {"label": ml_check(features), "method": "ml", "features": features}
        except Exception:
            # e.g. the model was saved by a different scikit-learn version on another computer:
            # fall back to the rules instead of stopping the test
            pass
    return {"label": rule_check(features), "method": "rules", "features": features}

if __name__ == "__main__":
    import random
    import fake_data
    import filters

    random.seed(1)
    for kind in fake_data.TRIAL_KINDS:
        readings = fake_data.lines_to_readings(fake_data.generate_curve(34.0, kind))
        smooth = filters.filter_readings(readings)
        f = extract_features(smooth)
        print(f"{kind:12} -> rules say {rule_check(f):12} "
              f"baseline {f['baseline_frac']:.2f}, rise {f['rise_time_ms']} ms, "
              f"dip {f['dip_frac']:.2f}")
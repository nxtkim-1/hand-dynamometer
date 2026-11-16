"""
make_fixtures.py - Reference answers from the Python app, for the website's parity tests.

The website re-implements filters.py, metrics.py, quality.py and grip_compare.py in TypeScript.
This script runs the ORIGINAL Python code on fixed inputs and saves its answers to
src/lib/__fixtures__/reference.json. The Vitest suite then checks that the TypeScript gives the
same numbers, so the two copies cannot drift apart without a failing test.

Run from the website folder after changing any of those Python files:
    python scripts/make_fixtures.py        (or: npm run fixtures)
"""

import json
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent.parent
sys.path.insert(0, str(REPO))

import fake_data  # noqa: E402
import filters  # noqa: E402
import grip_compare  # noqa: E402
import metrics  # noqa: E402
import quality  # noqa: E402

# Force the pure-Python Butterworth even if scipy is installed: it is the code that was ported
# (and it matches scipy to about 1e-12).
filters.butter = None
filters.filtfilt = None


def firmware_lines(rate_hz, peak_kg, seconds=5):
    """A curve in the firmware's 4-column format with integer millisecond timestamps."""
    random.seed(7)
    base = fake_data.max_grip_curve(peak_kg, seconds)
    readings = fake_data.lines_to_readings(base)
    step = round(fake_data.SAMPLE_RATE_HZ / rate_hz) if rate_hz < fake_data.SAMPLE_RATE_HZ else 1
    out = ["# hand_dynamometer_v1", "# calibration=estimated (datasheet, about +/-10 %)", "t_ms,raw,net,force_kg"]
    t0 = 1234
    for r in readings[::step]:
        net = int(r["force_kg"] * 42952)
        out.append(f"{t0 + r['time_ms']},{52400 + net},{net},{r['force_kg']:.3f}")
    return out


def case(name, lines, test="max"):
    readings = []
    first = None
    for line in lines:
        parts = line.split(",")
        try:
            t, f = int(parts[0]), float(parts[-1])
        except ValueError:
            continue
        if len(parts) < 2:
            continue
        first = t if first is None else first
        readings.append({"time_ms": t - first, "force_kg": f})
    smooth = filters.filter_readings(readings)
    m = metrics.trial_metrics(smooth)
    out = {
        "name": name,
        "test": test,
        "lines": lines,
        "rate_hz": filters.estimate_rate_hz(readings),
        "smooth": [r["force_kg"] for r in smooth],
        "moving_average": [r["force_kg"] for r in filters.filter_readings(readings, "moving_average")],
        "metrics": m,
    }
    if test == "max":
        features = quality.extract_features(smooth)
        out["features"] = features
        out["rule"] = quality.rule_check(features)
    else:
        out["fatigue_index_pct"] = metrics.fatigue_index_pct(smooth)
    return out


def main():
    cases = []
    for i, kind in enumerate(fake_data.TRIAL_KINDS):
        random.seed(100 + i)
        cases.append(case(f"sim_{kind}", fake_data.generate_curve(34.0, kind)))
    random.seed(200)
    cases.append(case("sim_fatigue", fake_data.fatigue_curve(31.0), test="fatigue"))
    cases.append(case("firmware_10hz", firmware_lines(10, 30.0)))
    cases.append(case("firmware_50hz", firmware_lines(50, 30.0)))

    assessments = []
    for force, age, sex in [(31.0, 19, "male"), (31.0, 19, "female"), (24.0, 72, "male"), (15.0, 80, "female"),
                            (52.0, 33, "male"), (8.5, 6, "female"), (60.0, 100, "male"), (18.0, 67, "female"),
                            (44.0, 47, "male"), (5.0, 90, "female")]:
        assessments.append(grip_compare.assess(force, age, sex))

    asym = [{"left": l, "right": r, "result": list(metrics.asymmetry(l, r))}
            for l, r in [(31.0, 34.0), (34.0, 31.0), (0.0, 30.0), (25.0, 25.0)]]

    folder = HERE.parent / "src" / "lib" / "__fixtures__"
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / "reference.json"
    path.write_text(json.dumps({"cases": cases, "assessments": assessments, "asymmetry": asym}, indent=1),
                    encoding="utf-8")
    print(f"Wrote {path.relative_to(HERE.parent)}: {len(cases)} curves, {len(assessments)} assessments")


if __name__ == "__main__":
    main()

"""Each simulated fault type is recognised by the hand-written rules."""
import random

import pytest

import fake_data
import filters
import quality


@pytest.mark.parametrize("kind", fake_data.TRIAL_KINDS)
def test_rules_recognise_each_kind(kind):
    random.seed(1)
    readings = fake_data.lines_to_readings(fake_data.generate_curve(34.0, kind))
    features = quality.extract_features(filters.filter_readings(readings))
    assert quality.rule_check(features) == kind


def test_flat_curve_does_not_crash():
    flat = [{"time_ms": t, "force_kg": 0.0} for t in range(0, 5000, 20)]
    assert quality.extract_features(flat)["peak_kg"] == 0.0

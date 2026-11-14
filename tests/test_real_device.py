"""Problems that only show up with the real device: a flipped sign, no force reaching the cell,
the sensor check before the test, and the device being the default instead of simulated data."""
import argparse
import importlib
import os
import subprocess
import sys
from pathlib import Path

import pytest

import fake_data
import grip_test
import webapp
from test_device_modes import firmware_lines
from test_hardware_input import FirmwareSerial
from test_webapp import USER, client  # noqa: F401  (client is a fixture)

ROOT = Path(__file__).resolve().parent.parent


def curve(force, seconds=5, rate_hz=10):
    """Readings from a function of time in ms, at the HX711's 10 samples/s."""
    return [{"time_ms": t, "force_kg": force(t)} for t in range(0, seconds * 1000, 1000 // rate_hz)]


SQUEEZE = curve(lambda t: 25.0 if 1000 < t < 4000 else 0.0)
NEGATIVE = curve(lambda t: -25.0 if 1000 < t < 4000 else 0.0)
FLAT = curve(lambda t: 0.02 if 1000 < t < 4000 else 0.0)


# ---------- diagnose(): flat and negative recordings ----------

def test_a_real_squeeze_passes():
    assert grip_test.diagnose(SQUEEZE) is None


def test_negative_force_points_to_sign():
    assert "SIGN" in grip_test.diagnose(NEGATIVE)


def test_flat_force_points_to_wiring_and_load_path():
    message = grip_test.diagnose(FLAT)
    assert "hardly changed" in message and "DT to D3" in message


@pytest.mark.parametrize("readings, words", [(NEGATIVE, "SIGN"), (FLAT, "hardly changed")])
def test_flat_or_negative_trials_fail_instead_of_scoring(readings, words):
    """These used to be scored: the flat one even as a 'good' trial of 0.0 kg."""
    state = {"plan": webapp.build_plan("right"), "results": {}}
    event, payload = webapp.analyse(state, 0, readings, [])
    assert event == "failed" and words in payload["message"]
    assert state["results"] == {}


# ---------- sensor check after zeroing ----------

def test_sensor_check_passes_a_squeeze_and_release():
    ok, message = grip_test.sensor_check(SQUEEZE)
    assert ok and "25.0 kg" in message


def test_sensor_check_without_data():
    ok, message = grip_test.sensor_check([])
    assert not ok and "No data" in message


def test_sensor_check_catches_a_handle_that_does_not_return():
    stuck = curve(lambda t: 25.0 if t > 1000 else 0.0)
    ok, message = grip_test.sensor_check(stuck)
    assert not ok and "after letting go" in message


def test_sensor_check_from_the_browser(client):  # noqa: F811
    sid = client.post("/api/start", json={**USER, "source": "browser"}).get_json()["session_id"]
    lines = ["# tared", "t_ms,raw,net,force_kg"] + [f"{r['time_ms']},0,0,{r['force_kg']:.3f}" for r in SQUEEZE]
    body = client.post(f"/api/{sid}/check", json={"lines": lines}).get_json()
    assert body["ok"] is True
    lines = [f"{r['time_ms']},0,0,{r['force_kg']:.3f}" for r in NEGATIVE]
    assert client.post(f"/api/{sid}/check", json={"lines": lines}).get_json()["ok"] is False


def test_sensor_check_from_the_server_device(client, monkeypatch):  # noqa: F811
    now = [0.0]
    def fake_time():
        now[0] += 0.1
        return now[0]
    monkeypatch.setattr(grip_test, "USE_FAKE", False)
    monkeypatch.setattr(grip_test, "connect_serial", lambda: FirmwareSerial(rate_hz=10))
    monkeypatch.setattr(webapp.time, "time", fake_time)
    sid = client.post("/api/start", json=USER).get_json()["session_id"]
    body = client.get(f"/api/{sid}/check/stream").get_data(as_text=True)
    assert "event: point" in body and "event: verdict" in body


def test_sensor_check_needs_a_device(client):  # noqa: F811
    sid = client.post("/api/start", json=USER).get_json()["session_id"]      # simulated: no serial port
    assert client.get(f"/api/{sid}/check/stream").status_code == 400


# ---------- the real device is the default ----------

def test_device_is_the_default_without_the_simulate_setting():
    env = {k: v for k, v in os.environ.items() if k != "GRIPCHECK_SIMULATE"}
    out = subprocess.run([sys.executable, "-c", "import grip_test; print(grip_test.USE_FAKE)"],
                         cwd=ROOT, env=env, capture_output=True, text=True, check=True)
    assert out.stdout.strip() == "False"


@pytest.mark.parametrize("argv, fake", [([], False), (["--device"], False), (["--simulate"], True)])
def test_command_line_options(monkeypatch, argv, fake):
    monkeypatch.setattr(grip_test, "USE_FAKE", not fake)
    args = grip_test.device_args(argparse.ArgumentParser()).parse_args(argv)
    grip_test.apply_args(args)
    assert grip_test.USE_FAKE is fake
    assert grip_test.REST_SECONDS == (3 if fake else 60)


def test_browser_device_trial_at_10_hz_still_scores(client):  # noqa: F811
    """A normal squeeze from the real firmware format at 10 Hz passes the new checks."""
    r = client.post("/api/start", json={**USER, "source": "browser"}).get_json()
    up = client.post(f"/api/{r['session_id']}/step/0/upload", json={"lines": firmware_lines(5)})
    assert up.status_code == 200, up.get_json()


# ---------- simulator ----------

def test_simulator_uses_the_chosen_trial_kind(monkeypatch):
    """make_lines() picked a bad-trial kind and then ignored it."""
    chosen = []
    monkeypatch.setattr(fake_data, "generate_curve", lambda peak, kind, s: chosen.append(kind) or ["0,0.0"])
    monkeypatch.setattr(fake_data.random, "random", lambda: 0.0)              # always a bad trial
    fake_data.make_lines("right", "max", 5)
    assert chosen and chosen[0] != "good"

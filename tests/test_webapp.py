"""The web app runs the same protocol as the terminal app and produces the same report."""
import pytest

import grip_test
import webapp
from test_hardware_input import FirmwareSerial

USER = {"participant_id": "P01", "age": "19", "sex": "male", "dominant": "right",
        "height_cm": "178", "weight_kg": "70", "injury": False}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(grip_test, "SESSIONS_DIR", tmp_path)
    monkeypatch.setattr(webapp, "PLAYBACK_DELAY", 0)        # play fake curves instantly
    webapp.app.testing = True
    return webapp.app.test_client()


def run_whole_test(client):
    r = client.post("/api/start", json=USER)
    assert r.status_code == 200, r.get_json()
    plan = r.get_json()["plan"]
    assert len(plan) == 7 and plan[-1]["test"] == "fatigue"
    for i in range(len(plan)):
        body = client.get(f"/api/step/{i}/stream").get_data(as_text=True)
        assert "event: point" in body and "event: done" in body, body[-300:]
    r = client.post("/api/finish")
    assert r.status_code == 200, r.get_json()
    return client.get(r.get_json()["report_url"]).get_data(as_text=True)


def test_pages_load(client):
    assert b"Grip Strength Test" in client.get("/").data
    assert client.get("/web/app.js").status_code == 200
    assert client.get("/api/config").get_json()["use_fake"] in (True, False)


@pytest.mark.parametrize("bad, message", [
    ({"age": "abc"}, "number"), ({"age": "3"}, "between"),
    ({"sex": ""}, "male or female"), ({"weight_kg": "999"}, "between")])
def test_invalid_details_are_rejected(client, bad, message):
    r = client.post("/api/start", json={**USER, **bad})
    assert r.status_code == 400 and message in r.get_json()["error"]


def test_finish_before_all_trials_is_refused(client):
    client.post("/api/start", json=USER)
    assert client.post("/api/finish").status_code == 400


def test_full_web_test_with_simulated_data(client, tmp_path):
    html = run_whole_test(client)
    assert "Download PDF" in html                 # PDF button on the final report
    assert "Grip / body weight" in html           # new optional field is used
    assert "ID P01" in html
    assert 'http-equiv="refresh"' not in html     # final report does not keep reloading
    rows = next(tmp_path.glob("*_summary.csv")).read_text().splitlines()
    assert rows[0].endswith("quality")


def test_repeating_a_trial_replaces_it(client):
    client.post("/api/start", json=USER)
    client.get("/api/step/0/stream").get_data()
    client.get("/api/step/0/stream").get_data()
    assert list(webapp.state["results"]) == [0]


def test_full_web_test_with_firmware_format(client, monkeypatch):
    now = [0.0]
    def fake_time():
        now[0] += 0.02
        return now[0]
    monkeypatch.setattr(grip_test, "USE_FAKE", False)
    monkeypatch.setattr(grip_test, "connect_serial", lambda: FirmwareSerial())
    monkeypatch.setattr(grip_test, "tare", lambda ser: None)
    monkeypatch.setattr(webapp.time, "time", fake_time)
    r = client.post("/api/start", json=USER)
    assert r.get_json()["needs_tare"] is True
    assert client.post("/api/tare").status_code == 200
    webapp.state.clear()
    assert "Download PDF" in run_whole_test(client)

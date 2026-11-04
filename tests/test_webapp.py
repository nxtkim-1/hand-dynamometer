"""The web app runs the same protocol as the terminal app and produces the same report."""
import pytest

import grip_test
import quality
import webapp
from test_hardware_input import FirmwareSerial

USER = {"participant_id": "P01", "age": "19", "sex": "male", "dominant": "right",
        "height_cm": "178", "weight_kg": "70", "injury": False}


@pytest.fixture
def client(monkeypatch, tmp_path):
    monkeypatch.setattr(grip_test, "SESSIONS_DIR", tmp_path)
    monkeypatch.setattr(webapp, "PLAYBACK_DELAY", 0)        # play fake curves instantly
    monkeypatch.setattr(webapp, "sessions", {})
    webapp.app.testing = True
    return webapp.app.test_client()


def start(client, **changes):
    r = client.post("/api/start", json={**USER, **changes})
    assert r.status_code == 200, r.get_json()
    return r.get_json()["session_id"], r.get_json()["plan"]


def record_all(client, sid, plan):
    for i in range(len(plan)):
        body = client.get(f"/api/{sid}/step/{i}/stream").get_data(as_text=True)
        assert "event: point" in body and "event: done" in body, body[-300:]


def finish(client, sid):
    r = client.post(f"/api/{sid}/finish")
    assert r.status_code == 200, r.get_json()
    url = r.get_json()["report_url"]
    return url, client.get(url).get_data(as_text=True)


def test_pages_load(client):
    assert b"GripCheck" in client.get("/").data
    assert client.get("/web/app.js").status_code == 200
    assert client.get("/api/config").get_json()["use_fake"] in (True, False)


@pytest.mark.parametrize("bad, message", [
    ({"age": "abc"}, "number"), ({"age": "3"}, "between"),
    ({"sex": ""}, "male or female"), ({"weight_kg": "999"}, "between")])
def test_invalid_details_are_rejected(client, bad, message):
    r = client.post("/api/start", json={**USER, **bad})
    assert r.status_code == 400 and message in r.get_json()["error"]


def test_finish_before_all_trials_is_refused(client):
    sid, _ = start(client)
    assert client.post(f"/api/{sid}/finish").status_code == 400


def test_unknown_session_is_refused(client):
    assert client.get("/api/nope/step/0/stream").status_code == 404


def test_full_web_test_with_simulated_data(client, tmp_path):
    sid, plan = start(client)
    assert len(plan) == 7 and plan[-1]["test"] == "fatigue"
    record_all(client, sid, plan)
    url, html = finish(client, sid)
    assert "Download PDF" in html                 # PDF button on the final report
    assert "Grip / body weight" in html           # new optional field is used
    assert "ID P01" in html
    assert "<title>GripCheck report P01" in html  # becomes the PDF file name
    assert 'http-equiv="refresh"' not in html     # final report does not keep reloading
    assert client.get("/report").get_data(as_text=True) == html     # /report = newest report
    assert client.get("/report/../grip_test.py").status_code == 404 # cannot escape the folder
    rows = next(tmp_path.glob("*_summary.csv")).read_text().splitlines()
    assert rows[0].endswith("quality")


def test_repeating_a_trial_replaces_it(client):
    sid, _ = start(client)
    client.get(f"/api/{sid}/step/0/stream").get_data()
    client.get(f"/api/{sid}/step/0/stream").get_data()
    assert list(webapp.sessions[sid]["results"]) == [0]


def test_two_visitors_do_not_mix(client, monkeypatch, tmp_path):
    monkeypatch.setattr(webapp, "DEMO", True)
    sid_a, plan = start(client, participant_id="A", age="25")
    sid_b, _ = start(client, participant_id="B", age="70", sex="female")
    for i in range(len(plan)):                    # interleave the two tests step by step
        client.get(f"/api/{sid_a}/step/{i}/stream").get_data()
        client.get(f"/api/{sid_b}/step/{i}/stream").get_data()
    url_a, html_a = finish(client, sid_a)
    url_b, html_b = finish(client, sid_b)
    assert url_a != url_b
    assert "ID A" in html_a and "age 25" in html_a and "ID B" not in html_a
    assert "ID B" in html_b and "age 70" in html_b
    assert len(list(tmp_path.glob("*_report.html"))) == 2   # nothing was overwritten


def test_demo_hides_the_newest_report(client, monkeypatch):
    monkeypatch.setattr(webapp, "DEMO", True)
    sid, plan = start(client)
    record_all(client, sid, plan)
    url, _ = finish(client, sid)
    assert client.get("/report").status_code == 404        # strangers cannot see it
    assert client.get(url).status_code == 200              # the owner's own link works
    assert len(url.rsplit("_", 1)[-1]) == 8                 # private random part in the link


def test_broken_model_falls_back_to_rules(client, monkeypatch):
    def broken(features):
        raise ValueError("model saved by another scikit-learn version")
    monkeypatch.setattr(quality, "ml_check", broken)
    sid, _ = start(client)
    body = client.get(f"/api/{sid}/step/0/stream").get_data(as_text=True)
    assert "event: done" in body


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
    sid = r.get_json()["session_id"]
    assert r.get_json()["needs_tare"] is True
    assert client.post(f"/api/{sid}/tare").status_code == 200
    record_all(client, sid, r.get_json()["plan"])
    _, html = finish(client, sid)
    assert "Download PDF" in html

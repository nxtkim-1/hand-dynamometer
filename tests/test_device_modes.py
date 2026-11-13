"""Real-device paths that need no code editing: port auto-detect, --device, Web Serial uploads,
and the 'estimated calibration' notice."""
from types import SimpleNamespace

import pytest

import grip_test
import webapp
from test_hardware_input import FirmwareSerial
from test_webapp import USER, client, finish  # noqa: F401  (client is a fixture)


def firmware_lines(seconds, rate_hz=10, counts_per_kg=1.0):
    """What the browser receives from the Nano during one trial (header lines included)."""
    dev = FirmwareSerial(rate_hz=rate_hz, counts_per_kg=counts_per_kg)
    n = 3 + int(seconds * rate_hz)
    return [dev.readline().decode().strip() for _ in range(n)]


# ---------- port auto-detect and --device ----------

def fake_ports(monkeypatch, *ports):
    from serial.tools import list_ports
    monkeypatch.setattr(list_ports, "comports", lambda: [SimpleNamespace(device=d, vid=v) for d, v in ports])


def test_finds_the_one_arduino(monkeypatch):
    fake_ports(monkeypatch, ("COM3", None), ("COM7", 0x1A86))      # Bluetooth port + CH340 clone Nano
    assert grip_test.find_arduino_port() == "COM7"


def test_no_arduino_gives_a_clear_message(monkeypatch):
    fake_ports(monkeypatch, ("COM3", None))
    with pytest.raises(RuntimeError, match="No Arduino found"):
        grip_test.find_arduino_port()


def test_two_arduinos_ask_for_a_port(monkeypatch):
    fake_ports(monkeypatch, ("COM5", 0x2341), ("COM7", 0x1A86))
    with pytest.raises(RuntimeError, match="--port"):
        grip_test.find_arduino_port()


def test_device_flag_switches_to_real_data(monkeypatch):
    monkeypatch.setattr(grip_test, "USE_FAKE", True)
    monkeypatch.setattr(grip_test, "REST_SECONDS", 3)
    monkeypatch.setattr(grip_test, "PORT", "auto")
    grip_test.use_device("COM7")
    assert (grip_test.USE_FAKE, grip_test.REST_SECONDS, grip_test.PORT) == (False, 60, "COM7")


# ---------- Web Serial: the browser records, the server analyses ----------

def start_browser(client, **changes):
    r = client.post("/api/start", json={**USER, "source": "browser", **changes})
    assert r.status_code == 200, r.get_json()
    data = r.get_json()
    assert data["source"] == "browser" and data["needs_tare"] is True
    return data


def test_full_test_from_a_browser_connected_device(client, monkeypatch):
    monkeypatch.setattr(webapp, "DEMO", True)                     # works on the public site too
    data = start_browser(client)
    assert data["rest_seconds"] == 60                             # real squeezes get real rests
    for i, step in enumerate(data["plan"]):
        r = client.post(f"/api/{data['session_id']}/step/{i}/upload",
                        json={"lines": firmware_lines(step["seconds"])})
        assert r.status_code == 200, r.get_json()
        result = r.get_json()
        assert float(result["peak_kg"]) > 20
        assert any("samples/s" in n for n in result["notes"])     # 10 Hz -> RFD n/a, said plainly
    _, html = finish(client, data["session_id"])
    assert "FAKE DATA" not in html
    assert "Estimated calibration" in html


def test_measured_calibration_removes_the_notice(client, monkeypatch):
    monkeypatch.setattr(grip_test, "CALIBRATION", "measured")
    data = start_browser(client)
    assert data["calibration_note"] is None
    for i, step in enumerate(data["plan"]):
        client.post(f"/api/{data['session_id']}/step/{i}/upload", json={"lines": firmware_lines(step["seconds"])})
    _, html = finish(client, data["session_id"])
    assert "Estimated calibration" not in html


def test_simulated_reports_have_no_calibration_notice(client):
    r = client.post("/api/start", json=USER)
    sid, plan = r.get_json()["session_id"], r.get_json()["plan"]
    assert r.get_json()["calibration_note"] is None
    for i in range(len(plan)):
        client.get(f"/api/{sid}/step/{i}/stream").get_data()
    _, html = finish(client, sid)
    assert "FAKE DATA" in html and "Estimated calibration" not in html


def test_uncalibrated_firmware_is_refused(client):
    data = start_browser(client)
    r = client.post(f"/api/{data['session_id']}/step/0/upload",
                    json={"lines": firmware_lines(5, counts_per_kg=43000)})
    assert r.status_code == 400 and "not calibrated" in r.get_json()["error"]


@pytest.mark.parametrize("body", [{}, {"lines": "1,2"}, {"lines": [1, 2]}, {"lines": ["x" * 500]},
                                  {"lines": ["0,1.0"] * (webapp.MAX_UPLOAD_LINES + 1)}])
def test_bad_uploads_are_refused(client, body):
    data = start_browser(client)
    assert client.post(f"/api/{data['session_id']}/step/0/upload", json=body).status_code == 400


def test_empty_or_garbage_recording_fails_clearly(client):
    data = start_browser(client)
    r = client.post(f"/api/{data['session_id']}/step/0/upload", json={"lines": ["# tared", "nan,nan", "hello"]})
    assert r.status_code == 400 and "No data received" in r.get_json()["error"]


def test_paths_cannot_be_mixed(client):
    browser = start_browser(client)
    assert client.get(f"/api/{browser['session_id']}/step/0/stream").status_code == 400
    server = client.post("/api/start", json=USER).get_json()
    r = client.post(f"/api/{server['session_id']}/step/0/upload", json={"lines": firmware_lines(5)})
    assert r.status_code == 400


def test_config_offers_the_browser_device(client):
    cfg = client.get("/api/config").get_json()
    assert cfg["browser_device"] is True and cfg["baud"] == 115200
    assert cfg["calibration"] in ("estimated", "measured")

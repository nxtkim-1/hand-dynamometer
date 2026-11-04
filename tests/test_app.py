"""End-to-end: the whole protocol runs and saves its files, with fake data AND with
a pretend Arduino speaking the real firmware format."""
import builtins
import csv

import pytest

import grip_test
from test_hardware_input import FirmwareSerial


@pytest.fixture
def app(monkeypatch, tmp_path):
    answers = iter(["abc", "19", "male", "right"] + [""] * 20)   # "abc" checks age validation
    monkeypatch.setattr(builtins, "input", lambda prompt="": next(answers))
    monkeypatch.setattr(grip_test, "SESSIONS_DIR", tmp_path)
    monkeypatch.setattr(grip_test, "REST_SECONDS", 0)
    monkeypatch.setattr(grip_test.plt, "pause", lambda *a: None)
    monkeypatch.setattr("webbrowser.open", lambda url: None)
    return tmp_path


def summary_rows(folder):
    path = next(folder.glob("session_*_summary.csv"))
    with open(path) as f:
        return list(csv.reader(f))


def check_outputs(folder):
    for suffix in ["_raw.csv", "_summary.csv", "_centiles.png", "_report.html", "_curves.png"]:
        assert list(folder.glob(f"session_*{suffix}")), suffix
    rows = summary_rows(folder)
    assert rows[0][-1] == "quality"
    assert len([r for r in rows if r[2:3] == ["max"]]) == 6
    assert "refresh" not in next(folder.glob("session_*_report.html")).read_text()  # final report stops refreshing


def test_full_protocol_with_simulated_data(app):
    grip_test.main()
    check_outputs(app)


def test_full_protocol_with_firmware_format(app, monkeypatch):
    now = [0.0]
    def fake_time():
        now[0] += 0.02
        return now[0]
    monkeypatch.setattr(grip_test.time, "time", fake_time)
    monkeypatch.setattr(grip_test, "USE_FAKE", False)
    monkeypatch.setattr(grip_test, "open_serial", lambda: FirmwareSerial())
    grip_test.main()
    check_outputs(app)

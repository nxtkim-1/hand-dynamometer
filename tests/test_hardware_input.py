"""record() must read the REAL firmware format, not only the simulator's."""
import math

import pytest

import fake_data
import grip_test


class FirmwareSerial:
    """Pretends to be firmware/grip_firmware.ino: header lines, then t_ms,raw,net,force_kg."""

    def __init__(self, rate_hz=50, peak_kg=34.0, counts_per_kg=1.0):
        self.dt = 1000 // rate_hz
        self.peak = peak_kg
        self.counts_per_kg = counts_per_kg   # 1.0 = calibrated output, 43000 = NOT calibrated
        self.reset_input_buffer()

    def reset_input_buffer(self):
        self.t = 0
        self.pending = ["# tared", "# hand_dynamometer_v1", "t_ms,raw,net,force_kg"]

    def write(self, data):
        pass

    def close(self):
        pass

    def readline(self):
        if self.pending:
            return (self.pending.pop(0) + "\n").encode()
        self.t += self.dt
        s = self.t / 1000
        kg = 0.0 if s < 0.5 else self.peak * (1 - math.exp(-(s - 0.5) / 0.15))
        net = int(kg * 43000)
        return f"{self.t},{net + 8_000_000},{net},{kg * self.counts_per_kg:.3f}\n".encode()


@pytest.fixture
def fast_clock(monkeypatch):
    """Make record()'s 5-second wall clock finish instantly (1 call = 1/50 s)."""
    now = [0.0]
    def fake_time():
        now[0] += 0.02
        return now[0]
    monkeypatch.setattr(grip_test.time, "time", fake_time)
    monkeypatch.setattr(grip_test.plt, "pause", lambda *a: None)


@pytest.fixture
def ax():
    fig, ax = grip_test.plt.subplots()
    yield ax
    grip_test.plt.close(fig)


def test_firmware_format_is_read(fast_clock, ax):
    readings = grip_test.record(FirmwareSerial(), ax, "right", "t", "max", 5)
    assert len(readings) > 200
    assert readings[0]["time_ms"] == 0                         # time restarts at 0
    assert 33 < max(r["force_kg"] for r in readings) < 34.1    # LAST column is force


def test_simulator_format_still_works(monkeypatch, ax):
    monkeypatch.setattr(grip_test.plt, "pause", lambda *a: None)
    readings = grip_test.record(None, ax, "right", "t", "max", 5)
    assert len(readings) == 250


def test_garbage_only_gives_helpful_error(fast_clock, ax):
    class Garbage(FirmwareSerial):
        def readline(self):
            return b"HX711 not found: check DT, SCK, VCC, GND\n"
    with pytest.raises(RuntimeError, match="HX711 not found"):
        grip_test.record(Garbage(), ax, "right", "t", "max", 5)


def test_uncalibrated_firmware_is_stopped(fast_clock, ax):
    readings = grip_test.record(FirmwareSerial(counts_per_kg=43000), ax, "right", "t", "max", 5)
    with pytest.raises(RuntimeError, match="not calibrated"):
        grip_test.check_recording(readings, warned=False)


def test_slow_rate_is_warned(fast_clock, ax, capsys):
    readings = grip_test.record(FirmwareSerial(rate_hz=10), ax, "right", "t", "max", 5)
    grip_test.check_recording(readings, warned=False)
    assert "samples/s" in capsys.readouterr().out

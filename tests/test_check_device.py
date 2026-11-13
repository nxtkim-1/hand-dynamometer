"""software/check_device.py gives the right verdict for a healthy device and for the common faults."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "software"))
import check_device  # noqa: E402


class Clock:
    def __init__(self):
        self.t = 0.0

    def now(self):
        return self.t

    def sleep(self, s):
        self.t += s


class FakeNano:
    """10 Hz firmware lines; force follows what the test 'does' with the handle."""

    def __init__(self, clock, sign=1, counts_per_kg=42952, offset_kg=0.0, stuck_kg=0.0, cal="estimated",
                 dead=False):
        self.clock, self.sign, self.cpk = clock, sign, counts_per_kg
        self.offset, self.stuck, self.cal, self.dead = offset_kg, stuck_kg, cal, dead
        self.squeezing = False
        self.t_ms = 0
        self.pending = ["# tared", "# hand_dynamometer_v1", f"# calibration={self.cal}", "t_ms,raw,net,force_kg"]

    def readline(self):
        self.clock.t += 0.1
        if self.dead:
            return b""
        if self.pending:
            return (self.pending.pop(0) + "\n").encode()
        self.t_ms += 100
        true_kg = (30.0 if self.squeezing else self.stuck) + self.offset
        net = int(self.sign * true_kg * 42952)
        return f"{self.t_ms},{net + 52400},{net},{net / self.cpk:.3f}\n".encode()

    def write(self, data):
        if data == b"T":
            self.offset = 0.0           # tare removes whatever offset there was

    def reset_input_buffer(self):
        pass


def run(nano, clock):
    def prompt(msg):
        if "SQUEEZE" in msg:
            nano.squeezing = True
        elif "LET GO" in msg:
            nano.squeezing = False
    results = check_device.run_checks(nano, prompt=prompt, out=lambda *a: None, sleep=clock.sleep, now=clock.now)
    return {title: status for status, title, _ in results}


def test_healthy_device_passes():
    clock = Clock()
    r = run(FakeNano(clock, offset_kg=1.2), clock)
    assert r["Firmware output"] == r["Zero"] == r["Squeeze"] == r["Returns to zero"] == "PASS"
    assert r["Sample rate"] == "WARN"                    # 10 Hz: works, RFD n/a
    assert r["Calibration is an estimate"] == "WARN"
    assert "FAIL" not in r.values()


def test_negative_squeeze_says_flip_sign():
    clock = Clock()
    assert run(FakeNano(clock, sign=-1), clock)["Squeeze reads NEGATIVE"] == "FAIL"


def test_uncalibrated_firmware_is_caught():
    clock = Clock()
    assert run(FakeNano(clock, counts_per_kg=1.0), clock)["Squeeze"] == "FAIL"


def test_rubbing_seam_is_flagged():
    clock = Clock()
    r = run(FakeNano(clock, stuck_kg=0.0), clock)
    assert r["Returns to zero"] == "PASS"
    nano = FakeNano(clock)
    def prompt(msg):                                     # handle stays loaded after letting go
        if "SQUEEZE" in msg:
            nano.squeezing = True
        elif "LET GO" in msg:
            nano.squeezing, nano.stuck = False, 3.0
    res = check_device.run_checks(nano, prompt=prompt, out=lambda *a: None, sleep=clock.sleep, now=clock.now)
    assert dict((t, s) for s, t, _ in res)["Returns to zero"] == "WARN"


def test_silent_device_fails_early():
    clock = Clock()
    assert run(FakeNano(clock, dead=True), clock) == {"No data from the device": "FAIL"}


def test_measured_calibration_passes():
    clock = Clock()
    assert run(FakeNano(clock, cal="measured"), clock)["Calibration"] == "PASS"

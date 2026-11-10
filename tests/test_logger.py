"""logger.py in fake mode: run it as a real program, stop it with Ctrl+C, check the CSV."""
import csv
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest

LOGGER = Path(__file__).resolve().parent.parent / "software" / "logger.py"


@pytest.mark.skipif(sys.platform == "win32", reason="cannot send Ctrl+C to a subprocess on Windows")
def test_fake_session_is_saved_on_ctrl_c(tmp_path):
    proc = subprocess.Popen([sys.executable, str(LOGGER), "fake", "--label", "testrun"],
                            cwd=tmp_path, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(4)
    proc.send_signal(signal.SIGINT)
    out, err = proc.communicate(timeout=10)
    assert proc.returncode == 0, err

    files = list(tmp_path.glob("session_*_testrun.csv"))
    assert len(files) == 1
    with open(files[0]) as f:
        rows = list(csv.reader(f))
    assert rows[0] == ["pc_time_s", "t_ms", "raw", "net", "force_kg"]
    data = rows[1:]
    assert len(data) >= 10                                    # ~10 lines/s for 4 s

    t_ms = [int(r[1]) for r in data]
    assert t_ms == sorted(t_ms) and len(set(t_ms)) == len(t_ms)
    for _, _, raw, net, kg in data:
        assert int(raw) - int(net) == 123456
        assert abs(float(kg) - int(net) / 42952) < 0.01

    assert f"Saved {len(data)} samples" in out

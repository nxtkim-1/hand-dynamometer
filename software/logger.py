"""
logger.py — record the dynamometer's serial stream to a CSV file.

Usage:
    python logger.py COM3                          # Windows
    python logger.py /dev/ttyUSB0                  # Linux
    python logger.py /dev/tty.usbserial-XXXX       # Mac
    python logger.py fake                          # no hardware: simulates a squeeze

Options:
    --label NAME   tag the filename, e.g. --label cal_run1 or --label hold_left
    --plot         live plot of 'net' counts (handy for checking wiring; slower)
    --baud N       default 115200

Stop with Ctrl+C. On exit it prints the mean and standard deviation of the
last 2 seconds of 'net' counts — that is the number you record for each
calibration point.

Output columns:  pc_time_s, t_ms, raw, net, force_kg
"""
import sys
import csv
import time
import math
import random
import argparse
from collections import deque
from datetime import datetime

ap = argparse.ArgumentParser()
ap.add_argument("port", help="serial port, or the word 'fake'")
ap.add_argument("--baud", type=int, default=115200)
ap.add_argument("--plot", action="store_true")
ap.add_argument("--label", default="")
args = ap.parse_args()


class FakeArduino:
    """Pretends to be the firmware: 10 lines/s, a squeeze that ramps up,
    holds, decays, and releases. Counts per kg = 8000 so 40 kg ~ 320000."""
    CPK = 42952.0

    def __init__(self):
        self.t0 = time.time()
        self.i = 0

    def readline(self):
        time.sleep(0.1)
        t = time.time() - self.t0
        if t < 2:
            kg = 0.0
        elif t < 3.5:
            kg = 40.0 * (t - 2) / 1.5
        elif t < 34:
            kg = 40.0 * math.exp(-(t - 3.5) / 45.0)
        else:
            kg = max(0.0, 40.0 * math.exp(-30.5 / 45.0) - (t - 34) * 25.0)
        net = int(kg * self.CPK + random.gauss(0, 40))
        raw = net + 123456
        line = f"{int(t*1000)},{raw},{net},{net/self.CPK:.3f}\n"
        return line.encode("ascii")

    def reset_input_buffer(self):
        pass

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass


if args.port.lower() == "fake":
    ser_ctx = FakeArduino()
else:
    import serial
    ser_ctx = serial.Serial(args.port, args.baud, timeout=1)

label = f"_{args.label}" if args.label else ""
fname = datetime.now().strftime(f"session_%Y%m%d_%H%M%S{label}.csv")

if args.plot:
    import matplotlib.pyplot as plt
    plt.ion()
    fig, ax = plt.subplots()
    (line_artist,) = ax.plot([], [])
    ax.set_xlabel("time (s)")
    ax.set_ylabel("net counts")
    ax.grid(True)
    tbuf, ybuf = deque(maxlen=600), deque(maxlen=600)

last2s = deque()
n = 0

with ser_ctx as ser, open(fname, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["pc_time_s", "t_ms", "raw", "net", "force_kg"])

    if args.port.lower() != "fake":
        time.sleep(2.0)            # the Arduino resets when the port opens
    ser.reset_input_buffer()
    t0 = time.time()
    print(f"Logging to {fname}   (Ctrl+C to stop)")

    try:
        while True:
            s = ser.readline().decode("ascii", errors="ignore").strip()
            if not s or s.startswith("#") or s.startswith("t_ms"):
                continue
            parts = s.split(",")
            if len(parts) != 4:
                continue
            try:
                t_ms = int(parts[0])
                raw = int(parts[1])
                net = int(parts[2])
                kg = float(parts[3])
            except ValueError:
                continue

            now = time.time() - t0
            w.writerow([f"{now:.3f}", t_ms, raw, net, kg])
            f.flush()
            n += 1

            last2s.append((now, net))
            while last2s and now - last2s[0][0] > 2.0:
                last2s.popleft()

            if n % 5 == 0:
                print(f"\r{now:7.1f} s   net = {net:9d}   force = {kg:8.2f} kg   ",
                      end="", flush=True)

            if args.plot:
                tbuf.append(now)
                ybuf.append(net)
                if n % 5 == 0:
                    line_artist.set_data(list(tbuf), list(ybuf))
                    ax.relim()
                    ax.autoscale_view()
                    fig.canvas.draw_idle()
                    fig.canvas.flush_events()

    except KeyboardInterrupt:
        pass

vals = [v for _, v in last2s]
print(f"\n\nSaved {n} samples to {fname}")
if vals:
    mean = sum(vals) / len(vals)
    sd = (sum((v - mean) ** 2 for v in vals) / len(vals)) ** 0.5
    print(f"Last 2 s:  mean net = {mean:.1f} counts   std = {sd:.1f} counts   (n = {len(vals)})")

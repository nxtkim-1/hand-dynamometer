"""
analyze_hold.py — analyze a 30-second maximal hold recorded with logger.py.

Usage:
    python analyze_hold.py session_20261102_143012_hold_left.csv
    python analyze_hold.py session.csv --cpk 8291.4      # if firmware was not yet calibrated
    python analyze_hold.py session.csv --hold 30          # hold length in seconds (default 30)

Prints:  peak force, time to peak, force at end of hold, % decline
Writes:  hold_plot.png
"""
import sys
import csv
import argparse

import matplotlib.pyplot as plt

ap = argparse.ArgumentParser()
ap.add_argument("file")
ap.add_argument("--cpk", type=float, default=None,
                help="counts per kg; use if force_kg in the file is uncalibrated")
ap.add_argument("--hold", type=float, default=30.0, help="hold duration in seconds")
args = ap.parse_args()

t, f = [], []
for r in csv.DictReader(open(args.file, newline="")):
    t.append(float(r["pc_time_s"]))
    if args.cpk:
        f.append(float(r["net"]) / args.cpk)
    else:
        f.append(float(r["force_kg"]))

if len(t) < 10:
    sys.exit("Not enough data in file.")

peak = max(f)
i_pk = f.index(peak)
t_pk = t[i_pk]

# onset = first sample at or above 10 % of peak
i_on = next(i for i, v in enumerate(f) if v >= 0.10 * peak)
t_on = t[i_on]
t_end = t_on + args.hold

# end-of-hold force = mean of the last 2 s of the hold window
win = [v for tt, v in zip(t, f) if (t_end - 2.0) <= tt <= t_end]
f_end = sum(win) / len(win) if win else f[-1]
decline_pct = 100.0 * (peak - f_end) / peak

print("=== 30-SECOND HOLD ===")
print(f"peak force        = {peak:.2f} kg   at t = {t_pk:.2f} s")
print(f"time to peak      = {t_pk - t_on:.2f} s   (from onset at 10 % of peak)")
print(f"force at {args.hold:.0f} s      = {f_end:.2f} kg   (mean of last 2 s of hold)")
print(f"decline over hold = {decline_pct:.1f} %")

plt.figure(figsize=(8, 4))
plt.plot(t, f, lw=1)
plt.axvline(t_on, ls="--", color="gray", label="onset")
plt.axvline(t_end, ls="--", color="gray", label=f"{args.hold:.0f} s")
plt.plot(t_pk, peak, "ro", label=f"peak {peak:.1f} kg")
plt.axhline(f_end, ls=":", color="r",
            label=f"end {f_end:.1f} kg  (−{decline_pct:.0f} %)")
plt.xlabel("time (s)")
plt.ylabel("force (kg)")
plt.title("Maximal grip hold — force decay")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("hold_plot.png", dpi=150)
print("wrote hold_plot.png")

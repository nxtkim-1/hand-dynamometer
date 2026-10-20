"""
calibrate.py — fit the calibration line and produce the numbers for the report.

Usage:
    python calibrate.py                        # reads calibration_points.csv
    python calibrate.py my_points.csv

Input CSV columns:
    mass_kg      actual (verified) mass hung from the handle; 0 for unloaded
    net_counts   mean 'net' from logger.py over the last 2 s at that mass
    direction    'up' while adding mass, 'down' while removing
    run          1, 2, 3 ... one number per complete up/down sequence

Example:
    mass_kg,net_counts,direction,run
    0,12,up,1
    4.98,41230,up,1
    10.02,82910,up,1
    10.02,82880,down,1
    4.98,41205,down,1
    0,-8,down,1
    0,15,up,2
    ...

Prints:
    COUNTS_PER_KG  -> paste into grip_firmware.ino and re-upload
    R^2, max nonlinearity (% FS), hysteresis (% FS), repeatability (% FS)
Writes:
    calibration_fit.png, calibration_residuals.png
"""
import sys
import csv

import numpy as np
import matplotlib.pyplot as plt

FULL_SCALE_KG = 100.0   # rated capacity of the load cell — edit if yours differs

fname = sys.argv[1] if len(sys.argv) > 1 else "calibration_points.csv"
rows = list(csv.DictReader(open(fname, newline="")))
if len(rows) < 4:
    sys.exit("Need at least 4 calibration points.")

m = np.array([float(r["mass_kg"]) for r in rows])
c = np.array([float(r["net_counts"]) for r in rows])
d = np.array([r["direction"].strip().lower() for r in rows])
run = np.array([int(r["run"]) for r in rows])

# ---- Linear fit:  counts = slope * mass + intercept
slope, intercept = np.polyfit(m, c, 1)
pred = slope * m + intercept
resid_counts = c - pred
resid_kg = resid_counts / slope

ss_res = np.sum(resid_counts ** 2)
ss_tot = np.sum((c - c.mean()) ** 2)
r2 = 1.0 - ss_res / ss_tot

fs_counts = abs(slope * FULL_SCALE_KG)
nonlin_pct = 100.0 * np.max(np.abs(resid_counts)) / fs_counts

# ---- Hysteresis: at each mass, |mean(up) - mean(down)|
hyst = []
for mass in np.unique(m):
    up = c[(m == mass) & (d == "up")]
    dn = c[(m == mass) & (d == "down")]
    if len(up) and len(dn):
        hyst.append(abs(up.mean() - dn.mean()))
hyst_pct = 100.0 * max(hyst) / fs_counts if hyst else float("nan")

# ---- Repeatability: std across runs at each (mass, direction)
reps = []
for mass in np.unique(m):
    for dd in ("up", "down"):
        v = c[(m == mass) & (d == dd)]
        if len(v) >= 2:
            reps.append(v.std(ddof=1))
rep_pct = 100.0 * max(reps) / fs_counts if reps else float("nan")

# ---- Report
print("=== CALIBRATION RESULT ===")
print(f"points: {len(m)}   runs: {len(np.unique(run))}   "
      f"calibrated range: {m.min():.2f} – {m.max():.2f} kg")
print(f"COUNTS_PER_KG      = {slope:.4f}      <-- paste into firmware")
print(f"intercept          = {intercept:.1f} counts   (should be near 0 after tare)")
print(f"R^2                = {r2:.6f}")
print(f"max nonlinearity   = {nonlin_pct:.3f} % FS   "
      f"(max residual {np.max(np.abs(resid_kg)):.3f} kg)")
print(f"hysteresis         = {hyst_pct:.3f} % FS")
print(f"repeatability      = {rep_pct:.3f} % FS   (max std across runs)")
print(f"(FS = {FULL_SCALE_KG:.0f} kg rated. In the report, state the calibrated range "
      f"as the validated range.)")

# ---- Plots
plt.figure()
plt.plot(m, c, "o", label="measured")
xx = np.linspace(0, m.max(), 50)
plt.plot(xx, slope * xx + intercept, "-", label=f"fit: {slope:.1f} counts/kg")
plt.xlabel("applied mass (kg)")
plt.ylabel("net counts")
plt.title("Calibration curve")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("calibration_fit.png", dpi=150)

plt.figure()
for dd, mk in (("up", "^"), ("down", "v")):
    sel = d == dd
    if sel.any():
        plt.plot(m[sel], resid_kg[sel], mk, label=dd)
plt.axhline(0, color="k", lw=0.8)
plt.xlabel("applied mass (kg)")
plt.ylabel("residual (kg)")
plt.title("Residuals from linear fit")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("calibration_residuals.png", dpi=150)

print("wrote calibration_fit.png and calibration_residuals.png")

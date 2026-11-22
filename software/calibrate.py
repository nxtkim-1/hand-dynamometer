"""
calibrate.py — fit the calibration line and produce the numbers for the report.

Usage:
    python calibrate.py                        # reads calibration_points.csv
    python calibrate.py my_points.csv
    python calibrate.py synthetic.csv --source simulated   # label test data honestly

Input CSV columns:
    mass_kg      actual (verified) mass hung from the handle; 0 for unloaded
                 (or mass_lb instead: pounds are converted, 1 lb = 0.45359237 kg;
                  see data/calibration_points_template_lb.csv)
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
import argparse
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from pipeline import FULL_SCALE_KG, fit_calibration, read_points_csv  # noqa: E402

ap = argparse.ArgumentParser(description="Fit the calibration line from known masses")
ap.add_argument("file", nargs="?", default="calibration_points.csv")
ap.add_argument("--source", choices=["measured", "simulated"], default="measured",
                help="'measured' = real weighed masses on the device; 'simulated' = synthetic test data")
args = ap.parse_args()

with open(args.file, newline="", encoding="utf-8") as f:
    rows = read_points_csv(f.read())
if len(rows) < 4:
    sys.exit("Need at least 4 filled-in calibration points (mass and net_counts).")

fit = fit_calibration(rows, source=args.source, full_scale_kg=FULL_SCALE_KG)
print("=== CALIBRATION RESULT ===")
print(fit.report())

m = [r["mass_kg"] for r in rows]
c = [r["net_counts"] for r in rows]
plt.figure()
plt.plot(m, c, "o", label="measured" if args.source == "measured" else "SIMULATED")
xx = [0, max(m)]
plt.plot(xx, [fit.counts_per_kg * x + fit.intercept_counts for x in xx], "-",
         label=f"fit: {fit.counts_per_kg:.1f} counts/kg")
plt.xlabel("applied mass (kg)")
plt.ylabel("net counts")
plt.title("Calibration curve" + ("" if args.source == "measured" else " (SIMULATED DATA)"))
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("calibration_fit.png", dpi=150)

plt.figure()
for d, mk in (("up", "^"), ("down", "v")):
    sel = [(r["mass_kg"], fit.counts_to_kg(r["net_counts"]) - r["mass_kg"]) for r in rows if r["direction"] == d]
    if sel:
        plt.plot([a for a, _ in sel], [b for _, b in sel], mk, label=d)
plt.axhline(0, color="k", lw=0.8)
plt.xlabel("applied mass (kg)")
plt.ylabel("residual (kg)")
plt.title("Residuals from linear fit")
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("calibration_residuals.png", dpi=150)
print("wrote calibration_fit.png and calibration_residuals.png")

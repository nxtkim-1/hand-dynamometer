# data/

Everything the scripts read and write.

- `calibration_points.csv` — you build this by hand during the calibration session.
  Columns: `mass_kg,net_counts,direction,run`. See `docs/04_calibration.md`.
- `example_calibration_points.csv` — synthetic example so you can run `calibrate.py` today.
- `session_YYYYMMDD_HHMMSS_<label>.csv` — written by `logger.py`. Keep every session you cite in the report.

Run from this folder:
```
python ../software/calibrate.py calibration_points.csv
python ../software/analyze_hold.py session_..._hold_left.csv
```
Plots land here; copy the ones you use into `images/`.

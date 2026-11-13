"""
check_device.py - one-minute health check of the dynamometer before running GripCheck.

    python software/check_device.py            (port found automatically)
    python software/check_device.py --port COM7

It walks you through: plug in -> hands off -> squeeze -> let go, and prints PASS / WARN / FAIL
for each thing GripCheck depends on, with the fix for anything that fails:
  1. the Arduino is found and the port opens
  2. the firmware prints t_ms,raw,net,force_kg lines (and which calibration it reports)
  3. the sample rate (10 Hz works; 80 Hz is needed for RFD)
  4. zeroing with "T" brings the reading to about 0 kg
  5. a squeeze reads POSITIVE and plausible (not negative, not "not calibrated")
  6. letting go returns to about 0 kg (nothing rubbing across the seam)

Close the Arduino IDE's Serial Monitor first: only one program can use the port.
"""
import argparse
import statistics
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))   # import grip_test from the repo root
import grip_test  # noqa: E402

ZERO_TOL_KG = 0.3          # after zeroing, the hands-off reading must sit within this of 0
RETURN_TOL_KG = 0.5        # after letting go
MIN_SQUEEZE_KG = 2.0       # a firm squeeze must reach at least this


def read_for(ser, seconds, now=time.time):
    """Collect (data rows, comment lines) for a number of seconds. Rows: (t_ms, net, force_kg)."""
    rows, comments, start = [], [], now()
    while now() - start < seconds:
        line = ser.readline().decode(errors="ignore").strip()
        if not line:
            continue
        if line.startswith("#"):
            comments.append(line)
            continue
        parts = line.split(",")
        try:
            rows.append((int(parts[0]), int(float(parts[2])) if len(parts) >= 4 else None, float(parts[-1])))
        except (ValueError, IndexError):
            comments.append(line)          # header "t_ms,raw,net,force_kg" or noise
    return rows, comments


def rate_hz(rows):
    if len(rows) < 2 or rows[-1][0] == rows[0][0]:
        return 0.0
    return (len(rows) - 1) / ((rows[-1][0] - rows[0][0]) / 1000)


def run_checks(ser, prompt=print, out=print, sleep=time.sleep, now=time.time, boot_wait=True):
    """Run every check on an open serial connection. Returns a list of (status, title, detail)."""
    results = []

    def add(status, title, detail=""):
        results.append((status, title, detail))
        out(f"  [{status}] {title}" + (f" - {detail}" if detail else ""))

    # --- firmware output
    if boot_wait:
        sleep(2.5)                                    # opening the port restarts the Nano
    rows, comments = read_for(ser, 5, now)             # long enough to catch the boot header (tare takes ~2 s)
    if not rows:
        add("FAIL", "No data from the device",
            "upload firmware/grip_firmware_tillaart/grip_firmware_tillaart.ino and check the HX711 wiring "
            f"(first lines seen: {comments[:3]})")
        return results
    four_cols = all(r[1] is not None for r in rows)
    add("PASS" if four_cols else "WARN", "Firmware output",
        f"{len(rows)} lines, format t_ms,raw,net,force_kg" if four_cols else "lines do not have 4 columns")
    cal = next((c for c in comments if c.startswith("# calibration=")), None)
    if cal is None:
        add("WARN", "Calibration line missing", "older firmware; upload grip_firmware_tillaart.ino again")
    elif "measured" in cal:
        add("PASS", "Calibration", cal[2:])
    else:
        add("WARN", "Calibration is an estimate", cal[2:] + " (fine for now; G3 replaces it)")

    hz = rate_hz(rows)
    if hz < 5:
        add("FAIL", "Sample rate", f"{hz:.1f} samples/s is too slow; check the HX711 wiring")
    elif hz < grip_test.MIN_RATE_HZ:
        add("WARN", "Sample rate", f"about {hz:.0f} samples/s: GripCheck works, RFD shows n/a until the RATE pin is high")
    else:
        add("PASS", "Sample rate", f"about {hz:.0f} samples/s")

    # --- zero
    prompt("\nHands OFF the handle. Zeroing in 2 s...")
    sleep(2)
    ser.write(b"T")
    sleep(2.5)
    ser.reset_input_buffer()
    rest, _ = read_for(ser, 2, now)
    kg = [r[2] for r in rest]
    if not kg:
        add("FAIL", "Zero", "no data after zeroing")
        return results
    mean, noise = statistics.mean(kg), (statistics.pstdev(kg) if len(kg) > 1 else 0.0)
    ok = abs(mean) < ZERO_TOL_KG
    add("PASS" if ok else "WARN", "Zero", f"{mean:+.2f} kg at rest, noise {noise:.2f} kg"
        + ("" if ok else " (something may be touching the handle, or the reading is drifting)"))

    # --- squeeze
    prompt("\nSQUEEZE the handle firmly now and hold it...")
    squeeze, _ = read_for(ser, 4, now)
    kg = [r[2] for r in squeeze]
    peak, low = (max(kg), min(kg)) if kg else (0.0, 0.0)
    if peak > grip_test.MAX_PLAUSIBLE_KG:
        add("FAIL", "Squeeze", f"peak {peak:.0f} 'kg' is impossible: COUNTS_PER_KG is still 1.0 in the firmware")
    elif peak >= MIN_SQUEEZE_KG:
        add("PASS", "Squeeze", f"peak {peak:.1f} kg (estimated scale), reads positive")
    elif low <= -MIN_SQUEEZE_KG:
        add("FAIL", "Squeeze reads NEGATIVE", f"lowest {low:.1f} kg: change SIGN in the firmware (-1 <-> 1) and upload")
    else:
        add("FAIL", "Squeeze barely moves", f"peak {peak:.2f} kg: check the seam with paper, the bolts and the HX711 joints")

    # --- release
    prompt("\nLET GO completely...")
    sleep(1.5)
    ser.reset_input_buffer()
    after, _ = read_for(ser, 2, now)
    kg = [r[2] for r in after]
    back = statistics.mean(kg) if kg else float("nan")
    ok = kg and abs(back) < RETURN_TOL_KG
    add("PASS" if ok else "WARN", "Returns to zero", f"{back:+.2f} kg after release"
        + ("" if ok else " (check that nothing rubs across the 3 mm seam, and that plugs are seated)"))
    return results


def main():
    parser = argparse.ArgumentParser(description="Check the dynamometer before running GripCheck")
    parser.add_argument("--port", help="serial port, e.g. COM7 (default: find it automatically)")
    args = parser.parse_args()
    if args.port:
        grip_test.PORT = args.port
    print("Dynamometer check. Close the Arduino Serial Monitor first.\n")
    try:
        ser = grip_test.connect_serial()            # finds the port, waits for the Nano to restart
    except RuntimeError as e:
        print(f"  [FAIL] Connect - {e}")
        sys.exit(1)
    print(f"  [PASS] Connected on {ser.port}")
    try:
        results = run_checks(ser, boot_wait=False)   # connect_serial() already waited for the restart
    finally:
        ser.close()
    fails = [r for r in results if r[0] == "FAIL"]
    print("\nRESULT:", "FAIL - fix the items above, then run this again." if fails
          else "READY - start GripCheck (start_gripcheck.bat, or python webapp.py --device).")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()

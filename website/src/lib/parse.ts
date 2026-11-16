// Turning serial text into readings. Same rule as grip_test.parse_line():
//   simulator: "t_ms,force_kg"
//   firmware:  "t_ms,raw,net,force_kg"   -> first column = time, last column = force
// Lines starting with "#" (firmware comments) or anything else that is not data are skipped.

import type { Reading } from "./types";

export function parseLine(line: string): { t: number; f: number } | null {
  const parts = line.split(",");
  if (parts.length < 2) return null;
  const first = parts[0].trim();
  if (!/^[+-]?\d+$/.test(first)) return null; // Python int() accepts only whole numbers
  const t = parseInt(first, 10);
  const last = parts[parts.length - 1].trim();
  if (last === "") return null;
  const f = Number(last);
  if (!Number.isFinite(t) || !Number.isFinite(f)) return null;
  return { t, f };
}

/** Parse lines into readings whose time restarts at 0. Also returns the lines that were not data. */
export function linesToReadings(lines: string[]): { readings: Reading[]; skipped: string[] } {
  const readings: Reading[] = [];
  const skipped: string[] = [];
  let firstMs: number | null = null;
  for (const line of lines) {
    const parsed = parseLine(line);
    if (parsed === null) {
      if (line) skipped.push(line);
      continue;
    }
    if (firstMs === null) firstMs = parsed.t;
    readings.push({ time_ms: parsed.t - firstMs, force_kg: parsed.f });
  }
  return { readings, skipped };
}

/** Pull "# calibration=measured" style comments out of the firmware's start-up lines. */
export function parseCalibrationComment(line: string): "measured" | "estimated" | null {
  const m = /^#.*calibration\s*=\s*(measured|estimated)/i.exec(line.trim());
  return m ? (m[1].toLowerCase() as "measured" | "estimated") : null;
}

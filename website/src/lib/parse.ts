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

/** The firmware's four columns, or null for anything else (simulator lines have no raw/net). */
export function parseFirmwareLine(line: string): { t: number; raw: number; net: number; kg: number } | null {
  if (parseLine(line) === null) return null;
  const parts = line.split(",").map((s) => s.trim());
  if (parts.length !== 4) return null;
  const [t, raw, net, kg] = parts.map(Number);
  return [t, raw, net, kg].every(Number.isFinite) ? { t, raw, net, kg } : null;
}

/** What the firmware says about itself in its "#" lines (v1.1 and later print all of these). */
export interface DeviceInfo {
  firmware: string | null;
  countsPerKg: number | null;
  sign: 1 | -1 | null;
  calibration: "measured" | "estimated" | null;
  /** "YYYY-MM-DD" of a saved calibration, if the firmware stored one. */
  calibratedOn: string | null;
}

export const emptyDeviceInfo = (): DeviceInfo => ({ firmware: null, countsPerKg: null, sign: null, calibration: null, calibratedOn: null });

/** Read one "#" line into the matching DeviceInfo fields. Returns only what the line tells. */
export function parseDeviceInfo(line: string): Partial<DeviceInfo> {
  const s = line.trim();
  if (!s.startsWith("#")) return {};
  let m: RegExpExecArray | null;
  if ((m = /^#\s*hand_dynamometer_v([\w.]+)/i.exec(s))) return { firmware: m[1] };
  if ((m = /^#\s*counts_per_kg\s*=\s*([\d.]+)/i.exec(s))) return { countsPerKg: Number(m[1]) };
  if ((m = /^#\s*sign\s*=\s*([+-]?1)\b/i.exec(s))) return { sign: Number(m[1]) === -1 ? -1 : 1 };
  const cal = parseCalibrationComment(s);
  if (cal) {
    const date = /calibration\s*=\s*measured\s+(\d{4}-\d{2}-\d{2})/i.exec(s);
    return { calibration: cal, calibratedOn: cal === "measured" && date ? date[1] : null };
  }
  return {};
}

/** Flip the sign of a data line, the same as changing SIGN in the firmware.
 *  Firmware "t_ms,raw,net,force_kg": net and force_kg flip, time and raw stay as they are.
 *  Simulator "t_ms,force_kg": force flips. Comments and anything else come back unchanged. */
export function reverseLine(line: string): string {
  if (parseLine(line) === null) return line;
  const parts = line.split(",");
  const flip = (s: string) => {
    const t = s.trim();
    const decimals = t.includes(".") ? t.split(".")[1].length : 0;
    const v = -Number(t);
    return (v === 0 ? 0 : v).toFixed(decimals); // never print "-0"
  };
  const last = parts.length - 1;
  parts[last] = flip(parts[last]);
  if (parts.length >= 4) parts[last - 1] = flip(parts[last - 1]);
  return parts.join(",");
}

/** A squeeze can only push the bars together, so a reading this far below zero is not noise
 *  (the bench noise is about ±70 counts, a few grams): either the direction is reversed, or the
 *  device was zeroed while something was pressing on it. */
export const NEGATIVE_WARN_KG = -2;

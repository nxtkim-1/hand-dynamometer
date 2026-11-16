// Is a maximal trial valid? Port of quality.py's rule check.
// The Python app can also use a Random Forest (models/quality_model.joblib); that model was trained
// on simulated curves only and cannot run in a browser, so the website uses the hand-written rules.

import { findPeak } from "./metrics";
import type { QualityLabel, Reading } from "./types";

export interface QualityFeatures {
  baseline_frac: number; // force already there in the first 300 ms, as a fraction of peak
  rise_time_ms: number; // 10 % -> 90 % of peak
  dip_frac: number; // biggest drop during the hold, as a fraction of peak
  hold_cv: number; // wobble during the hold
  peak_kg: number;
}

function firstTimeAbove(readings: Reading[], level: number): number {
  for (const r of readings) if (r.force_kg >= level) return r.time_ms;
  return readings[readings.length - 1].time_ms;
}

const mean = (xs: number[]) => xs.reduce((a, b) => a + b, 0) / xs.length;
const pstdev = (xs: number[]) => {
  const m = mean(xs);
  return Math.sqrt(xs.reduce((s, x) => s + (x - m) ** 2, 0) / xs.length);
};

export function extractFeatures(readings: Reading[]): QualityFeatures {
  const peak = findPeak(readings).force_kg;
  if (peak <= 0) return { baseline_frac: 0, rise_time_ms: 0, dip_frac: 0, hold_cv: 0, peak_kg: 0 };

  const start = readings[0].time_ms;
  const baseline = readings.filter((r) => r.time_ms - start <= 300).map((r) => r.force_kg);
  const riseTime = firstTimeAbove(readings, 0.9 * peak) - firstTimeAbove(readings, 0.1 * peak);

  let firstAbove = -1;
  let lastAbove = -1;
  readings.forEach((r, i) => {
    if (r.force_kg >= 0.8 * peak) {
      if (firstAbove < 0) firstAbove = i;
      lastAbove = i;
    }
  });
  const hold = readings.slice(firstAbove, lastAbove + 1).map((r) => r.force_kg);

  return {
    baseline_frac: mean(baseline) / peak,
    rise_time_ms: riseTime,
    dip_frac: (peak - Math.min(...hold)) / peak,
    hold_cv: pstdev(hold) / mean(hold),
    peak_kg: peak,
  };
}

export function ruleCheck(f: QualityFeatures): QualityLabel {
  if (f.baseline_frac > 0.1) return "false_start";
  if (f.dip_frac > 0.25) return "slip";
  if (f.rise_time_ms > 600) return "submaximal";
  return "good";
}

export function checkTrial(readings: Reading[]): QualityLabel {
  return ruleCheck(extractFeatures(readings));
}

export const QUALITY_TEXT: Record<QualityLabel, { title: string; why: string }> = {
  good: { title: "Good trial", why: "Clean rise, steady hold." },
  false_start: { title: "Possible false start", why: "Force was already there before the countdown ended." },
  slip: { title: "Possible slip", why: "Force dropped suddenly, as if the hand slipped." },
  submaximal: { title: "Possibly not a full effort", why: "Force rose slowly, which suggests less than full effort." },
};

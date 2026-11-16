// Force-time metrics. Port of metrics.py; definitions are on the How it works page.

import type { Reading, TrialMetrics } from "./types";

export const G = 9.81; // 1 kg of force = 9.81 N
export const MIN_RFD_POINTS = 5; // fewer points in the RFD window -> the slope is unreliable

export function findPeak(readings: Reading[]): Reading {
  let best = readings[0];
  for (const r of readings) if (r.force_kg > best.force_kg) best = r;
  return best;
}

/** First reading above 5 % of the peak: the squeeze has started. */
export function findOnset(readings: Reading[], fraction = 0.05): Reading {
  const threshold = findPeak(readings).force_kg * fraction;
  return readings.find((r) => r.force_kg >= threshold) ?? readings[0];
}

export function timeToPeakMs(readings: Reading[]): number {
  return findPeak(readings).time_ms - findOnset(readings).time_ms;
}

/** Least-squares straight line y = slope * x + intercept. */
export function fitLine(xs: number[], ys: number[]): { slope: number; intercept: number } {
  const n = xs.length;
  const meanX = xs.reduce((a, b) => a + b, 0) / n;
  const meanY = ys.reduce((a, b) => a + b, 0) / n;
  let top = 0;
  let bottom = 0;
  for (let i = 0; i < n; i++) {
    top += (xs[i] - meanX) * (ys[i] - meanY);
    bottom += (xs[i] - meanX) ** 2;
  }
  const slope = top / bottom;
  return { slope, intercept: meanY - slope * meanX };
}

/** Rate of force development: slope of force (N) over the first 200 ms after onset, in N/s. */
export function rfdNPerS(readings: Reading[], windowMs = 200): number | null {
  const onset = findOnset(readings).time_ms;
  const xs: number[] = [];
  const ys: number[] = [];
  for (const r of readings) {
    if (onset <= r.time_ms && r.time_ms <= onset + windowMs) {
      xs.push(r.time_ms / 1000);
      ys.push(r.force_kg * G);
    }
  }
  if (xs.length < MIN_RFD_POINTS) return null;
  return fitLine(xs, ys).slope;
}

/** Percent drop from the peak to the mean of the last second of a 30 s squeeze. */
export function fatigueIndexPct(readings: Reading[], squeezeMs = 30000, finalWindowMs = 1000): number | null {
  const peakKg = findPeak(readings).force_kg;
  const endMs = findOnset(readings).time_ms + squeezeMs;
  const final = readings.filter((r) => endMs - finalWindowMs <= r.time_ms && r.time_ms <= endMs).map((r) => r.force_kg);
  if (final.length === 0 || peakKg === 0) return null;
  const finalKg = final.reduce((a, b) => a + b, 0) / final.length;
  return ((peakKg - finalKg) / peakKg) * 100;
}

/** Left/right ratio and how much weaker the weaker hand is (%). */
export function asymmetry(leftKg: number, rightKg: number): { ratio: number | null; weakerPct: number | null } {
  if (leftKg <= 0 || rightKg <= 0) return { ratio: null, weakerPct: null };
  return { ratio: leftKg / rightKg, weakerPct: (Math.abs(leftKg - rightKg) / Math.max(leftKg, rightKg)) * 100 };
}

export function trialMetrics(readings: Reading[]): TrialMetrics {
  return {
    peak_kg: findPeak(readings).force_kg,
    time_to_peak_ms: timeToPeakMs(readings),
    rfd_n_per_s: rfdNPerS(readings),
  };
}

/** Coefficient of variation (%) of several peaks: how repeatable the trials were. */
export function cvPct(values: number[]): number | null {
  if (values.length < 2) return null;
  const mean = values.reduce((a, b) => a + b, 0) / values.length;
  if (mean === 0) return null;
  const sd = Math.sqrt(values.reduce((s, v) => s + (v - mean) ** 2, 0) / (values.length - 1));
  return (sd / mean) * 100;
}

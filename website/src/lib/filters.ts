// Noise removal. A line-by-line port of filters.py (its pure-Python path, which matches scipy's
// butter() + filtfilt()). Tested against outputs of the Python code in filters.test.ts.
//
// Why a zero-phase Butterworth: a normal low-pass filter delays the signal, which would make
// time-to-peak and RFD look slower than they were. Running it forwards and then backwards
// ("filtfilt") cancels that delay.

import type { Reading } from "./types";

export const SAMPLE_RATE_HZ = 50; // fallback when the rate cannot be measured
export const CUTOFF_HZ = 10;
export const MIN_POINTS = 16; // filtfilt needs more points than its padding

/** Samples per second = gaps / total time. One gap is not enough: millis() is whole numbers. */
export function estimateRateHz(readings: Reading[]): number {
  if (readings.length < 2) return SAMPLE_RATE_HZ;
  const spanMs = readings[readings.length - 1].time_ms - readings[0].time_ms;
  if (spanMs <= 0) return SAMPLE_RATE_HZ;
  return ((readings.length - 1) * 1000) / spanMs;
}

export function movingAverage(values: number[], window = 5): number[] {
  const half = Math.floor(window / 2);
  return values.map((_, i) => {
    const chunk = values.slice(Math.max(0, i - half), i + half + 1);
    return chunk.reduce((a, b) => a + b, 0) / chunk.length;
  });
}

// ---- complex numbers, only what the filter design needs ----
type C = { re: number; im: number };
const c = (re: number, im = 0): C => ({ re, im });
const add = (a: C, b: C): C => c(a.re + b.re, a.im + b.im);
const sub = (a: C, b: C): C => c(a.re - b.re, a.im - b.im);
const mul = (a: C, b: C): C => c(a.re * b.re - a.im * b.im, a.re * b.im + a.im * b.re);
const div = (a: C, b: C): C => {
  const d = b.re * b.re + b.im * b.im;
  return c((a.re * b.re + a.im * b.im) / d, (a.im * b.re - a.re * b.im) / d);
};

/** Polynomial coefficients from its roots (real parts only, as in filters._poly). */
function poly(roots: C[]): number[] {
  let coeffs: C[] = [c(1)];
  for (const r of roots) {
    const next: C[] = Array.from({ length: coeffs.length + 1 }, () => c(0));
    coeffs.forEach((v, i) => {
      next[i] = add(next[i], v);
      next[i + 1] = sub(next[i + 1], mul(v, r));
    });
    coeffs = next;
  }
  return coeffs.map((v) => v.re);
}

/** Digital Butterworth low-pass design (bilinear transform), same maths as filters._butter_coeffs. */
export function butterCoeffs(order: number, cutoffHz: number, fs: number): { b: number[]; a: number[] } {
  const wn = (2 * cutoffHz) / fs;
  const warped = 4 * Math.tan((Math.PI * wn) / 2);
  const poles: C[] = [];
  for (let m = -order + 1; m < order; m += 2) {
    const angle = (Math.PI * m) / (2 * order);
    poles.push(mul(c(-warped), c(Math.cos(angle), Math.sin(angle))));
  }
  const zPoles = poles.map((p) => div(add(c(4), p), sub(c(4), p)));
  const zZeros = Array.from({ length: order }, () => c(-1));
  let gain = c(warped ** order);
  for (const p of poles) gain = div(gain, sub(c(4), p));
  const b = poly(zZeros).map((v) => gain.re * v);
  return { b, a: poly(zPoles) };
}

/** Initial filter state for a step input, so the output does not start with a jump. */
function lfilterZi(bIn: number[], aIn: number[]): number[] {
  const n = aIn.length - 1;
  const b = bIn.map((v) => v / aIn[0]);
  const a = aIn.map((v) => v / aIn[0]);
  const sumA = a.slice(1).reduce((s, v) => s + v, 0);
  const sumB = b.slice(1).reduce((s, v) => s + v, 0);
  const zi = new Array<number>(n).fill(0);
  zi[0] = (sumB - b[0] * sumA) / (1 + sumA);
  for (let i = 1; i < n; i++) {
    let s = 0;
    for (let j = i + 1; j <= n; j++) s += b[j] - a[j] * b[0] - a[j] * zi[0];
    zi[i] = s;
  }
  return zi;
}

/** One pass of the filter (direct form II transposed). */
function lfilter(b: number[], a: number[], values: number[], zi: number[]): number[] {
  const n = a.length - 1;
  const z = zi.slice();
  const out: number[] = [];
  for (const x of values) {
    const y = b[0] * x + z[0];
    for (let j = 0; j < n - 1; j++) z[j] = b[j + 1] * x + z[j + 1] - a[j + 1] * y;
    z[n - 1] = b[n] * x - a[n] * y;
    out.push(y);
  }
  return out;
}

/** Forward-backward filtering with odd-reflection padding at both ends (scipy's default). */
export function filtfilt(b: number[], a: number[], values: number[]): number[] {
  const padlen = 3 * Math.max(a.length, b.length);
  const first = values[0];
  const last = values[values.length - 1];
  const ext: number[] = [];
  for (let i = padlen; i > 0; i--) ext.push(2 * first - values[i]);
  ext.push(...values);
  for (let i = 1; i <= padlen; i++) ext.push(2 * last - values[values.length - 1 - i]);
  const zi = lfilterZi(b, a);
  const y = lfilter(b, a, ext, zi.map((z) => z * ext[0]));
  const yRev = y.reverse();
  const y2 = lfilter(b, a, yRev, zi.map((z) => z * yRev[0]));
  return y2.reverse().slice(padlen, ext.length - padlen);
}

export function butterLowpass(values: number[], cutoffHz = CUTOFF_HZ, fs = SAMPLE_RATE_HZ, order = 4): number[] {
  const { b, a } = butterCoeffs(order, cutoffHz, fs);
  return filtfilt(b, a, values);
}

const round3 = (x: number) => Math.round(x * 1000) / 1000;

/**
 * A smoothed copy of a curve (the original is not changed). The filter is designed for the
 * curve's MEASURED rate, so it is right for the 50 Hz simulator and a 10 or 80 Hz HX711 alike.
 */
export function filterReadings(readings: Reading[], method: "butter" | "moving_average" = "butter"): Reading[] {
  const forces = readings.map((r) => r.force_kg);
  const fs = estimateRateHz(readings);
  const cutoff = Math.min(CUTOFF_HZ, 0.4 * fs); // must stay below half the sample rate (Nyquist)
  let smooth: number[];
  if (readings.length < MIN_POINTS) smooth = forces;
  else if (method === "moving_average") smooth = movingAverage(forces);
  else smooth = butterLowpass(forces, cutoff, fs);
  return readings.map((r, i) => ({ time_ms: r.time_ms, force_kg: round3(smooth[i]) }));
}

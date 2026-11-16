// Realistic force curves for trying the app without the device. Port of fake_data.py.
// Lines use the simulator format "t_ms,force_kg" at 50 samples/s.
//
// Difference from fake_data.make_lines(): the Python version picks a fault type but then always
// returns a clean curve, so its faults never appear. Here the fault really is used, which lets
// visitors see the quality check work. The fault ranges are also narrowed (false-start offset
// 12-35 % instead of 5-35 %, slip drop 30-50 % instead of 15-50 %, submaximal rise 0.4-0.7 s
// instead of 0.3-0.7 s) so a simulated fault is a clear one, not a borderline case the rules
// could reasonably call "good".

import type { Hand, TestKind } from "./types";

export const SAMPLE_RATE_HZ = 50;
export const DT_MS = 1000 / SAMPLE_RATE_HZ;
export const FAKE_PEAKS: Record<Hand, number> = { right: 34, left: 31 };
export const TRIAL_KINDS = ["good", "false_start", "slip", "submaximal"] as const;
export type TrialKind = (typeof TRIAL_KINDS)[number];
export const FAKE_BAD_RATE = 0.2;

export type Rng = () => number;

/** Small seeded random generator (mulberry32) so tests can repeat a curve exactly. */
export function seeded(seed: number): Rng {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const uniform = (rng: Rng, lo: number, hi: number) => lo + (hi - lo) * rng();
function gauss(rng: Rng, mu: number, sigma: number): number {
  const u = 1 - rng(); // Box-Muller
  const v = rng();
  return mu + sigma * Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v);
}

interface MaxOptions {
  durationS?: number;
  riseTauS?: number;
  noiseKg?: number;
  startKg?: number;
  slipS?: number | null;
  slipDrop?: number;
}

export function maxGripCurve(peakKg: number, rng: Rng, o: MaxOptions = {}): string[] {
  const { durationS = 5, riseTauS = 0.15, noiseKg = 0.15, startKg = 0, slipS = null, slipDrop = 0 } = o;
  const startS = 0.5;
  const releaseS = 3.5;
  const holdDrop = 0.03;
  const heldKg = peakKg * (1 - holdDrop * (releaseS - startS));
  const lines: string[] = [];
  for (let i = 0; i < Math.floor(durationS * SAMPLE_RATE_HZ); i++) {
    const t = i / SAMPLE_RATE_HZ;
    let force: number;
    if (t < startS) force = startKg;
    else if (t < releaseS) {
      const rise = 1 - Math.exp(-(t - startS) / riseTauS);
      const hold = 1 - holdDrop * (t - startS);
      force = startKg + (peakKg - startKg) * rise * hold;
      if (slipS !== null && slipS <= t && t < slipS + 0.3) force *= 1 - slipDrop;
    } else force = heldKg * (1 - (t - releaseS) / 0.3);
    force = Math.max(0, force + gauss(rng, 0, noiseKg));
    lines.push(`${Math.round(i * DT_MS)},${force.toFixed(2)}`);
  }
  return lines;
}

export function generateCurve(peakKg: number, kind: TrialKind, rng: Rng, durationS = 5): string[] {
  switch (kind) {
    case "good":
      return maxGripCurve(peakKg, rng, { durationS, riseTauS: uniform(rng, 0.08, 0.3), startKg: peakKg * uniform(rng, 0, 0.05) });
    case "false_start":
      return maxGripCurve(peakKg, rng, { durationS, riseTauS: uniform(rng, 0.08, 0.3), startKg: peakKg * uniform(rng, 0.12, 0.35) });
    case "slip":
      return maxGripCurve(peakKg, rng, { durationS, riseTauS: uniform(rng, 0.08, 0.3), slipS: uniform(rng, 1.2, 2.8), slipDrop: uniform(rng, 0.3, 0.5) });
    case "submaximal":
      return maxGripCurve(peakKg * uniform(rng, 0.5, 0.8), rng, { durationS, riseTauS: uniform(rng, 0.4, 0.7), noiseKg: 0.3 });
  }
}

export function fatigueCurve(peakKg: number, rng: Rng, durationS = 32): string[] {
  const startS = 1;
  const squeezeS = 30;
  const riseTauS = 0.2;
  const fadeTauS = 15;
  const lines: string[] = [];
  for (let i = 0; i < Math.floor(durationS * SAMPLE_RATE_HZ); i++) {
    const t = i / SAMPLE_RATE_HZ;
    let force = 0;
    if (t >= startS && t <= startS + squeezeS) {
      const rise = 1 - Math.exp(-(t - startS) / riseTauS);
      const fade = 0.5 + 0.5 * Math.exp(-(t - startS) / fadeTauS);
      force = peakKg * rise * fade;
    }
    force = Math.max(0, force + gauss(rng, 0, 0.3));
    lines.push(`${Math.round(i * DT_MS)},${force.toFixed(2)}`);
  }
  return lines;
}

/** One simulated trial. Each is a little different, and about 1 in 5 maximal trials has a fault. */
export function makeLines(hand: Hand, test: TestKind, durationS: number, rng: Rng = Math.random, forceKind?: TrialKind): string[] {
  const peak = FAKE_PEAKS[hand] * uniform(rng, 0.93, 1);
  if (test === "fatigue") return fatigueCurve(peak, rng, durationS);
  let kind: TrialKind = forceKind ?? "good";
  if (!forceKind && rng() < FAKE_BAD_RATE) kind = TRIAL_KINDS[1 + Math.floor(rng() * 3)];
  return generateCurve(peak, kind, rng, durationS);
}

// Comparison with published norms. Port of grip_compare.py.

import { NORMS, type NormRow } from "../data/norms";
import type { Sex } from "./types";

/** Young-adult peak (age ~32) from Dodds 2014, used for the T-score. */
export const PEAK: Record<Sex, { mean: number; sd: number }> = {
  male: { mean: 51.9, sd: 9.9 },
  female: { mean: 31.4, sd: 6.1 },
};

/** Low-grip-strength cut-offs, defined for adults aged 65 and over. */
export const CUTOFFS: Record<string, Record<Sex, number>> = {
  EWGSOP2: { male: 27, female: 16 },
  "AWGS 2019": { male: 28, female: 18 },
};

export type Band =
  | "below 10th percentile"
  | "10th-25th percentile"
  | "25th-50th percentile"
  | "50th-75th percentile"
  | "75th-90th percentile"
  | "above 90th percentile";

export interface Assessment {
  force: number;
  age: number;
  sex: Sex;
  ref_age: number;
  median: number;
  band: Band;
  z: number;
  percentile: number;
  t: number;
  cutoffs: Record<string, { applies: boolean; below: boolean | null; limit: number; text: string }>;
}

/** Closest age with the same sex. On a tie the younger row wins (same as the Python loop). */
export function findNormRow(age: number, sex: Sex, norms: NormRow[] = NORMS): NormRow {
  let best: NormRow | null = null;
  let bestGap = Infinity;
  for (const row of norms) {
    if (row.sex !== sex) continue;
    const gap = Math.abs(row.age - age);
    if (gap < bestGap) {
      bestGap = gap;
      best = row;
    }
  }
  if (!best) throw new Error(`No normative data for ${sex}`);
  return best;
}

export function percentileBand(force: number, row: NormRow): Band {
  if (force < row.p10) return "below 10th percentile";
  if (force < row.p25) return "10th-25th percentile";
  if (force < row.p50) return "25th-50th percentile";
  if (force < row.p75) return "50th-75th percentile";
  if (force < row.p90) return "75th-90th percentile";
  return "above 90th percentile";
}

/** Error function: Taylor series near 0, continued fraction in the tails (both accurate to ~1e-14). */
export function erf(x: number): number {
  const sign = x < 0 ? -1 : 1;
  const ax = Math.abs(x);
  if (ax < 3) {
    let term = ax;
    let sum = ax;
    for (let n = 1; n < 100; n++) {
      term *= (-ax * ax) / n;
      const add = term / (2 * n + 1);
      sum += add;
      if (Math.abs(add) < 1e-17) break;
    }
    return sign * (2 / Math.sqrt(Math.PI)) * sum;
  }
  let frac = 0; // erfc(x) = exp(-x^2)/sqrt(pi) / (x + (1/2)/(x + 1/(x + (3/2)/(x + ...))))
  for (let k = 60; k >= 1; k--) frac = k / 2 / (ax + frac);
  const erfc = Math.exp(-ax * ax) / Math.sqrt(Math.PI) / (ax + frac);
  return sign * (1 - erfc);
}

export const normalCdf = (z: number) => 0.5 * (1 + erf(z / Math.SQRT2));

const round = (x: number, d: number) => Math.round(x * 10 ** d) / 10 ** d;

export function assess(force: number, age: number, sex: Sex): Assessment {
  const row = findNormRow(age, sex);
  const z = (force - row.mean) / row.sd;
  const cutoffs: Assessment["cutoffs"] = {};
  for (const [name, values] of Object.entries(CUTOFFS)) {
    const limit = values[sex];
    if (age < 65) {
      cutoffs[name] = { applies: false, below: null, limit, text: "not applicable (defined for age 65+)" };
    } else if (force < limit) {
      cutoffs[name] = { applies: true, below: true, limit, text: `below cut-off (< ${limit} kg)` };
    } else {
      cutoffs[name] = { applies: true, below: false, limit, text: `at or above cut-off (>= ${limit} kg)` };
    }
  }
  return {
    force,
    age,
    sex,
    ref_age: row.age,
    median: row.p50,
    band: percentileBand(force, row),
    z: round(z, 2),
    percentile: round(normalCdf(z) * 100, 1),
    t: round((force - PEAK[sex].mean) / PEAK[sex].sd, 2),
    cutoffs,
  };
}

export function normsFor(sex: Sex): NormRow[] {
  return NORMS.filter((r) => r.sex === sex);
}

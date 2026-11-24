// Calibration arithmetic for the Calibrate page: turn "this mass gave this many counts" into counts per kg,
// check it on a weight the fit never saw, and decide when a hanging weight has stopped moving.
// Same model as software/calibrate.py: net = countsPerKg * mass + intercept, least squares.

export const DATASHEET_COUNTS_PER_KG = 42952;
export const LB_PER_KG = 2.2046226218;
/** The firmware refuses anything outside this range (command C). */
export const FIRMWARE_MIN_CPK = 10000;
export const FIRMWARE_MAX_CPK = 100000;
/** A result further than this from the datasheet usually means a rig problem, not a strange cell. */
export const PLAUSIBLE_FRACTION = 0.3;
/** Check-weight error that counts as a pass (same as VT-10 C3). */
export const CHECK_PASS_PCT = 2;

export interface CalPoint {
  massKg: number;
  /** Mean net counts while the mass hung still. */
  net: number;
}

export interface CalFit {
  countsPerKg: number;
  interceptCounts: number;
  /** Largest distance of a point from the line, in kg. 0 with only two points. */
  maxResidualKg: number;
  points: number;
}

export function fitCalibration(points: CalPoint[]): CalFit {
  const n = points.length;
  if (n < 2) throw new Error("Need the zero reading and at least one weight.");
  const mx = points.reduce((a, p) => a + p.massKg, 0) / n;
  const my = points.reduce((a, p) => a + p.net, 0) / n;
  let sxx = 0;
  let sxy = 0;
  for (const p of points) {
    sxx += (p.massKg - mx) ** 2;
    sxy += (p.massKg - mx) * (p.net - my);
  }
  if (sxx === 0) throw new Error("The weights must differ from zero and from each other.");
  const countsPerKg = sxy / sxx;
  const interceptCounts = my - countsPerKg * mx;
  const maxResidualKg = Math.max(...points.map((p) => Math.abs(p.net - (countsPerKg * p.massKg + interceptCounts)) / Math.abs(countsPerKg)));
  return { countsPerKg, interceptCounts, maxResidualKg, points: n };
}

/** What the fit says the check weight weighs, and the error against its real mass. */
export function checkWeight(fit: CalFit, check: CalPoint): { predictedKg: number; errorPct: number; pass: boolean } {
  const predictedKg = (check.net - fit.interceptCounts) / fit.countsPerKg;
  const errorPct = ((predictedKg - check.massKg) / check.massKg) * 100;
  return { predictedKg, errorPct, pass: Math.abs(errorPct) <= CHECK_PASS_PCT };
}

export type Plausibility = "ok" | "unusual" | "impossible";

export function plausibility(countsPerKg: number): Plausibility {
  if (!(countsPerKg >= FIRMWARE_MIN_CPK && countsPerKg <= FIRMWARE_MAX_CPK)) return "impossible";
  return Math.abs(countsPerKg / DATASHEET_COUNTS_PER_KG - 1) <= PLAUSIBLE_FRACTION ? "ok" : "unusual";
}

export interface WindowStats {
  mean: number;
  sd: number;
  n: number;
}

export function stats(values: number[]): WindowStats {
  const n = values.length;
  if (n === 0) return { mean: 0, sd: 0, n: 0 };
  const mean = values.reduce((a, v) => a + v, 0) / n;
  const sd = Math.sqrt(values.reduce((a, v) => a + (v - mean) ** 2, 0) / n);
  return { mean, sd, n };
}

/** At 10 samples/s: 2 s of samples. */
export const STEADY_SAMPLES = 20;

/** Allowed wobble while "steady": bench noise is about ±70 counts at rest; a hanging weight sways a little more. */
export function steadyLimit(mean: number): number {
  return Math.max(120, Math.abs(mean) * 0.0015);
}

/** True when the last STEADY_SAMPLES values sit still: small spread and no drift between the two halves. */
export function isSteady(values: number[]): boolean {
  if (values.length < STEADY_SAMPLES) return false;
  const w = values.slice(-STEADY_SAMPLES);
  const s = stats(w);
  const half = STEADY_SAMPLES / 2;
  const drift = Math.abs(stats(w.slice(half)).mean - stats(w.slice(0, half)).mean);
  const lim = steadyLimit(s.mean);
  return s.sd <= lim && drift <= lim;
}

/** "20261123" for the firmware's C command, from the browser's local date. */
export function dateStamp(d = new Date()): string {
  const p = (x: number) => String(x).padStart(2, "0");
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}`;
}

export function toKg(value: number, unit: "kg" | "lb"): number {
  return unit === "kg" ? value : value / LB_PER_KG;
}

/** Calibration record as CSV: a header block, every point, and every captured sample. */
export function calibrationCsv(opts: {
  date: Date;
  firmware: string | null;
  previousCountsPerKg: number | null;
  fit: CalFit;
  points: (CalPoint & { label: string; samples: number[] })[];
  check: (CalPoint & { samples: number[]; predictedKg: number; errorPct: number }) | null;
  noiseSd: number;
  savedToDevice: boolean;
}): string {
  const r = (x: number, d = 1) => x.toFixed(d);
  const lines = [
    "# GripCheck calibration record",
    `# date=${opts.date.toISOString()}`,
    `# firmware=${opts.firmware ?? "unknown"}`,
    `# previous_counts_per_kg=${opts.previousCountsPerKg ?? "unknown"}`,
    `# counts_per_kg=${r(opts.fit.countsPerKg)}`,
    `# intercept_counts=${r(opts.fit.interceptCounts)}`,
    `# max_residual_kg=${r(opts.fit.maxResidualKg, 3)}`,
    `# rest_noise_sd_counts=${r(opts.noiseSd)}`,
    opts.check
      ? `# check_weight_kg=${r(opts.check.massKg, 3)} predicted_kg=${r(opts.check.predictedKg, 3)} error_pct=${r(opts.check.errorPct, 2)}`
      : "# check_weight=none",
    `# saved_to_device=${opts.savedToDevice ? "yes" : "no"}`,
    "point,label,mass_kg,mean_net_counts,sample_index,net_counts",
  ];
  const all = [...opts.points.map((p) => ({ ...p, kind: "fit" })), ...(opts.check ? [{ ...opts.check, label: "check weight", kind: "check" }] : [])];
  all.forEach((p, i) => {
    p.samples.forEach((v, j) => lines.push([i, `${p.kind}:${p.label}`, r(p.massKg, 3), r(p.net), j, v].join(",")));
  });
  return lines.join("\n") + "\n";
}

// The standard test, and scoring one recorded trial. Port of the protocol parts of grip_test.py
// and webapp.py (build_plan, read_user, _score_trial, summarize).

import { estimateRateHz, filterReadings } from "./filters";
import { asymmetry, cvPct, fatigueIndexPct, trialMetrics } from "./metrics";
import { checkTrial } from "./quality";
import type { Hand, Participant, Reading, Step, TrialResult } from "./types";

export const TRIALS_PER_HAND = 3;
export const TRIAL_SECONDS = 5;
export const FATIGUE_SECONDS = 32; // 30 s squeeze plus a second either side
export const REST_SECONDS = { simulated: 3, device: 60 } as const;
export const MAX_PLAUSIBLE_KG = 150; // the cell is rated 100 kg; far above that means "not calibrated"
export const MIN_RATE_HZ = 40; // RFD needs at least this; the HX711 defaults to 10 Hz
export const BAUD = 115200;

export const PROMPT_POSTURE = ["Sit upright", "Elbow at 90°", "Forearm neutral", "Wrist straight"];
export const PROMPT_GO = "Squeeze as hard as you can!";
export const PROMPT_FATIGUE = "Squeeze as hard as you can and keep squeezing for 30 seconds!";

/** Firmware COUNTS_PER_KG is a datasheet estimate until the known-mass calibration (gate G3) is done. */
export const CALIBRATION: "estimated" | "measured" = "estimated";
export const CALIBRATION_NOTE =
  "Forces are estimated from the load-cell datasheet (about ±10 %), not from a measured calibration, so peak values and percentiles are approximate.";

/** Alternate hands three times (dominant first), then the 30 s fatigue test on the dominant hand. */
export function buildPlan(dominant: Hand): Step[] {
  const other: Hand = dominant === "right" ? "left" : "right";
  const plan: Step[] = [];
  for (let trial = 1; trial <= TRIALS_PER_HAND; trial++) {
    for (const hand of [dominant, other]) plan.push({ hand, trial, test: "max", seconds: TRIAL_SECONDS });
  }
  plan.push({ hand: dominant, trial: 1, test: "fatigue", seconds: FATIGUE_SECONDS });
  return plan;
}

// ---------- participant form ----------

export type FormValues = Record<string, string | boolean | undefined>;

function readNumber(data: FormValues, key: string, label: string, low: number, high: number, required: boolean): number | null {
  const raw = data[key];
  if (raw === undefined || raw === "" || typeof raw === "boolean") {
    if (required) throw new Error(`Please enter ${label.toLowerCase()}.`);
    return null;
  }
  const n = Number(raw);
  if (!Number.isFinite(n)) throw new Error(`${label} must be a number.`);
  if (n < low || n > high) throw new Error(`${label} must be between ${low} and ${high}.`);
  return n;
}

/** Same limits as the Python app. Throws an Error whose message is shown under the form. */
export function readParticipant(data: FormValues): Participant {
  const age = readNumber(data, "age", "Age", 5, 100, true)!;
  if (!Number.isInteger(age)) throw new Error("Age must be a whole number.");
  const sex = String(data.sex ?? "").toLowerCase();
  const dominant = String(data.dominant ?? "").toLowerCase();
  if (sex !== "male" && sex !== "female") throw new Error("Please choose male or female (the normative data are reported by sex).");
  if (dominant !== "right" && dominant !== "left") throw new Error("Please choose the dominant hand.");
  return {
    participant_id: String(data.participant_id ?? "").trim().slice(0, 40),
    age,
    sex,
    dominant,
    height_cm: readNumber(data, "height_cm", "Height", 100, 230, false),
    weight_kg: readNumber(data, "weight_kg", "Weight", 20, 250, false),
    injury: Boolean(data.injury),
  };
}

// ---------- scoring one trial ----------

export class TrialError extends Error {}

/** Check, filter and score one recorded trial. Throws TrialError with a message for the user. */
export function scoreTrial(step: Step, readings: Reading[], skipped: string[] = []): TrialResult {
  if (readings.length === 0) {
    const hint = skipped.length ? ` First non-data line: "${skipped[0]}"` : "";
    throw new TrialError("No data received. Check the USB cable." + hint);
  }
  const notes: string[] = [];
  const rate = estimateRateHz(readings);
  if (rate < MIN_RATE_HZ) {
    notes.push(
      `Data arrived at about ${Math.round(rate)} samples/s. RFD needs at least ${MIN_RATE_HZ}, so it is shown as n/a.`,
    );
  }
  const rawPeak = Math.max(...readings.map((r) => r.force_kg));
  if (rawPeak > MAX_PLAUSIBLE_KG) {
    throw new TrialError(
      `A peak of ${rawPeak.toFixed(0)} "kg" is not physically possible. The firmware is probably not calibrated: run software/calibrate.py and set COUNTS_PER_KG.`,
    );
  }
  const smooth = filterReadings(readings);
  const metrics = trialMetrics(smooth);
  let quality: TrialResult["quality"] = null;
  if (step.test === "max") quality = checkTrial(smooth);
  else metrics.fatigue_index_pct = fatigueIndexPct(smooth);
  return { step, readings, smooth, metrics, quality, rate_hz: rate, notes };
}

// ---------- session summary ----------

export interface Summary {
  right: TrialResult;
  left: TrialResult;
  ratio: number | null;
  weaker_pct: number | null;
  fatigue_index_pct: number | null;
  overall_peak_kg: number;
  stronger: Hand;
  cv_pct: Record<Hand, number | null>;
}

export function bestTrial(trials: TrialResult[], hand: Hand): TrialResult {
  let best: TrialResult | null = null;
  for (const t of trials) {
    if (t.step.hand === hand && t.step.test === "max" && (!best || t.metrics.peak_kg > best.metrics.peak_kg)) best = t;
  }
  if (!best) throw new Error(`No ${hand}-hand trial recorded.`);
  return best;
}

export function summarize(trials: TrialResult[]): Summary {
  const max = trials.filter((t) => t.step.test === "max");
  const fatigue = trials.find((t) => t.step.test === "fatigue");
  const right = bestTrial(max, "right");
  const left = bestTrial(max, "left");
  const { ratio, weakerPct } = asymmetry(left.metrics.peak_kg, right.metrics.peak_kg);
  const peaks = (hand: Hand) => max.filter((t) => t.step.hand === hand).map((t) => t.metrics.peak_kg);
  return {
    right,
    left,
    ratio,
    weaker_pct: weakerPct,
    fatigue_index_pct: fatigue?.metrics.fatigue_index_pct ?? null,
    overall_peak_kg: Math.max(right.metrics.peak_kg, left.metrics.peak_kg),
    stronger: right.metrics.peak_kg >= left.metrics.peak_kg ? "right" : "left",
    cv_pct: { right: cvPct(peaks("right")), left: cvPct(peaks("left")) },
  };
}

/** Format a number for display; "n/a" for metrics that could not be computed. */
export function fmt(x: number | null | undefined, digits = 1): string {
  return x === null || x === undefined || !Number.isFinite(x) ? "n/a" : x.toFixed(digits);
}

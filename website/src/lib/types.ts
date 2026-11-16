// Shared shapes for the whole analysis pipeline. Names match the Python app (grip_test.py, metrics.py)
// so a reading here is the same thing as a reading there.

export type Hand = "right" | "left";
export type Sex = "male" | "female";
export type TestKind = "max" | "fatigue";
export type QualityLabel = "good" | "false_start" | "slip" | "submaximal";

/** One sample: time since the trial started (ms) and force (kg). */
export interface Reading {
  time_ms: number;
  force_kg: number;
}

export interface Step {
  hand: Hand;
  trial: number;
  test: TestKind;
  seconds: number;
}

export interface TrialMetrics {
  peak_kg: number;
  time_to_peak_ms: number;
  /** null when there are too few samples in the 200 ms window (e.g. a 10 Hz HX711). */
  rfd_n_per_s: number | null;
  fatigue_index_pct?: number | null;
}

export interface TrialResult {
  step: Step;
  readings: Reading[];
  smooth: Reading[];
  metrics: TrialMetrics;
  quality: QualityLabel | null;
  rate_hz: number;
  notes: string[];
}

export interface Participant {
  participant_id: string;
  age: number;
  sex: Sex;
  dominant: Hand;
  height_cm: number | null;
  weight_kg: number | null;
  injury: boolean;
}

export type DataSource = "simulated" | "device";

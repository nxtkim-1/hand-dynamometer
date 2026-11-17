// Deterministic simulated sample session so visitors can inspect a complete
// GripCheck report (including a flagged slip trial and 30 s fatigue hold) in one click.

import { linesToReadings } from "./parse";
import { buildPlan, scoreTrial } from "./protocol";
import { makeLines, seeded, type TrialKind } from "./simulator";
import type { Session } from "./storage";
import type { TrialResult } from "./types";

export const SAMPLE_SESSION_ID = "sample-demo";

export function buildSampleSession(id = SAMPLE_SESSION_ID): Session {
  const rng = seeded(202611);
  const plan = buildPlan("right");
  // Make trial index 2 (R2) a clear slip so the report showcases quality flagging & best-of-3 selection
  const kinds: (TrialKind | undefined)[] = ["good", "good", "slip", "good", "good", "good", undefined];
  const trials: TrialResult[] = plan.map((step, i) => {
    const lines = makeLines(step.hand, step.test, step.seconds, rng, kinds[i]);
    const { readings, skipped } = linesToReadings(lines);
    return scoreTrial(step, readings, skipped);
  });

  return {
    id,
    created: "2026-11-16T14:30:00.000Z",
    source: "simulated",
    calibration: null,
    participant: {
      participant_id: "DEMO-01",
      age: 29,
      sex: "male",
      dominant: "right",
      height_cm: 178,
      weight_kg: 74,
      injury: false,
    },
    trials,
  };
}

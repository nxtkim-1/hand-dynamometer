// Parity tests: the TypeScript analysis must give the same answers as the Python app.
// Reference values come from scripts/make_fixtures.py, which runs the original Python code.

import { describe, expect, it } from "vitest";
import ref from "./__fixtures__/reference.json";
import { estimateRateHz, filterReadings } from "./filters";
import { asymmetry, fatigueIndexPct, trialMetrics } from "./metrics";
import { assess } from "./norms";
import { linesToReadings } from "./parse";
import { extractFeatures, ruleCheck } from "./quality";

type Case = (typeof ref.cases)[number];

describe.each(ref.cases.map((c) => [c.name, c] as [string, Case]))("curve %s", (_name, c) => {
  const { readings } = linesToReadings(c.lines);
  const smooth = filterReadings(readings);

  it("measures the same sample rate", () => {
    expect(estimateRateHz(readings)).toBeCloseTo(c.rate_hz, 9);
  });

  it("filters to the same curve (Butterworth and moving average)", () => {
    expect(smooth).toHaveLength(c.smooth.length);
    smooth.forEach((r, i) => expect(Math.abs(r.force_kg - c.smooth[i])).toBeLessThanOrEqual(0.0011));
    filterReadings(readings, "moving_average").forEach((r, i) =>
      expect(Math.abs(r.force_kg - c.moving_average[i])).toBeLessThanOrEqual(0.0011),
    );
  });

  it("computes the same metrics", () => {
    const m = trialMetrics(smooth);
    expect(m.peak_kg).toBeCloseTo(c.metrics.peak_kg, 2);
    expect(m.time_to_peak_ms).toBe(c.metrics.time_to_peak_ms);
    if (c.metrics.rfd_n_per_s === null) expect(m.rfd_n_per_s).toBeNull();
    else expect(m.rfd_n_per_s!).toBeCloseTo(c.metrics.rfd_n_per_s, 0);
  });

  if (c.test === "max") {
    it("gets the same quality features and label", () => {
      const f = extractFeatures(smooth);
      const want = c.features!;
      expect(f.baseline_frac).toBeCloseTo(want.baseline_frac, 3);
      expect(f.rise_time_ms).toBe(want.rise_time_ms);
      expect(f.dip_frac).toBeCloseTo(want.dip_frac, 3);
      expect(f.hold_cv).toBeCloseTo(want.hold_cv, 3);
      expect(ruleCheck(f)).toBe(c.rule);
    });
  } else {
    it("gets the same fatigue index", () => {
      expect(fatigueIndexPct(smooth)!).toBeCloseTo(c.fatigue_index_pct!, 2);
    });
  }
});

describe("normative comparison", () => {
  it.each(ref.assessments.map((a) => [a.force, a.age, a.sex, a] as const))("%s kg, age %s, %s", (force, age, sex, want) => {
    const got = assess(force, age, sex as "male" | "female");
    expect(got.ref_age).toBe(want.ref_age);
    expect(got.median).toBe(want.median);
    expect(got.band).toBe(want.band);
    expect(got.z).toBe(want.z);
    expect(got.percentile).toBeCloseTo(want.percentile, 5);
    expect(got.t).toBe(want.t);
    for (const [name, text] of Object.entries(want.cutoffs)) expect(got.cutoffs[name].text).toBe(text);
  });
});

describe("asymmetry", () => {
  it.each(ref.asymmetry.map((a) => [a.left, a.right, a.result] as const))("left %s, right %s", (l, r, want) => {
    const got = asymmetry(l, r);
    if (want[0] === null) expect(got.ratio).toBeNull();
    else expect(got.ratio!).toBeCloseTo(want[0], 9);
    if (want[1] === null) expect(got.weakerPct).toBeNull();
    else expect(got.weakerPct!).toBeCloseTo(want[1], 9);
  });
});

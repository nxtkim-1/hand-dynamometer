import { describe, expect, it } from "vitest";
import { buildSampleSession, SAMPLE_SESSION_ID } from "./sampleSession";
import { summarize } from "./protocol";
import { convertKg, formatForce } from "./units";

describe("sampleSession", () => {
  it("builds a complete 7-trial session with one flagged slip trial", () => {
    const s = buildSampleSession();
    expect(s.id).toBe(SAMPLE_SESSION_ID);
    expect(s.trials).toHaveLength(7);
    expect(s.trials.some((t) => t.quality === "slip")).toBe(true);
    const sum = summarize(s.trials);
    expect(sum.overall_peak_kg).toBeGreaterThan(25);
    expect(sum.fatigue_index_pct).toBeGreaterThan(20);
  });
});

describe("units", () => {
  it("converts kg to lb without modifying kg", () => {
    expect(convertKg(10, "kg")).toBe(10);
    expect(convertKg(34, "lb")).toBeCloseTo(74.96, 1);
    expect(formatForce(34, "lb")).toBe("75.0");
  });
});

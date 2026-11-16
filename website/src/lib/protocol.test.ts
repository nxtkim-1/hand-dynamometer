// Behaviour tests for the parts that are new or differ from the Python app.

import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";
import { NORMS } from "../data/norms";
import { erf } from "./norms";
import { linesToReadings, parseCalibrationComment, parseLine } from "./parse";
import { buildPlan, readParticipant, scoreTrial, summarize, TrialError } from "./protocol";
import { checkTrial } from "./quality";
import { filterReadings } from "./filters";
import { makeLines, seeded, TRIAL_KINDS, type TrialKind } from "./simulator";
import type { Step, TrialResult } from "./types";

describe("parseLine", () => {
  it("reads both the simulator and the firmware format", () => {
    expect(parseLine("1200,31.50")).toEqual({ t: 1200, f: 31.5 });
    expect(parseLine("1234,52410,0,0.000")).toEqual({ t: 1234, f: 0 });
  });
  it("skips headers, comments and broken lines", () => {
    for (const line of ["t_ms,raw,net,force_kg", "# tared", "", "12", "1.5,3", "100,", "100,abc"]) {
      expect(parseLine(line)).toBeNull();
    }
  });
  it("restarts time at zero and keeps the skipped lines", () => {
    const { readings, skipped } = linesToReadings(["# tared", "5000,1,0,0.5", "5100,1,0,0.7"]);
    expect(readings).toEqual([{ time_ms: 0, force_kg: 0.5 }, { time_ms: 100, force_kg: 0.7 }]);
    expect(skipped).toEqual(["# tared"]);
  });
  it("finds the firmware's calibration comment", () => {
    expect(parseCalibrationComment("# calibration=estimated (datasheet, about +/-10 %)")).toBe("estimated");
    expect(parseCalibrationComment("# calibration=measured")).toBe("measured");
    expect(parseCalibrationComment("1,2,3,4")).toBeNull();
  });
});

describe("buildPlan", () => {
  it("alternates hands, dominant first, then the fatigue test", () => {
    const plan = buildPlan("left");
    expect(plan.map((s) => `${s.hand[0]}${s.trial}${s.test[0]}`)).toEqual(["l1m", "r1m", "l2m", "r2m", "l3m", "r3m", "l1f"]);
    expect(plan[6].seconds).toBe(32);
  });
});

describe("readParticipant", () => {
  const ok = { age: "21", sex: "female", dominant: "right" };
  it("accepts a valid form", () => {
    expect(readParticipant({ ...ok, height_cm: "170", injury: true })).toMatchObject({ age: 21, height_cm: 170, weight_kg: null, injury: true });
  });
  it.each([
    [{ ...ok, age: "" }, "Please enter age."],
    [{ ...ok, age: "4" }, "Age must be between 5 and 100."],
    [{ ...ok, age: "20.5" }, "Age must be a whole number."],
    [{ ...ok, sex: "" }, /male or female/],
    [{ ...ok, dominant: "both" }, "Please choose the dominant hand."],
    [{ ...ok, weight_kg: "900" }, "Weight must be between 20 and 250."],
  ])("rejects %j", (form, message) => {
    expect(() => readParticipant(form)).toThrow(message);
  });
});

describe("scoreTrial", () => {
  const step: Step = { hand: "right", trial: 1, test: "max", seconds: 5 };
  it("explains an empty recording", () => {
    expect(() => scoreTrial(step, [], ["garbage"])).toThrow(TrialError);
    expect(() => scoreTrial(step, [], ["garbage"])).toThrow(/garbage/);
  });
  it("stops on an impossible force (firmware not calibrated)", () => {
    const readings = Array.from({ length: 50 }, (_, i) => ({ time_ms: i * 20, force_kg: i * 10 }));
    expect(() => scoreTrial(step, readings)).toThrow(/not physically possible/);
  });
  it("warns about a 10 Hz device and reports RFD as n/a", () => {
    const lines = makeLines("right", "max", 5, seeded(3), "good").filter((_, i) => i % 5 === 0);
    const r = scoreTrial(step, linesToReadings(lines).readings);
    expect(r.metrics.rfd_n_per_s).toBeNull();
    expect(r.notes[0]).toMatch(/about 10 samples\/s/);
  });
});

describe("simulator", () => {
  it("is repeatable with a seed", () => {
    expect(makeLines("left", "max", 5, seeded(9))).toEqual(makeLines("left", "max", 5, seeded(9)));
  });
  it.each(TRIAL_KINDS.map((k) => [k]))("the quality rules recognise a simulated %s trial", (kind: TrialKind) => {
    for (let seed = 1; seed <= 25; seed++) {
      const { readings } = linesToReadings(makeLines("right", "max", 5, seeded(seed), kind));
      expect(checkTrial(filterReadings(readings))).toBe(kind);
    }
  });
});

describe("summarize", () => {
  it("takes the best trial per hand and the fatigue index", () => {
    const rng = seeded(42);
    const results: TrialResult[] = buildPlan("right").map((step) =>
      scoreTrial(step, linesToReadings(makeLines(step.hand, step.test, step.seconds, rng, step.test === "max" ? "good" : undefined)).readings),
    );
    const s = summarize(results);
    const rightPeaks = results.filter((r) => r.step.hand === "right" && r.step.test === "max").map((r) => r.metrics.peak_kg);
    expect(s.right.metrics.peak_kg).toBe(Math.max(...rightPeaks));
    expect(s.overall_peak_kg).toBe(Math.max(s.right.metrics.peak_kg, s.left.metrics.peak_kg));
    expect(s.fatigue_index_pct).toBeGreaterThan(20);
    expect(s.ratio).toBeCloseTo(s.left.metrics.peak_kg / s.right.metrics.peak_kg, 9);
    expect(s.cv_pct.right).not.toBeNull();
  });
});

describe("norms", () => {
  it("matches the repository's CSV exactly", () => {
    const csv = readFileSync(new URL("../../../data/dodds2014_norms.csv", import.meta.url), "utf-8").trim().split(/\r?\n/);
    const header = csv[0].split(",");
    const rows = csv.slice(1).map((line) => {
      const cells = line.split(",");
      return Object.fromEntries(header.map((h, i) => [h, h === "sex" ? cells[i] : Number(cells[i])]));
    });
    expect(NORMS).toEqual(rows);
  });
  it("erf is accurate in the middle and the tails", () => {
    expect(erf(0)).toBe(0);
    expect(erf(0.5)).toBeCloseTo(0.5204998778130465, 13);
    expect(erf(-1.5)).toBeCloseTo(-0.9661051464753108, 13);
    expect(erf(3.5)).toBeCloseTo(0.9999992569016276, 13);
  });
});

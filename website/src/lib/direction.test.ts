import { describe, expect, it } from "vitest";
import { linesToReadings, NEGATIVE_WARN_KG, parseLine, reverseLine } from "./parse";

describe("reverseLine (same effect as flipping SIGN in the firmware)", () => {
  it("flips net and force on a firmware line, keeps time and raw", () => {
    expect(reverseLine("1234,40100,-12300,-0.286")).toBe("1234,40100,12300,0.286");
    expect(reverseLine("1234,64700,12300,0.286")).toBe("1234,64700,-12300,-0.286");
  });

  it("keeps the number of decimals and never prints -0", () => {
    expect(reverseLine("10,52410,0,0.000")).toBe("10,52410,0,0.000");
    expect(reverseLine("10,52410,-5,-0.000")).toBe("10,52410,5,0.000");
  });

  it("flips the force on a simulator line", () => {
    expect(reverseLine("250,-18.42")).toBe("250,18.42");
  });

  it("leaves comments, headers and junk alone", () => {
    for (const line of ["# tared", "# calibration=estimated (datasheet, about +/-10 %)", "t_ms,raw,net,force_kg", "", "garbage"]) {
      expect(reverseLine(line)).toBe(line);
    }
  });

  it("flipping twice gives the original line", () => {
    const line = "98765,31000,-21400,-0.498";
    expect(reverseLine(reverseLine(line))).toBe(line);
  });

  it("turns a squeeze recorded the wrong way round into a positive curve", () => {
    // what the v4.2 frame sent with SIGN = -1: force goes down as the hand squeezes
    const wrong = ["0,52400,0,0.000", "100,-", "100,30000,-859000,-20.000", "200,22000,-1203000,-28.008", "300,52390,-10,-0.000"];
    const { readings } = linesToReadings(wrong.map(reverseLine));
    expect(Math.max(...readings.map((r) => r.force_kg))).toBeCloseTo(28.008, 3);
    expect(Math.min(...readings.map((r) => r.force_kg))).toBeGreaterThanOrEqual(0);
  });

  it("the warning threshold is far outside the bench noise (±70 counts ≈ 0.002 kg)", () => {
    expect(NEGATIVE_WARN_KG).toBeLessThan(-1);
    expect(parseLine(reverseLine("1,0,70,0.002"))!.f).toBeGreaterThan(NEGATIVE_WARN_KG);
  });
});

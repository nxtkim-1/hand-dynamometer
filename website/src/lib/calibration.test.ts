import { describe, expect, it } from "vitest";
import {
  calibrationCsv,
  checkWeight,
  dateStamp,
  fitCalibration,
  isSteady,
  plausibility,
  STEADY_SAMPLES,
  toKg,
} from "./calibration";
import { parseDeviceInfo, parseFirmwareLine } from "./parse";

describe("fitCalibration", () => {
  it("recovers counts per kg and intercept from exact points", () => {
    const fit = fitCalibration([
      { massKg: 0, net: 100 },
      { massKg: 10, net: 100 + 430000 },
      { massKg: 20, net: 100 + 860000 },
    ]);
    expect(fit.countsPerKg).toBeCloseTo(43000, 6);
    expect(fit.interceptCounts).toBeCloseTo(100, 6);
    expect(fit.maxResidualKg).toBeCloseTo(0, 9);
  });

  it("works with the zero reading plus one weight (two-point calibration)", () => {
    const fit = fitCalibration([
      { massKg: 0, net: -20 },
      { massKg: 21.4, net: -20 + 21.4 * 42985 },
    ]);
    expect(fit.countsPerKg).toBeCloseTo(42985, 6);
  });

  it("reports the largest miss from the line in kg", () => {
    // middle point sits 4,300 counts (0.1 kg at 43,000 counts/kg) above an otherwise straight line
    const fit = fitCalibration([
      { massKg: 0, net: 0 },
      { massKg: 10, net: 430000 + 4300 },
      { massKg: 20, net: 860000 },
    ]);
    expect(fit.maxResidualKg).toBeGreaterThan(0.05);
    expect(fit.maxResidualKg).toBeLessThan(0.1);
  });

  it("refuses too few points or masses that are all the same", () => {
    expect(() => fitCalibration([{ massKg: 0, net: 0 }])).toThrow();
    expect(() => fitCalibration([{ massKg: 5, net: 1 }, { massKg: 5, net: 2 }])).toThrow();
  });
});

describe("checkWeight", () => {
  const fit = fitCalibration([
    { massKg: 0, net: 0 },
    { massKg: 20, net: 860000 },
  ]);
  it("passes within 2 %", () => {
    const r = checkWeight(fit, { massKg: 16.92, net: 16.92 * 43000 * 1.01 });
    expect(r.errorPct).toBeCloseTo(1, 6);
    expect(r.pass).toBe(true);
  });
  it("fails above 2 %", () => {
    const r = checkWeight(fit, { massKg: 10, net: 10 * 43000 * 0.97 });
    expect(r.errorPct).toBeCloseTo(-3, 6);
    expect(r.pass).toBe(false);
  });
});

describe("plausibility", () => {
  it("accepts values near the datasheet, flags far ones, refuses what the firmware would refuse", () => {
    expect(plausibility(42952)).toBe("ok");
    expect(plausibility(42952 * 1.29)).toBe("ok");
    expect(plausibility(42952 * 1.4)).toBe("unusual");
    expect(plausibility(9000)).toBe("impossible");
    expect(plausibility(150000)).toBe("impossible");
    expect(plausibility(Number.NaN)).toBe("impossible");
  });
});

describe("isSteady", () => {
  const noise = (i: number) => ((i * 37) % 11) - 5; // deterministic ±5 counts
  it("needs a full window", () => {
    expect(isSteady(Array.from({ length: STEADY_SAMPLES - 1 }, () => 500000))).toBe(false);
  });
  it("is true for a still weight with bench-level noise", () => {
    expect(isSteady(Array.from({ length: 30 }, (_, i) => 920000 + noise(i) * 14))).toBe(true);
  });
  it("is false while the weight swings or the reading is still climbing", () => {
    expect(isSteady(Array.from({ length: 30 }, (_, i) => 920000 + (i % 2 ? 6000 : -6000)))).toBe(false);
    expect(isSteady(Array.from({ length: 30 }, (_, i) => 900000 + i * 1500))).toBe(false);
  });
});

describe("helpers", () => {
  it("converts pounds and stamps dates for the firmware", () => {
    expect(toKg(25, "lb")).toBeCloseTo(11.3398, 4);
    expect(toKg(3, "kg")).toBe(3);
    expect(dateStamp(new Date(2026, 10, 23))).toBe("20261123");
  });

  it("writes a calibration record with every sample", () => {
    const fit = fitCalibration([
      { massKg: 0, net: 0 },
      { massKg: 10, net: 430000 },
    ]);
    const csv = calibrationCsv({
      date: new Date("2026-11-23T12:00:00Z"),
      firmware: "1.1",
      previousCountsPerKg: 42952,
      fit,
      points: [
        { massKg: 0, net: 0, label: "zero", samples: [1, -1] },
        { massKg: 10, net: 430000, label: "10 kg", samples: [430010, 429990] },
      ],
      check: null,
      noiseSd: 30,
      savedToDevice: true,
    });
    expect(csv).toContain("# counts_per_kg=43000.0");
    expect(csv).toContain("# saved_to_device=yes");
    expect(csv.trim().split("\n").filter((l) => !l.startsWith("#")).length).toBe(1 + 4); // header + 4 samples
  });
});

describe("firmware v1.1 lines", () => {
  it("reads the settings comments", () => {
    expect(parseDeviceInfo("# hand_dynamometer_v1.1")).toEqual({ firmware: "1.1" });
    expect(parseDeviceInfo("# counts_per_kg=42984.8")).toEqual({ countsPerKg: 42984.8 });
    expect(parseDeviceInfo("# sign=-1")).toEqual({ sign: -1 });
    expect(parseDeviceInfo("# sign=1")).toEqual({ sign: 1 });
    expect(parseDeviceInfo("# calibration=measured 2026-11-23")).toEqual({ calibration: "measured", calibratedOn: "2026-11-23" });
    expect(parseDeviceInfo("# calibration=estimated (datasheet, about +/-10 %)")).toEqual({ calibration: "estimated", calibratedOn: null });
    expect(parseDeviceInfo("# tared")).toEqual({});
    expect(parseDeviceInfo("1234,52410,0,0.000")).toEqual({});
  });

  it("splits a data line into its four columns, and ignores simulator lines", () => {
    expect(parseFirmwareLine("1234,64700,12300,0.286")).toEqual({ t: 1234, raw: 64700, net: 12300, kg: 0.286 });
    expect(parseFirmwareLine("250,18.42")).toBeNull();
    expect(parseFirmwareLine("# tared")).toBeNull();
  });
});

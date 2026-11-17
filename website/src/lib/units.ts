// Display unit helper (kg default, optional lb conversion for clinical familiarity).
// All saved readings, norms, and CSV exports remain strictly in kg.

export type ForceUnit = "kg" | "lb";

export const KG_TO_LB = 2.2046226218;
const UNIT_KEY = "gripcheck.unit.v1";

export function getStoredUnit(): ForceUnit {
  try {
    return localStorage.getItem(UNIT_KEY) === "lb" ? "lb" : "kg";
  } catch {
    return "kg";
  }
}

export function setStoredUnit(unit: ForceUnit) {
  try {
    localStorage.setItem(UNIT_KEY, unit);
  } catch {
    /* ignore */
  }
}

export function convertKg(kg: number, unit: ForceUnit): number {
  return unit === "lb" ? kg * KG_TO_LB : kg;
}

export function formatForce(kg: number, unit: ForceUnit, digits = 1): string {
  return convertKg(kg, unit).toFixed(digits);
}

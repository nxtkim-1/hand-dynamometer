// Dodds RM et al. (2014) Grip Strength across the Life Course. PLoS ONE 9(12): e113637. CC BY 4.0.
// Copied from ../data/dodds2014_norms.csv (Table 2). norms.test.ts fails if the two ever differ.

import type { Sex } from "../lib/types";

export interface NormRow { sex: Sex; age: number; p10: number; p25: number; p50: number; p75: number; p90: number; mean: number; sd: number }

export const NORMS: NormRow[] = [
  { sex: "male", age: 5, p10: 6, p25: 7, p50: 8, p75: 9, p90: 10, mean: 7.7, sd: 2.9 },
  { sex: "male", age: 10, p10: 12, p25: 15, p50: 17, p75: 20, p90: 22, mean: 17.2, sd: 4.1 },
  { sex: "male", age: 15, p10: 21, p25: 25, p50: 29, p75: 33, p90: 38, mean: 29.6, sd: 5.6 },
  { sex: "male", age: 20, p10: 30, p25: 35, p50: 40, p75: 46, p90: 52, mean: 41.5, sd: 7.3 },
  { sex: "male", age: 25, p10: 36, p25: 41, p50: 48, p75: 55, p90: 61, mean: 48.8, sd: 8.7 },
  { sex: "male", age: 30, p10: 38, p25: 44, p50: 51, p75: 58, p90: 64, mean: 51.6, sd: 9.6 },
  { sex: "male", age: 35, p10: 39, p25: 45, p50: 51, p75: 58, p90: 64, mean: 51.6, sd: 10.1 },
  { sex: "male", age: 40, p10: 38, p25: 44, p50: 50, p75: 57, p90: 63, mean: 50.3, sd: 10.3 },
  { sex: "male", age: 45, p10: 36, p25: 42, p50: 49, p75: 56, p90: 61, mean: 48.8, sd: 10.3 },
  { sex: "male", age: 50, p10: 35, p25: 41, p50: 48, p75: 54, p90: 60, mean: 47.6, sd: 10.1 },
  { sex: "male", age: 55, p10: 34, p25: 40, p50: 47, p75: 53, p90: 59, mean: 46.2, sd: 9.8 },
  { sex: "male", age: 60, p10: 33, p25: 39, p50: 45, p75: 51, p90: 56, mean: 44.6, sd: 9.2 },
  { sex: "male", age: 65, p10: 31, p25: 37, p50: 43, p75: 48, p90: 53, mean: 42.3, sd: 8.6 },
  { sex: "male", age: 70, p10: 29, p25: 34, p50: 39, p75: 44, p90: 49, mean: 39.1, sd: 8.1 },
  { sex: "male", age: 75, p10: 26, p25: 31, p50: 35, p75: 41, p90: 45, mean: 35.6, sd: 7.6 },
  { sex: "male", age: 80, p10: 23, p25: 27, p50: 32, p75: 37, p90: 42, mean: 32.2, sd: 7.3 },
  { sex: "male", age: 85, p10: 19, p25: 24, p50: 29, p75: 33, p90: 38, mean: 28.5, sd: 7.0 },
  { sex: "male", age: 90, p10: 16, p25: 20, p50: 25, p75: 29, p90: 33, mean: 24.7, sd: 6.8 },
  { sex: "female", age: 5, p10: 6, p25: 7, p50: 8, p75: 9, p90: 10, mean: 8.0, sd: 3.1 },
  { sex: "female", age: 10, p10: 12, p25: 14, p50: 16, p75: 19, p90: 21, mean: 16.7, sd: 3.8 },
  { sex: "female", age: 15, p10: 17, p25: 20, p50: 24, p75: 27, p90: 30, mean: 23.9, sd: 4.5 },
  { sex: "female", age: 20, p10: 21, p25: 24, p50: 28, p75: 32, p90: 36, mean: 28.4, sd: 5.1 },
  { sex: "female", age: 25, p10: 23, p25: 26, p50: 30, p75: 35, p90: 38, mean: 30.6, sd: 5.6 },
  { sex: "female", age: 30, p10: 24, p25: 27, p50: 31, p75: 35, p90: 39, mean: 31.4, sd: 6.0 },
  { sex: "female", age: 35, p10: 23, p25: 27, p50: 31, p75: 35, p90: 39, mean: 31.3, sd: 6.2 },
  { sex: "female", age: 40, p10: 23, p25: 27, p50: 31, p75: 35, p90: 39, mean: 30.7, sd: 6.3 },
  { sex: "female", age: 45, p10: 22, p25: 26, p50: 30, p75: 34, p90: 38, mean: 29.9, sd: 6.4 },
  { sex: "female", age: 50, p10: 21, p25: 25, p50: 29, p75: 33, p90: 37, mean: 28.7, sd: 6.4 },
  { sex: "female", age: 55, p10: 19, p25: 23, p50: 28, p75: 32, p90: 35, mean: 27.5, sd: 6.4 },
  { sex: "female", age: 60, p10: 18, p25: 22, p50: 27, p75: 31, p90: 34, mean: 26.5, sd: 6.2 },
  { sex: "female", age: 65, p10: 17, p25: 21, p50: 25, p75: 29, p90: 33, mean: 25.3, sd: 6.0 },
  { sex: "female", age: 70, p10: 16, p25: 20, p50: 24, p75: 27, p90: 31, mean: 23.5, sd: 5.7 },
  { sex: "female", age: 75, p10: 14, p25: 18, p50: 21, p75: 25, p90: 28, mean: 21.4, sd: 5.4 },
  { sex: "female", age: 80, p10: 13, p25: 16, p50: 19, p75: 23, p90: 26, mean: 19.1, sd: 5.1 },
  { sex: "female", age: 85, p10: 11, p25: 14, p50: 17, p75: 20, p90: 23, mean: 16.6, sd: 4.7 },
  { sex: "female", age: 90, p10: 9, p25: 11, p50: 14, p75: 17, p90: 20, mean: 14.2, sd: 4.4 },
];

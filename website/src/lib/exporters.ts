// CSV downloads in the same layout as grip_test.save_session(), so files from the website and
// from the Python app can be analysed together (history.py).

import { fmt, summarize } from "./protocol";
import type { Session } from "./storage";

const csvCell = (v: unknown) => {
  const s = v === null || v === undefined ? "" : String(v);
  return /[",\n]/.test(s) ? `"${s.replace(/"/g, '""')}"` : s;
};
const row = (cells: unknown[]) => cells.map(csvCell).join(",");

export function rawCsv(s: Session): string {
  const out = [row(["hand", "trial", "test", "time_ms", "force_kg"])];
  for (const t of s.trials) for (const r of t.readings) out.push(row([t.step.hand, t.step.trial, t.step.test, r.time_ms, r.force_kg]));
  return out.join("\n") + "\n";
}

export function summaryCsv(s: Session): string {
  const out = [row(["hand", "trial", "test", "peak_kg", "time_to_peak_ms", "rfd_n_per_s", "fatigue_index_pct", "quality"])];
  for (const t of s.trials) {
    const m = t.metrics;
    out.push(
      row([
        t.step.hand,
        t.step.trial,
        t.step.test,
        m.peak_kg,
        m.time_to_peak_ms,
        m.rfd_n_per_s === null ? "" : m.rfd_n_per_s.toFixed(1),
        m.fatigue_index_pct == null ? "" : m.fatigue_index_pct.toFixed(1),
        t.quality ?? "",
      ]),
    );
  }
  const sum = summarize(s.trials);
  out.push(row(["left_right_ratio", sum.ratio === null ? "" : sum.ratio.toFixed(3)]));
  out.push(row(["weaker_hand_pct", fmt(sum.weaker_pct) === "n/a" ? "" : fmt(sum.weaker_pct)]));
  return out.join("\n") + "\n";
}

export function download(filename: string, text: string, type = "text/csv") {
  const url = URL.createObjectURL(new Blob([text], { type }));
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

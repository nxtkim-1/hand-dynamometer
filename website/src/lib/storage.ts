// Saved sessions live only in this browser (localStorage). Nothing is uploaded anywhere.

import { filterReadings } from "./filters";
import { CALIBRATION } from "./protocol";
import type { DataSource, Participant, TrialResult } from "./types";

export interface Session {
  id: string;
  created: string; // ISO date
  source: DataSource;
  /** How the device's scale factor was obtained; null for simulated data. */
  calibration: "estimated" | "measured" | null;
  participant: Participant;
  trials: TrialResult[]; // in plan order; the last one is the fatigue test
}

const KEY = "gripcheck.sessions.v1";
const MAX_SESSIONS = 20;

export function newSessionId(): string {
  const d = new Date();
  const pad = (n: number) => String(n).padStart(2, "0");
  const stamp = `${d.getFullYear()}${pad(d.getMonth() + 1)}${pad(d.getDate())}-${pad(d.getHours())}${pad(d.getMinutes())}${pad(d.getSeconds())}`;
  return `${stamp}-${Math.random().toString(36).slice(2, 6)}`;
}

export function loadSessions(): Session[] {
  try {
    const raw = localStorage.getItem(KEY);
    const list = raw ? (JSON.parse(raw) as Session[]) : [];
    if (!Array.isArray(list)) return [];
    // the smoothed curves are not stored (they double the size); rebuild them from the raw readings
    for (const s of list) for (const t of s.trials) if (!t.smooth?.length) t.smooth = filterReadings(t.readings);
    return list;
  } catch {
    return [];
  }
}

export function getSession(id: string): Session | null {
  return loadSessions().find((s) => s.id === id) ?? null;
}

/** Save, newest first. Returns false if the browser refused (private mode, storage full). */
export function saveSession(session: Session): boolean {
  const compact = (s: Session): Session => ({ ...s, trials: s.trials.map((t) => ({ ...t, smooth: [] })) });
  let list = [session, ...loadSessions().filter((s) => s.id !== session.id)].slice(0, MAX_SESSIONS).map(compact);
  for (;;) {
    try {
      localStorage.setItem(KEY, JSON.stringify(list));
      return true;
    } catch {
      if (list.length <= 1) return false;
      list = list.slice(0, -1); // storage full: drop the oldest and try again
    }
  }
}

export function deleteSession(id: string) {
  try {
    const rest = loadSessions().filter((s) => s.id !== id);
    localStorage.setItem(KEY, JSON.stringify(rest.map((s) => ({ ...s, trials: s.trials.map((t) => ({ ...t, smooth: [] })) }))));
  } catch {
    /* nothing to do */
  }
}

export function calibrationFor(source: DataSource, fromDevice: "measured" | "estimated" | null): Session["calibration"] {
  if (source === "simulated") return null;
  return fromDevice ?? CALIBRATION;
}

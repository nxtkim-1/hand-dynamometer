// Minimal Web Audio API cues for the guided grip test (countdown ticks, squeeze start, trial end).
// Safe no-op if AudioContext is unavailable or muted.

let ctx: AudioContext | null = null;
const SOUND_KEY = "gripcheck.sound.v1";

export function getSoundEnabled(): boolean {
  try {
    const v = localStorage.getItem(SOUND_KEY);
    return v !== "off";
  } catch {
    return true;
  }
}

export function setSoundEnabled(on: boolean) {
  try {
    localStorage.setItem(SOUND_KEY, on ? "on" : "off");
  } catch {
    /* ignore */
  }
}

function getAudio(): AudioContext | null {
  if (typeof window === "undefined") return null;
  const Ctor = window.AudioContext ?? (window as unknown as { webkitAudioContext?: typeof AudioContext }).webkitAudioContext;
  if (!Ctor) return null;
  if (!ctx) ctx = new Ctor();
  if (ctx.state === "suspended") void ctx.resume().catch(() => {});
  return ctx;
}

function tone(freq: number, durationMs: number, delayMs = 0, gainPeak = 0.08, type: OscillatorType = "sine") {
  const audio = getAudio();
  if (!audio) return;
  try {
    const start = audio.currentTime + delayMs / 1000;
    const osc = audio.createOscillator();
    const gain = audio.createGain();
    osc.type = type;
    osc.frequency.setValueAtTime(freq, start);
    gain.gain.setValueAtTime(0.0001, start);
    gain.gain.exponentialRampToValueAtTime(gainPeak, start + 0.012);
    gain.gain.exponentialRampToValueAtTime(0.0001, start + durationMs / 1000);
    osc.connect(gain);
    gain.connect(audio.destination);
    osc.start(start);
    osc.stop(start + durationMs / 1000 + 0.02);
  } catch {
    /* ignore audio errors */
  }
}

export function cueCountdown(enabled: boolean) {
  if (!enabled) return;
  tone(520, 90, 0, 0.06);
}

export function cueGo(enabled: boolean) {
  if (!enabled) return;
  tone(880, 180, 0, 0.09);
}

export function cueDone(enabled: boolean) {
  if (!enabled) return;
  tone(660, 110, 0, 0.07);
  tone(880, 160, 115, 0.08);
}

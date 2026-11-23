// The guided grip test. Same protocol as grip_test.py / webapp.py:
// 3 maximal 5 s squeezes per hand (alternating, dominant first), then a 30 s fatigue squeeze.
//
// Stages:  setup -> participant -> zero (device only) -> trials -> saving
// Trial phases: ready -> countdown -> recording -> result -> resting -> (next trial)

import { useCallback, useEffect, useRef, useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { LiveChart, type Pt } from "../components/Charts";
import { useDevice, useLiveForce, useNegativeReading } from "../components/DeviceContext";
import { IconArrow, IconCheck, IconInfo, IconUsb, IconVolume, IconVolumeOff, IconWarn, IconWave } from "../components/Icons";
import { serialSupported } from "../lib/device";
import { linesToReadings, parseLine } from "../lib/parse";
import {
  buildPlan,
  CALIBRATION,
  CALIBRATION_NOTE,
  fmt,
  PROMPT_FATIGUE,
  PROMPT_GO,
  PROMPT_POSTURE,
  readParticipant,
  REST_SECONDS,
  scoreTrial,
  TrialError,
} from "../lib/protocol";
import { QUALITY_TEXT } from "../lib/quality";
import { makeLines } from "../lib/simulator";
import { cueCountdown, cueDone, cueGo, getSoundEnabled, setSoundEnabled } from "../lib/sound";
import { calibrationFor, newSessionId, saveSession, type Session } from "../lib/storage";
import type { DataSource, Participant, Step, TrialResult } from "../lib/types";
import { formatForce, getStoredUnit, setStoredUnit, type ForceUnit } from "../lib/units";

type Stage = "setup" | "participant" | "zero" | "trials" | "saving";
type Phase = "ready" | "countdown" | "recording" | "analysing" | "result" | "resting" | "error";

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const cap = (s: string) => s[0].toUpperCase() + s.slice(1);
const colorVarFor = (step: Step) => (step.test === "fatigue" ? "--fatigue" : `--${step.hand}`);
const stepLabel = (s: Step) => (s.test === "fatigue" ? "30 s hold" : `${s.hand[0].toUpperCase()}${s.trial}`);

/** Shown when the device reads clearly below zero. A squeeze only pushes the bars together, so there are
 *  two causes: the cell sits the other way round in this frame (flip the direction), or the device was
 *  zeroed while something pressed on it (zero again). The graphs start at 0, so negative force draws as
 *  a flat line on the axis, which is why the graph looks empty. */
function DirectionCheck(props: {
  negative: boolean;
  reversed: boolean;
  onReverse: (on: boolean) => void;
  onZero?: () => void;
  zeroing?: boolean;
}) {
  const { negative, reversed, onReverse, onZero, zeroing } = props;
  if (negative) {
    return (
      <div className="notice warn" role="alert">
        <IconWarn />
        <div style={{ display: "grid", gap: 8 }}>
          <span>
            <b>The force went below zero, so the graph has nothing to draw.</b> Squeezing can only push the bars together, so check which
            case this is:
          </span>
          <span>
            <b>Squeezing makes the number go more negative:</b> the load cell is mounted the other way round in this frame.{" "}
            <button type="button" className="btn btn-sm btn-secondary" onClick={() => onReverse(!reversed)}>
              {reversed ? "Undo reverse" : "Reverse direction"}
            </button>
          </span>
          <span>
            <b>It reads negative with nothing touching it:</b> it was zeroed while something pressed on it. Let go and zero again.
            {onZero && (
              <>
                {" "}
                <button type="button" className="btn btn-sm btn-secondary" disabled={zeroing} onClick={onZero}>
                  {zeroing ? "Zeroing… hands off" : "Zero again"}
                </button>
              </>
            )}
          </span>
        </div>
      </div>
    );
  }
  if (reversed) {
    return (
      <p className="muted small" style={{ margin: 0 }}>
        Direction reversed in this browser (same as flipping SIGN in the firmware).{" "}
        <button type="button" className="btn btn-sm btn-ghost" onClick={() => onReverse(false)}>
          Undo
        </button>
      </p>
    );
  }
  return null;
}

export default function TestPage() {
  const navigate = useNavigate();
  const { device, status, message, connect, reversed, setReversed } = useDevice();
  const liveKg = useLiveForce(device);
  const negative = useNegativeReading(device);

  const [stage, setStage] = useState<Stage>("setup");
  const [source, setSource] = useState<DataSource>(device ? "device" : "simulated");
  const [participant, setParticipant] = useState<Participant | null>(null);
  const [plan, setPlan] = useState<Step[]>([]);
  const [index, setIndex] = useState(0);
  const [results, setResults] = useState<(TrialResult | undefined)[]>([]);
  const [phase, setPhase] = useState<Phase>("ready");
  const [count, setCount] = useState<number | "go" | null>(null);
  const [error, setError] = useState("");
  const [formError, setFormError] = useState("");
  const [zeroing, setZeroing] = useState(false);
  const [restLeft, setRestLeft] = useState(0);
  const [soundOn, setSoundOn] = useState(getSoundEnabled);
  const [unit, setUnit] = useState<ForceUnit>(getStoredUnit);
  const soundRef = useRef(soundOn);
  soundRef.current = soundOn;

  // live recording: points are kept in a ref (no re-render per sample); `tick` redraws once per frame
  const pointsRef = useRef<Pt[]>([]);
  const [tick, setTick] = useState(0);
  const [live, setLive] = useState({ force: 0, peak: 0, left: 0 });
  const frameQueued = useRef(false);
  // every recording remembers the run id it started with; stopping the test or leaving the page
  // bumps the id, so an old recording loop notices it is stale and quietly ends
  const runId = useRef(0);
  const primaryRef = useRef<HTMLButtonElement>(null);

  useEffect(
    () => () => {
      runId.current++;
    },
    [],
  );

  // if the device is unplugged mid-test, the recording loop reports it; here we only keep `source` sane
  useEffect(() => {
    if (device && stage === "setup") setSource("device");
  }, [device, stage]);

  const step = plan[index];
  const restSeconds = REST_SECONDS[source];
  const showCalibrationBanner = source === "device" && (device?.calibration ?? CALIBRATION) !== "measured";

  function toggleSound() {
    const next = !soundOn;
    setSoundOn(next);
    setSoundEnabled(next);
  }

  function changeUnit(next: ForceUnit) {
    setUnit(next);
    setStoredUnit(next);
  }

  const queueFrame = useCallback((left: number) => {
    if (frameQueued.current) return;
    frameQueued.current = true;
    requestAnimationFrame(() => {
      frameQueued.current = false;
      const pts = pointsRef.current;
      const lastPt = pts[pts.length - 1];
      setLive({ force: lastPt?.f ?? 0, peak: pts.reduce((m, p) => Math.max(m, p.f), 0), left });
      setTick((t) => t + 1);
    });
  }, []);

  // ---------- rest timer ----------
  useEffect(() => {
    if (phase !== "resting") return;
    if (restLeft <= 0) {
      setPhase("result");
      return;
    }
    const id = setTimeout(() => setRestLeft((s) => s - 1), 1000);
    return () => clearTimeout(id);
  }, [phase, restLeft]);

  // move keyboard focus to the main button whenever the phase changes
  useEffect(() => {
    if (stage === "trials") primaryRef.current?.focus({ preventScroll: true });
  }, [phase, index, stage]);

  // ---------- one trial ----------
  async function recordSimulated(s: Step, stale: () => boolean): Promise<string[]> {
    const lines = makeLines(s.hand, s.test, s.seconds);
    const parsed = lines.map(parseLine);
    const start = performance.now();
    let i = 0;
    while (i < lines.length) {
      if (stale()) return [];
      const elapsed = performance.now() - start;
      while (i < lines.length && parsed[i]!.t <= elapsed) {
        pointsRef.current.push({ t: parsed[i]!.t, f: parsed[i]!.f });
        i++;
      }
      queueFrame(Math.max(0, s.seconds - elapsed / 1000));
      await sleep(16);
    }
    return lines;
  }

  async function recordDevice(s: Step, stale: () => boolean): Promise<string[]> {
    if (!device || !device.connected) throw new TrialError("The device is not connected. Connect it again to continue.");
    let first: number | null = null;
    const started = performance.now();
    const lines = await device.record(
      s.seconds,
      (line) => {
        const p = parseLine(line);
        if (!p) return;
        if (first === null) first = p.t;
        pointsRef.current.push({ t: p.t - first, f: p.f });
        queueFrame(Math.max(0, s.seconds - (performance.now() - started) / 1000));
      },
      stale,
    );
    return lines;
  }

  async function runTrial() {
    if (!step) return;
    const my = ++runId.current;
    const stale = () => runId.current !== my;
    setError("");
    pointsRef.current = [];
    setLive({ force: 0, peak: 0, left: step.seconds });
    setTick((t) => t + 1);
    setPhase("countdown");
    for (const n of [3, 2, 1]) {
      setCount(n);
      cueCountdown(soundRef.current);
      await sleep(1000);
      if (stale()) return;
    }
    setCount("go");
    cueGo(soundRef.current);
    setTimeout(() => setCount(null), 700);
    setPhase("recording");
    try {
      const lines = source === "device" ? await recordDevice(step, stale) : await recordSimulated(step, stale);
      if (stale()) return;
      cueDone(soundRef.current);
      setPhase("analysing");
      const { readings, skipped } = linesToReadings(lines);
      const result = scoreTrial(step, readings, skipped);
      setResults((prev) => {
        const next = prev.slice();
        next[index] = result;
        return next;
      });
      setLive((l) => ({ ...l, left: 0 }));
      if (index < plan.length - 1) {
        setRestLeft(restSeconds);
        setPhase("resting");
      } else setPhase("result");
    } catch (err) {
      if (stale()) return;
      setCount(null);
      setError(err instanceof Error ? err.message : String(err));
      setPhase("error");
    }
  }

  function nextTrial() {
    pointsRef.current = [];
    setLive({ force: 0, peak: 0, left: plan[index + 1].seconds });
    setIndex((i) => i + 1);
    setPhase("ready");
  }

  function repeatTrial() {
    pointsRef.current = [];
    setResults((prev) => {
      const next = prev.slice();
      next[index] = undefined;
      return next;
    });
    setLive({ force: 0, peak: 0, left: step.seconds });
    setTick((t) => t + 1);
    setRestLeft(0);
    setPhase("ready");
  }

  function finish() {
    if (!participant) return;
    setStage("saving");
    const session: Session = {
      id: newSessionId(),
      created: new Date().toISOString(),
      source,
      calibration: calibrationFor(source, device?.calibration ?? null),
      participant,
      trials: results as TrialResult[],
    };
    const saved = saveSession(session);
    navigate(`/results/${session.id}`, { state: { session, saved } });
  }

  function abandon() {
    if (!window.confirm("Stop this test? Trials recorded so far will be discarded.")) return;
    runId.current++;
    setStage("setup");
    setPlan([]);
    setResults([]);
    setIndex(0);
    setPhase("ready");
    setCount(null);
    pointsRef.current = [];
  }

  // ---------- forms ----------
  function submitParticipant(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const fd = new FormData(e.currentTarget);
    const values = Object.fromEntries([...fd.entries()].map(([k, v]) => [k, String(v)]));
    try {
      const p = readParticipant({ ...values, injury: fd.has("injury") });
      setParticipant(p);
      setPlan(buildPlan(p.dominant));
      setResults([]);
      setIndex(0);
      setPhase("ready");
      setStage(source === "device" ? "zero" : "trials");
    } catch (err) {
      setFormError((err as Error).message);
    }
  }

  async function zeroDevice(advanceToTrials = true) {
    if (!device) return;
    setZeroing(true);
    setError("");
    try {
      await device.tare();
      if (advanceToTrials) setStage("trials");
    } catch (err) {
      setError((err as Error).message);
    } finally {
      setZeroing(false);
    }
  }

  // Enter or Space presses the main button during the trials (like the terminal version)
  useEffect(() => {
    if (stage !== "trials") return;
    const onKey = (e: KeyboardEvent) => {
      const tag = (e.target as HTMLElement).tagName;
      if (tag === "BUTTON" || tag === "A" || tag === "INPUT" || tag === "TEXTAREA") return;
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        primaryRef.current?.click();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [stage]);

  // ======================================================================== render

  if (stage === "saving") {
    return (
      <div className="container">
        <div className="card card-pad center-card">
          <div className="spinner" aria-hidden="true" />
          <h2>Building your report</h2>
          <p className="muted">Comparing your results with the normative data.</p>
        </div>
      </div>
    );
  }

  const calibrationBanner = showCalibrationBanner && (
    <div className="notice warn" role="note">
      <IconWarn />
      <div>
        <b>Estimated calibration.</b> {CALIBRATION_NOTE}
      </div>
    </div>
  );

  if (stage === "setup") {
    const supported = serialSupported();
    const liveVal = liveKg !== null ? Math.max(0, liveKg) : 0;
    return (
      <div className="container test-shell">
        <div className="page-head" style={{ paddingBottom: 8 }}>
          <span className="eyebrow">Grip test · about 4 minutes</span>
          <h1>Set up the test</h1>
          <p className="lead">
            Six short maximal squeezes, three per hand, then one 30-second hold. Choose where the force comes from.
          </p>
        </div>
        <div className="setup-grid">
          <div className={`card source-card${source === "device" ? " selected" : ""}`} onClick={() => setSource("device")}>
            <label className="source-pick">
              <input type="radio" name="source" checked={source === "device"} onChange={() => setSource("device")} />
              <h3>
                <IconUsb /> GripCheck dynamometer
              </h3>
            </label>
            <p>Plug the device in by USB. The browser reads it directly: nothing to install.</p>
            <ul>
              <li>Chrome or Edge on a computer</li>
              <li>Close the Arduino Serial Monitor first</li>
              <li>60 s rest between squeezes</li>
            </ul>
            {!supported && (
              <div className="notice warn">
                <IconWarn />
                <div>This browser cannot talk to USB devices. Open this page in Chrome or Edge on a computer.</div>
              </div>
            )}
            {supported && status !== "connected" && (
              <button
                type="button"
                className="btn btn-secondary"
                disabled={status === "connecting"}
                onClick={(e) => {
                  e.stopPropagation();
                  setSource("device");
                  void connect();
                }}
              >
                <IconUsb size={18} /> {status === "connecting" ? "Connecting…" : "Connect device"}
              </button>
            )}
            {status === "connected" && (
              <div style={{ display: "grid", gap: 8 }}>
                <div className="live-meter">
                  <span className="tag ok">
                    <IconCheck size={14} /> Connected
                  </span>
                  <span className="num">{liveKg !== null ? formatForce(liveKg, unit) : "n/a"}</span>
                  <span className="muted small">{unit} · squeeze to check it responds</span>
                </div>
                <div className="meter-bar" aria-hidden="true">
                  <i style={{ width: `${Math.min(100, (liveVal / 50) * 100)}%` }} />
                </div>
                <DirectionCheck
                  negative={negative}
                  reversed={reversed}
                  onReverse={setReversed}
                  onZero={() => void zeroDevice(false)}
                  zeroing={zeroing}
                />
              </div>
            )}
            {message && status !== "connected" && (
              <p className={status === "error" ? "error-text" : "muted small"} aria-live="polite">
                {message}
              </p>
            )}
          </div>

          <div className={`card source-card${source === "simulated" ? " selected" : ""}`} onClick={() => setSource("simulated")}>
            <label className="source-pick">
              <input type="radio" name="source" checked={source === "simulated"} onChange={() => setSource("simulated")} />
              <h3>
                <IconWave /> Simulated squeezes
              </h3>
            </label>
            <p>No device? Each squeeze is generated from a realistic force curve, so you can try the whole test.</p>
            <ul>
              <li>Works on any browser, including phones</li>
              <li>About 1 in 5 squeezes has a fault, to show the quality check</li>
              <li>3 s rest between squeezes</li>
            </ul>
          </div>
        </div>
        {source === "device" && calibrationBanner}
        <div className="btn-row">
          <button
            className="btn btn-primary btn-lg"
            disabled={source === "device" && status !== "connected"}
            onClick={() => {
              setFormError("");
              setStage("participant");
            }}
          >
            Continue <IconArrow />
          </button>
          {source === "device" && status !== "connected" && <span className="muted small">Connect the device to continue.</span>}
        </div>
      </div>
    );
  }

  if (stage === "participant") {
    return (
      <div className="container test-shell narrow">
        <div className="page-head" style={{ paddingBottom: 8 }}>
          <span className="eyebrow">Step 1 of 3</span>
          <h1>About the participant</h1>
          <p className="lead">Age and sex choose the comparison group. Everything stays in this browser.</p>
        </div>
        {source === "simulated" && (
          <div className="notice">
            <IconInfo />
            <div>Simulated mode: the curves are generated, so any values here are only for trying the app.</div>
          </div>
        )}
        <form className="card card-pad form" onSubmit={submitParticipant} onInput={() => setFormError("")} noValidate>
          <div className="form-grid">
            <label className="field">
              <span>
                Participant ID <span className="opt">optional</span>
              </span>
              <input className="input" name="participant_id" maxLength={40} autoComplete="off" placeholder="e.g. P01" defaultValue={participant?.participant_id} />
              <span className="hint">A code, not a name.</span>
            </label>
            <label className="field">
              <span>Age</span>
              <input className="input num" name="age" type="number" inputMode="numeric" min={5} max={100} required placeholder="5–100" autoFocus defaultValue={participant?.age} />
            </label>
          </div>
          <div className="form-grid">
            <fieldset className="field">
              <legend>Sex</legend>
              <div className="segmented">
                {(["female", "male"] as const).map((v) => (
                  <label key={v}>
                    <input type="radio" name="sex" value={v} defaultChecked={participant?.sex === v} />
                    <span>{cap(v)}</span>
                  </label>
                ))}
              </div>
              <span className="hint">The normative data are reported by sex.</span>
            </fieldset>
            <fieldset className="field">
              <legend>Dominant hand</legend>
              <div className="segmented">
                {(["right", "left"] as const).map((v) => (
                  <label key={v}>
                    <input type="radio" name="dominant" value={v} defaultChecked={(participant?.dominant ?? "right") === v} />
                    <span>{cap(v)}</span>
                  </label>
                ))}
              </div>
            </fieldset>
          </div>
          <div className="form-grid">
            <label className="field">
              <span>
                Height <span className="opt">cm, optional</span>
              </span>
              <input className="input num" name="height_cm" type="number" inputMode="decimal" min={100} max={230} placeholder="e.g. 175" defaultValue={participant?.height_cm ?? undefined} />
            </label>
            <label className="field">
              <span>
                Weight <span className="opt">kg, optional</span>
              </span>
              <input className="input num" name="weight_kg" type="number" inputMode="decimal" min={20} max={250} placeholder="e.g. 70" defaultValue={participant?.weight_kg ?? undefined} />
            </label>
          </div>
          <label className="check">
            <input type="checkbox" name="injury" defaultChecked={participant?.injury} />
            <span>Pain or injury in either hand, wrist or elbow in the last six months</span>
          </label>
          {formError && (
            <p className="error-text" role="alert">
              {formError}
            </p>
          )}
          <div className="btn-row">
            <button className="btn btn-primary btn-lg" type="submit">
              Continue <IconArrow />
            </button>
            <button className="btn btn-ghost" type="button" onClick={() => setStage("setup")}>
              Back
            </button>
          </div>
        </form>
      </div>
    );
  }

  if (stage === "zero") {
    const liveVal = liveKg !== null ? Math.max(0, liveKg) : 0;
    return (
      <div className="container test-shell narrow">
        <div className="page-head" style={{ paddingBottom: 8 }}>
          <span className="eyebrow">Step 2 of 3</span>
          <h1>Zero the device</h1>
          <p className="lead">Put the dynamometer on the table and let go of it completely. Nothing may touch the handle while it zeroes.</p>
        </div>
        <div className="card card-pad" style={{ display: "grid", gap: 18 }}>
          <div style={{ display: "grid", gap: 8 }}>
            <div className="live-meter">
              <span className="muted small">Reading now</span>
              <span className="num">{device && liveKg !== null ? formatForce(liveKg, unit) : "–"}</span>
              <span className="muted small">{unit}</span>
            </div>
            <div className="meter-bar" aria-hidden="true">
              <i style={{ width: `${Math.min(100, (liveVal / 50) * 100)}%` }} />
            </div>
          </div>
          {!device && (
            <div className="notice bad">
              <IconWarn />
              <div>
                The device is not connected.{" "}
                <button className="btn btn-sm btn-secondary" onClick={() => void connect()}>
                  Reconnect
                </button>
              </div>
            </div>
          )}
          {error && (
            <p className="error-text" role="alert">
              {error}
            </p>
          )}
          {device && <DirectionCheck negative={negative} reversed={reversed} onReverse={setReversed} />}
          {calibrationBanner}
          <div className="btn-row">
            <button className="btn btn-primary btn-lg" disabled={!device || zeroing} onClick={() => void zeroDevice(true)}>
              {zeroing ? "Zeroing… hands off" : "Zero now"}
            </button>
            <button className="btn btn-ghost" onClick={() => setStage("participant")}>
              Back
            </button>
          </div>
        </div>
      </div>
    );
  }

  // ---------- trials ----------
  const result = results[index];
  const isLast = index === plan.length - 1;
  const ghosts: Pt[][] = plan
    .map((s, i) => ({ s, r: results[i] }))
    .filter(({ s, r }, i) => i !== index && r && s.hand === step.hand && s.test === step.test)
    .map(({ r }) => r!.readings.map((x) => ({ t: x.time_ms, f: x.force_kg })));
  const busy = phase === "countdown" || phase === "recording" || phase === "analysing";
  const flagged = result?.quality && result.quality !== "good";

  let primary: { text: string; onClick: () => void; disabled?: boolean };
  if (phase === "ready") primary = { text: "I’m ready", onClick: runTrial };
  else if (phase === "error") primary = { text: "Try again", onClick: runTrial, disabled: source === "device" && !device };
  else if (busy) primary = { text: phase === "analysing" ? "Analysing…" : "Recording…", onClick: () => {}, disabled: true };
  else if (isLast) primary = { text: "See my report", onClick: finish };
  else if (phase === "resting") primary = { text: `Resting… ${restLeft}s`, onClick: () => {}, disabled: true };
  else {
    const n = plan[index + 1];
    primary = { text: n.test === "fatigue" ? "Start the 30 s hold" : `Next: ${n.hand} hand`, onClick: nextTrial };
  }

  return (
    <div className="container test-shell">
      <div className="test-toolbar">
        <ol className="stepper" aria-label="Test progress">
          {plan.map((s, i) => {
            const r = results[i];
            const state = i === index ? "current" : r ? (r.quality && r.quality !== "good" ? "flag" : "done") : "";
            const fill = i === index && phase === "recording" ? `${(1 - live.left / s.seconds) * 100}%` : undefined;
            return (
              <li key={i} className={state} aria-current={i === index ? "step" : undefined}>
                <span className="bar">
                  <i style={fill ? { width: fill } : r && i === index ? { width: "100%", background: "var(--ok)" } : undefined} />
                </span>
                <span className="lbl">
                  {stepLabel(s)}
                  {r ? ` · ${formatForce(r.metrics.peak_kg, unit)}` : ""}
                </span>
              </li>
            );
          })}
        </ol>
        <div className="btn-row" style={{ flex: "none" }}>
          <div className="pill-tabs" role="group" aria-label="Force display unit">
            {(["kg", "lb"] as ForceUnit[]).map((u) => (
              <button key={u} type="button" className={`pill-tab${unit === u ? " active" : ""}`} onClick={() => changeUnit(u)}>
                {u}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="btn btn-secondary btn-sm"
            onClick={toggleSound}
            aria-pressed={soundOn}
            title={soundOn ? "Mute countdown chimes" : "Enable countdown chimes"}
          >
            {soundOn ? <IconVolume size={16} /> : <IconVolumeOff size={16} />}
            <span className="hide-sm">{soundOn ? "Sound on" : "Muted"}</span>
          </button>
        </div>
      </div>

      <div className="trial-layout">
        <section className="card chart-card" aria-labelledby="trial-title">
          <div className="chart-top">
            <div style={{ display: "grid", gap: 6 }}>
              <span className="eyebrow">
                {step.test === "fatigue" ? "Fatigue test" : `Maximal grip · trial ${step.trial} of 3`}
              </span>
              <h2 id="trial-title">{step.test === "fatigue" ? "Squeeze and hold for 30 seconds" : "Squeeze as hard as you can"}</h2>
            </div>
            <span className="tag" style={{ fontSize: "0.9rem", padding: "6px 12px" }}>
              <span className={`hand-dot ${step.test === "fatigue" ? "fatigue" : step.hand}`} /> {cap(step.hand)} hand
            </span>
          </div>
          <div className="chart-area">
            <LiveChart
              points={pointsRef.current}
              tick={tick}
              seconds={step.seconds}
              colorVar={colorVarFor(step)}
              ghosts={ghosts}
              unit={unit}
              label={
                result
                  ? `Force over time. Peak ${result.metrics.peak_kg.toFixed(1)} kg after ${result.metrics.time_to_peak_ms} ms.`
                  : "Force over time. The graph fills in while you squeeze."
              }
            />
            {count !== null && (
              <div className={`countdown${count === "go" ? " go" : ""}`} aria-live="assertive">
                <span key={String(count)}>{count === "go" ? "Squeeze!" : count}</span>
              </div>
            )}
          </div>
        </section>

        <aside className="side">
          <div className="readouts" aria-live="off">
            <div className="readout wide">
              <span className="label">Force</span>
              <span className="value">
                {formatForce(live.force, unit)}
                <small>{unit}</small>
              </span>
            </div>
            <div className="readout">
              <span className="label">Peak</span>
              <span className="value">
                {formatForce(live.peak, unit)}
                <small>{unit}</small>
              </span>
            </div>
            <div className="readout">
              <span className="label">Time left</span>
              <span className="value">
                {Math.ceil(live.left)}
                <small>s</small>
              </span>
            </div>
          </div>

          <div className="card panel">
            {(phase === "ready" || phase === "error") && (
              <>
                <ul className="posture" aria-label="Posture">
                  {PROMPT_POSTURE.map((p) => (
                    <li key={p}>{p}</li>
                  ))}
                </ul>
                <p className="muted small">
                  {step.test === "fatigue"
                    ? "Squeeze as hard as you can and keep squeezing until the timer ends."
                    : "After the 3-2-1, squeeze as hard as you can until the timer ends."}
                </p>
              </>
            )}
            {(phase === "countdown" || phase === "recording") && (
              <p className="go-text" aria-live="polite">
                {phase === "countdown" ? "Get ready…" : step.test === "fatigue" ? PROMPT_FATIGUE : PROMPT_GO}
              </p>
            )}
            {source === "device" && device && !busy && (
              <DirectionCheck
                negative={negative}
                reversed={reversed}
                onReverse={setReversed}
                onZero={() => void zeroDevice(false)}
                zeroing={zeroing}
              />
            )}
            {phase === "error" && (
              <div className="notice bad" role="alert">
                <IconWarn />
                <div>{error}</div>
              </div>
            )}
            {phase === "error" && source === "device" && !device && (
              <button className="btn btn-secondary" onClick={() => void connect()}>
                Reconnect device
              </button>
            )}
            {result && (phase === "result" || phase === "resting") && (
              <>
                <div className="result-chips">
                  <div>
                    <span>Peak (filtered)</span>
                    <b>
                      {formatForce(result.metrics.peak_kg, unit)} {unit}
                    </b>
                  </div>
                  <div>
                    <span>Time to peak</span>
                    <b>{result.metrics.time_to_peak_ms} ms</b>
                  </div>
                  <div>
                    <span>RFD</span>
                    <b>{fmt(result.metrics.rfd_n_per_s, 0)} N/s</b>
                  </div>
                  {step.test === "fatigue" ? (
                    <div>
                      <span>Fatigue index</span>
                      <b>{fmt(result.metrics.fatigue_index_pct)} %</b>
                    </div>
                  ) : (
                    <div>
                      <span>Samples/s</span>
                      <b>{Math.round(result.rate_hz)}</b>
                    </div>
                  )}
                </div>
                {result.quality && (
                  <div className={`notice ${flagged ? "warn" : "ok"}`}>
                    {flagged ? <IconWarn /> : <IconCheck />}
                    <div>
                      <b>{QUALITY_TEXT[result.quality].title}.</b> {QUALITY_TEXT[result.quality].why}
                      {flagged && " You can repeat this trial now or after resting."}
                    </div>
                  </div>
                )}
                {result.notes.map((n) => (
                  <div className="notice" key={n}>
                    <IconInfo />
                    <div>{n}</div>
                  </div>
                ))}
              </>
            )}
            {phase === "resting" && (
              <div className="rest-ring">
                <RestRing left={restLeft} total={restSeconds} />
                <div>
                  <b>Rest</b>
                  <p className="muted small">Relax your hand. The next squeeze unlocks when the timer ends.</p>
                </div>
              </div>
            )}

            <div className="btn-row">
              <button ref={primaryRef} className="btn btn-primary btn-lg" style={{ flex: 1 }} onClick={primary.onClick} disabled={primary.disabled}>
                {primary.text}
              </button>
            </div>
            <div className="btn-row">
              {phase === "resting" && (
                <button className="btn btn-ghost btn-sm" onClick={() => setRestLeft(0)}>
                  Skip rest
                </button>
              )}
              {result && (phase === "result" || phase === "resting") && (
                <button className={`btn btn-sm ${flagged ? "btn-secondary" : "btn-ghost"}`} onClick={repeatTrial}>
                  Repeat this trial
                </button>
              )}
              {source === "device" && device && phase === "ready" && (
                <button
                  type="button"
                  className="btn btn-ghost btn-sm"
                  disabled={zeroing}
                  onClick={() => void zeroDevice(false)}
                  title="Put the dynamometer down, hands off, then click to re-zero"
                >
                  {zeroing ? "Zeroing…" : "Re-zero"}
                </button>
              )}
              {!busy && (
                <button className="btn btn-ghost btn-sm" onClick={abandon} style={{ marginLeft: "auto" }}>
                  Stop test
                </button>
              )}
            </div>
          </div>
          {calibrationBanner}
          <p className="muted small">
            Tip: press <span className="kbd">Enter</span> or <span className="kbd">Space</span> for the main button.{" "}
            <Link to="/how-it-works#protocol">Why this protocol?</Link>
          </p>
        </aside>
      </div>
    </div>
  );
}

function RestRing({ left, total }: { left: number; total: number }) {
  const r = 22;
  const c = 2 * Math.PI * r;
  const frac = total > 0 ? Math.max(0, left) / total : 0;
  return (
    <svg width="56" height="56" viewBox="0 0 56 56" aria-label={`${left} seconds of rest left`} role="img">
      <circle cx="28" cy="28" r={r} fill="none" stroke="var(--rule)" strokeWidth="5" />
      <circle
        cx="28"
        cy="28"
        r={r}
        fill="none"
        stroke="var(--accent)"
        strokeWidth="5"
        strokeDasharray={c}
        strokeDashoffset={c * (1 - frac)}
        strokeLinecap="round"
        transform="rotate(-90 28 28)"
        style={{ transition: "stroke-dashoffset 1s linear" }}
      />
      <text x="28" y="33" textAnchor="middle" fontFamily="var(--mono)" fontSize="15" fill="var(--ink)">
        {left}
      </text>
    </svg>
  );
}

// Calibrate page: zero, hang weighed masses, check on one more, then write counts-per-kg into the device (firmware v1.1).

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import { Link } from "react-router-dom";
import { useDevice } from "../components/DeviceContext";
import { IconCheck, IconInfo, IconUsb, IconWarn } from "../components/Icons";
import { REPO_URL } from "../components/Layout";
import {
  calibrationCsv,
  checkWeight,
  dateStamp,
  DATASHEET_COUNTS_PER_KG,
  fitCalibration,
  isSteady,
  plausibility,
  stats,
  toKg,
  type CalPoint,
} from "../lib/calibration";
import type { GripDevice } from "../lib/device";
import { serialSupported } from "../lib/device";
import { download } from "../lib/exporters";
import { parseFirmwareLine } from "../lib/parse";

type Step = "connect" | "direction" | "zero" | "weights" | "check" | "save";
const STEPS: { id: Step; label: string }[] = [
  { id: "connect", label: "Connect" },
  { id: "direction", label: "Direction" },
  { id: "zero", label: "Zero" },
  { id: "weights", label: "Weights" },
  { id: "check", label: "Check" },
  { id: "save", label: "Save" },
];

/** A squeeze or a hung weight clearly above the noise (bench noise is about ±70 counts). */
const CLEAR_SIGNAL = 5000;
const CAPTURE_SAMPLES = 30; // 3 s at 10 samples/s

type Captured = CalPoint & { label: string; samples: number[] };

const sleep = (ms: number) => new Promise((r) => setTimeout(r, ms));
const fmt = (x: number, d = 0) => x.toLocaleString("en-US", { minimumFractionDigits: d, maximumFractionDigits: d });

/** Net counts exactly as the device sends them (before any browser-side reverse), refreshed 5 times a second. */
function useRawNet(device: GripDevice | null) {
  const buf = useRef<number[]>([]);
  const [, setTick] = useState(0);
  useEffect(() => {
    buf.current = [];
    if (!device) return;
    const stop = device.subscribeRaw((line) => {
      const p = parseFirmwareLine(line);
      if (!p) return;
      buf.current.push(p.net);
      if (buf.current.length > 400) buf.current.splice(0, buf.current.length - 400);
    });
    const id = setInterval(() => setTick((t) => t + 1), 200);
    return () => {
      stop();
      clearInterval(id);
    };
  }, [device]);
  const values = buf.current;
  const latest = values.length ? values[values.length - 1] : null;
  return { buf, latest, steady: isSteady(values) };
}

async function collect(buf: React.MutableRefObject<number[]>, n: number, timeoutMs = 8000): Promise<number[]> {
  const t0 = performance.now();
  while (buf.current.length < n) {
    if (performance.now() - t0 > timeoutMs) throw new Error("No readings arrived. Check the USB cable.");
    await sleep(100);
  }
  return buf.current.slice(-n);
}

export default function CalibratePage() {
  const { device, status, message, connect, setReversed } = useDevice();
  const { buf, latest, steady } = useRawNet(device);

  const [step, setStep] = useState<Step>("connect");
  const [support, setSupport] = useState<"unknown" | "checking" | "yes" | "no">("unknown");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");

  const [dirSeen, setDirSeen] = useState<"none" | "positive" | "negative">("none");
  const [zero, setZero] = useState<{ net: number; sd: number; samples: number[] } | null>(null);
  const [points, setPoints] = useState<Captured[]>([]);
  const [check, setCheck] = useState<Captured | null>(null);
  const [massText, setMassText] = useState("");
  const [unit, setUnit] = useState<"kg" | "lb">("kg");
  const [confirmUnusual, setConfirmUnusual] = useState(false);
  const [saved, setSaved] = useState<{ cpk: number; on: string } | null>(null);
  const previousCpk = useRef<number | null>(null);

  // ---- firmware support (v1.1 answers "I" with its settings)
  useEffect(() => {
    if (!device) {
      setSupport("unknown");
      setStep("connect");
      return;
    }
    let live = true;
    setSupport("checking");
    void device.requestInfo().then((ok) => {
      if (!live) return;
      setSupport(ok ? "yes" : "no");
      if (ok) previousCpk.current = device.info.countsPerKg;
    });
    return () => {
      live = false;
    };
  }, [device]);

  // ---- direction: watch for a clear squeeze either way
  useEffect(() => {
    if (step !== "direction" || latest === null) return;
    if (latest > CLEAR_SIGNAL) setDirSeen("positive");
    else if (latest < -CLEAR_SIGNAL) setDirSeen("negative");
  }, [latest, step]);

  const run = useCallback(async (fn: () => Promise<void>) => {
    setBusy(true);
    setError("");
    try {
      await fn();
    } catch (e) {
      setError((e as Error).message);
    } finally {
      setBusy(false);
    }
  }, []);

  const fixDirection = () =>
    run(async () => {
      if (!device) return;
      const current = device.info.sign ?? 1;
      const res = await device.saveSign(current === 1 ? -1 : 1);
      if (!res.ok) throw new Error(res.reply ?? "The device did not confirm the change. Reconnect and try again.");
      setReversed(false); // the device is right now, so the browser must not flip it a second time
      buf.current = [];
      setDirSeen("none");
    });

  const doZero = () =>
    run(async () => {
      if (!device) return;
      await device.tare();
      buf.current = [];
      const samples = await collect(buf, CAPTURE_SAMPLES);
      const s = stats(samples);
      setZero({ net: s.mean, sd: s.sd, samples });
    });

  const massKg = useMemo(() => {
    const v = Number(massText.replace(",", "."));
    return Number.isFinite(v) && v > 0 ? toKg(v, unit) : null;
  }, [massText, unit]);

  const captureReady = massKg !== null && massKg >= 0.5 && steady && latest !== null && latest - (zero?.net ?? 0) > CLEAR_SIGNAL;

  const capture = (asCheck: boolean) =>
    run(async () => {
      if (massKg === null) return;
      const samples = buf.current.slice(-CAPTURE_SAMPLES);
      const label = `${massText} ${unit}`;
      const pt: Captured = { massKg, net: stats(samples).mean, samples, label };
      if (asCheck) setCheck(pt);
      else setPoints((p) => [...p, pt]);
      setMassText("");
    });

  const fit = useMemo(() => {
    if (!zero || points.length === 0) return null;
    try {
      return fitCalibration([{ massKg: 0, net: zero.net }, ...points]);
    } catch {
      return null;
    }
  }, [zero, points]);
  const checkResult = fit && check ? checkWeight(fit, check) : null;
  const plaus = fit ? plausibility(fit.countsPerKg) : null;

  const save = () =>
    run(async () => {
      if (!device || !fit) return;
      const stamp = dateStamp();
      const res = await device.saveCalibration(fit.countsPerKg, stamp);
      if (!res.ok) throw new Error(res.reply?.replace(/^#\s*/, "") ?? "The device did not confirm. Reconnect and try again.");
      setSaved({ cpk: fit.countsPerKg, on: `${stamp.slice(0, 4)}-${stamp.slice(4, 6)}-${stamp.slice(6)}` });
    });

  const downloadRecord = () => {
    if (!fit || !zero) return;
    const csv = calibrationCsv({
      date: new Date(),
      firmware: device?.info.firmware ?? null,
      previousCountsPerKg: previousCpk.current,
      fit,
      points: [{ massKg: 0, net: zero.net, label: "zero", samples: zero.samples }, ...points],
      check: check && checkResult ? { ...check, predictedKg: checkResult.predictedKg, errorPct: checkResult.errorPct } : null,
      noiseSd: zero.sd,
      savedToDevice: saved !== null,
    });
    download(`gripcheck_calibration_${dateStamp()}.csv`, csv);
  };

  const restart = () => {
    setZero(null);
    setPoints([]);
    setCheck(null);
    setSaved(null);
    setConfirmUnusual(false);
    setDirSeen("none");
    setError("");
    setStep(device ? "direction" : "connect");
  };

  const stepIndex = STEPS.findIndex((s) => s.id === step);
  const net = latest;
  const netAboveZero = net !== null ? net - (zero?.net ?? 0) : null;

  const liveBox = (hint: string) => (
    <div className="calib-live">
      <div>
        <span className="muted small">Live reading</span>
        <div className="num">{net === null ? "—" : fmt(net)}</div>
        <span className="muted small">counts · {hint}</span>
      </div>
      <span className={`tag ${steady ? "ok" : ""}`}>{steady ? "Steady" : "Settling…"}</span>
    </div>
  );

  const massInput = (id: string) => (
    <div className="calib-mass">
      <label className="field" htmlFor={id}>
        <span>Weight on the strap, hanger included</span>
        <input
          id={id}
          className="input num"
          inputMode="decimal"
          placeholder={unit === "kg" ? "e.g. 11.32" : "e.g. 25"}
          value={massText}
          onChange={(e) => setMassText(e.target.value)}
        />
      </label>
      <div className="pill-tabs" role="group" aria-label="Weight unit">
        {(["kg", "lb"] as const).map((u) => (
          <button key={u} type="button" className={`pill-tab${unit === u ? " active" : ""}`} onClick={() => setUnit(u)}>
            {u}
          </button>
        ))}
      </div>
    </div>
  );

  return (
    <div className="container test-shell narrow">
      <div className="page-head" style={{ paddingBottom: 8 }}>
        <span className="eyebrow">Calibrate · about 10 minutes</span>
        <h1>Calibrate the dynamometer</h1>
        <p className="lead">
          Hang a few weighed masses from the finger bar. GripCheck works out how many counts one kilogram makes and saves that number in the device,
          so every test after this reports measured kilograms.
        </p>
      </div>

      <ol className="stepper" aria-label="Calibration progress" style={{ marginBottom: 20 }}>
        {STEPS.map((s, i) => (
          <li key={s.id} className={i < stepIndex || saved ? "done" : i === stepIndex ? "current" : ""} aria-current={i === stepIndex ? "step" : undefined}>
            <span className="bar">
              <i style={i < stepIndex || saved ? { width: "100%", background: "var(--ok)" } : undefined} />
            </span>
            <span className="lbl">
              {i + 1}. {s.label}
            </span>
          </li>
        ))}
      </ol>

      {error && (
        <div className="notice bad" role="alert" style={{ marginBottom: 16 }}>
          <IconWarn />
          <div>{error}</div>
        </div>
      )}

      {/* ---------------- 1. connect */}
      {step === "connect" && (
        <div className="card card-pad calib-step">
          <h2>Connect the device</h2>
          {!serialSupported() ? (
            <div className="notice warn">
              <IconWarn />
              <div>This browser cannot talk to USB devices. Open this page in Chrome or Edge on a computer.</div>
            </div>
          ) : status !== "connected" ? (
            <>
              <p>Plug the dynamometer in by USB and close the Arduino Serial Monitor.</p>
              <button type="button" className="btn btn-primary btn-lg" disabled={status === "connecting"} onClick={() => void connect()}>
                <IconUsb size={18} /> {status === "connecting" ? "Connecting…" : "Connect device"}
              </button>
              {message && <p className={status === "error" ? "error-text" : "muted small"}>{message}</p>}
            </>
          ) : support === "checking" || support === "unknown" ? (
            <p className="muted">Asking the device for its settings…</p>
          ) : support === "no" ? (
            <div className="notice warn">
              <IconWarn />
              <div>
                <b>This device runs older firmware that cannot store a calibration.</b> Upload{" "}
                <a href={`${REPO_URL}/blob/main/firmware/grip_firmware_tillaart/grip_firmware_tillaart.ino`} target="_blank" rel="noreferrer">
                  grip_firmware_tillaart.ino
                </a>{" "}
                (v1.1) with the Arduino IDE, close the IDE, then reload this page and connect again.
              </div>
            </div>
          ) : (
            <>
              <dl className="calib-facts">
                <dt>Firmware</dt>
                <dd>v{device?.info.firmware ?? "?"}</dd>
                <dt>Counts per kg now</dt>
                <dd>
                  {device?.info.countsPerKg !== null && device?.info.countsPerKg !== undefined ? fmt(device.info.countsPerKg, 1) : "?"}{" "}
                  <span className={`tag ${device?.info.calibration === "measured" ? "ok" : ""}`}>
                    {device?.info.calibration === "measured" ? `measured${device.info.calibratedOn ? ` ${device.info.calibratedOn}` : ""}` : "datasheet estimate"}
                  </span>
                </dd>
              </dl>
              <p className="muted small">You need: 2–4 weights you have weighed on a scale (hanger included), a strap, and somewhere to hang them.</p>
              <button type="button" className="btn btn-primary btn-lg" onClick={() => setStep("direction")}>
                Start
              </button>
            </>
          )}
        </div>
      )}

      {/* ---------------- 2. direction */}
      {step === "direction" && (
        <div className="card card-pad calib-step">
          <h2>Squeeze the handles</h2>
          <p>Give the handles one firm squeeze and let go. The reading must go up.</p>
          {liveBox("goes up when you squeeze")}
          {dirSeen === "positive" && (
            <div className="notice ok">
              <IconCheck />
              <div>Direction is right.</div>
            </div>
          )}
          {dirSeen === "negative" && (
            <div className="notice warn">
              <IconWarn />
              <div>
                It went <b>down</b>: the load cell sits the other way round in this frame. Fix it on the device (no re-upload needed), then squeeze
                again.
                <div className="btn-row" style={{ marginTop: 8 }}>
                  <button type="button" className="btn btn-secondary" disabled={busy} onClick={() => void fixDirection()}>
                    {busy ? "Saving…" : "Fix direction on the device"}
                  </button>
                </div>
              </div>
            </div>
          )}
          <div className="btn-row">
            <button
              type="button"
              className="btn btn-primary btn-lg"
              disabled={dirSeen !== "positive"}
              onClick={() => {
                setReversed(false);
                setStep("zero");
              }}
            >
              Next
            </button>
          </div>
        </div>
      )}

      {/* ---------------- 3. zero */}
      {step === "zero" && (
        <div className="card card-pad calib-step">
          <h2>Set up and zero</h2>
          <ol className="calib-list">
            <li>Turn the device so the palm bar points down and rest the frame on two blocks (do not clamp it).</li>
            <li>Loop a strap over the finger bar. It must touch nothing else.</li>
            <li>Nothing hanging, hands off, then press Zero.</li>
          </ol>
          {liveBox("nothing hanging")}
          {zero && (
            <div className="notice ok">
              <IconCheck />
              <div>
                Zeroed. Noise {fmt(zero.sd)} counts (about {fmt((zero.sd / DATASHEET_COUNTS_PER_KG) * 1000, 1)} g).
              </div>
            </div>
          )}
          <div className="btn-row">
            <button type="button" className={`btn ${zero ? "btn-secondary" : "btn-primary btn-lg"}`} disabled={busy} onClick={() => void doZero()}>
              {busy ? "Zeroing… keep still" : zero ? "Zero again" : "Zero"}
            </button>
            {zero && (
              <button type="button" className="btn btn-primary btn-lg" onClick={() => setStep("weights")}>
                Next
              </button>
            )}
          </div>
        </div>
      )}

      {/* ---------------- 4. weights */}
      {step === "weights" && (
        <div className="card card-pad calib-step">
          <h2>Hang weighed masses</h2>
          <p>
            Type the weight, hang it, wait until it says <b>Steady</b>, then press Capture. Two to four weights spread up to about 30 kg is best;
            one works.
          </p>
          {massInput("calib-mass")}
          {liveBox(netAboveZero !== null && massKg ? `≈ ${fmt(netAboveZero / massKg)} counts per kg` : "hang the weight")}
          <div className="btn-row">
            <button type="button" className="btn btn-primary" disabled={!captureReady || busy} onClick={() => void capture(false)}>
              Capture
            </button>
            {!steady && massKg !== null && <span className="muted small">Wait for Steady: stop the swing and take your hands off.</span>}
          </div>
          {points.length > 0 && (
            <table className="calib-table">
              <thead>
                <tr>
                  <th>Weight</th>
                  <th>kg</th>
                  <th>Counts</th>
                  <th>Counts per kg</th>
                  <th />
                </tr>
              </thead>
              <tbody>
                {points.map((p, i) => (
                  <tr key={i}>
                    <td>{p.label}</td>
                    <td>{fmt(p.massKg, 2)}</td>
                    <td>{fmt(p.net)}</td>
                    <td>{fmt((p.net - (zero?.net ?? 0)) / p.massKg)}</td>
                    <td>
                      <button type="button" className="btn btn-ghost btn-sm" onClick={() => setPoints((ps) => ps.filter((_, j) => j !== i))}>
                        Remove
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
          <div className="btn-row">
            <button type="button" className="btn btn-primary btn-lg" disabled={points.length === 0} onClick={() => setStep("check")}>
              Next
            </button>
          </div>
        </div>
      )}

      {/* ---------------- 5. check */}
      {step === "check" && fit && (
        <div className="card card-pad calib-step">
          <h2>Check on one more weight</h2>
          <p>Hang a weight you did not use above. GripCheck predicts it from the new number; within 2 % passes.</p>
          {massInput("check-mass")}
          {liveBox(netAboveZero !== null ? `reads ${fmt((net! - fit.interceptCounts) / fit.countsPerKg, 2)} kg with the new number` : "hang the weight")}
          <div className="btn-row">
            <button type="button" className="btn btn-primary" disabled={!captureReady || busy} onClick={() => void capture(true)}>
              Capture check weight
            </button>
          </div>
          {check && checkResult && (
            <div className={`notice ${checkResult.pass ? "ok" : "warn"}`}>
              {checkResult.pass ? <IconCheck /> : <IconWarn />}
              <div>
                {fmt(check.massKg, 2)} kg read as {fmt(checkResult.predictedKg, 2)} kg: {checkResult.errorPct >= 0 ? "+" : ""}
                {fmt(checkResult.errorPct, 2)} %. {checkResult.pass ? "Pass." : "More than 2 % off: check the strap touches only the finger bar, and the weights."}
              </div>
            </div>
          )}
          <div className="btn-row">
            <button type="button" className="btn btn-primary btn-lg" onClick={() => setStep("save")}>
              {check ? "Next" : "Skip the check"}
            </button>
          </div>
        </div>
      )}

      {/* ---------------- 6. save */}
      {step === "save" && fit && plaus && (
        <div className="card card-pad calib-step">
          <h2>{saved ? "Saved on the device" : "Save to the device"}</h2>
          <div className="calib-result">
            <span className="muted small">Counts per kg</span>
            <div className="num">{fmt(fit.countsPerKg, 1)}</div>
            <span className="muted small">
              {previousCpk.current ? `was ${fmt(previousCpk.current, 1)} (${fmt(((fit.countsPerKg / previousCpk.current) - 1) * 100, 2)} %)` : ""}
              {" · "}datasheet {fmt(DATASHEET_COUNTS_PER_KG)}
            </span>
          </div>
          <dl className="calib-facts">
            <dt>Points</dt>
            <dd>zero + {points.length} weight{points.length > 1 ? "s" : ""}, up to {fmt(Math.max(...points.map((p) => p.massKg)), 2)} kg</dd>
            {points.length > 1 && (
              <>
                <dt>Largest miss from the line</dt>
                <dd>{fmt(fit.maxResidualKg, 3)} kg</dd>
              </>
            )}
            <dt>Check weight</dt>
            <dd>{checkResult ? `${checkResult.errorPct >= 0 ? "+" : ""}${fmt(checkResult.errorPct, 2)} % ${checkResult.pass ? "(pass)" : "(over 2 %)"}` : "not done"}</dd>
          </dl>

          {plaus === "impossible" && (
            <div className="notice bad">
              <IconWarn />
              <div>This number is far outside what a 100 kg cell can give. Something touched the weight or the strap; start over.</div>
            </div>
          )}
          {plaus === "unusual" && !saved && (
            <div className="notice warn">
              <IconWarn />
              <div>
                More than 30 % from the datasheet. Usually the strap touches the frame or a weight was typed wrong.
                <label style={{ display: "flex", gap: 8, marginTop: 8, alignItems: "center" }}>
                  <input type="checkbox" checked={confirmUnusual} onChange={(e) => setConfirmUnusual(e.target.checked)} /> I checked the strap and the
                  weights; save anyway.
                </label>
              </div>
            </div>
          )}

          {saved ? (
            <>
              <div className="notice ok">
                <IconCheck />
                <div>
                  The device now uses {fmt(saved.cpk, 1)} counts per kg (calibrated {saved.on}) and reports measured kilograms. It keeps the number
                  after unplugging.
                </div>
              </div>
              <div className="calib-live">
                <div>
                  <span className="muted small">Live, with the new number</span>
                  <div className="num">{net === null ? "—" : fmt(net / saved.cpk, 2)}</div>
                  <span className="muted small">kg · hang anything to try it</span>
                </div>
              </div>
            </>
          ) : null}

          <div className="btn-row">
            {!saved && (
              <button
                type="button"
                className="btn btn-primary btn-lg"
                disabled={busy || plaus === "impossible" || (plaus === "unusual" && !confirmUnusual)}
                onClick={() => void save()}
              >
                {busy ? "Saving…" : "Save to device"}
              </button>
            )}
            <button type="button" className="btn btn-secondary" onClick={downloadRecord}>
              Download record (CSV)
            </button>
            {saved && (
              <Link className="btn btn-primary" to="/test">
                Run a grip test
              </Link>
            )}
            <button type="button" className="btn btn-ghost" onClick={restart}>
              Start over
            </button>
          </div>
          <p className="muted small" style={{ marginTop: 12 }}>
            <IconInfo size={14} /> Keep the downloaded record: it holds every reading behind this number.
          </p>
        </div>
      )}
    </div>
  );
}

// Project overview: what GripCheck is, why it exists, what it does, how it is built, and its honest status.

import { lazy, Suspense, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";

const CadViewer = lazy(() => import("../components/CadViewer"));
import {
  IconArrow,
  IconChart,
  IconChip,
  IconClock,
  IconGithub,
  IconRefresh,
  IconShield,
  IconTarget,
  IconUsb,
  IconWave,
} from "../components/Icons";
import { REPO_URL } from "../components/Layout";
import { filterReadings } from "../lib/filters";
import { findPeak, rfdNPerS, timeToPeakMs } from "../lib/metrics";
import { linesToReadings } from "../lib/parse";
import { checkTrial, QUALITY_TEXT } from "../lib/quality";
import { makeLines, type TrialKind } from "../lib/simulator";
import type { Reading } from "../lib/types";

export default function HomePage() {
  return (
    <>
      <Hero />
      <Mission />
      <Capabilities />
      <Device />
      <Software />
      <Status />
      <Team />
      <section className="section-tight">
        <div className="container">
          <div className="cta-band">
            <div>
              <h2>Try the test now</h2>
              <p>No device needed: simulated squeezes run the whole protocol and produce a full report in about two minutes.</p>
            </div>
            <div className="btn-row">
              <Link className="btn btn-primary btn-lg" to="/test">
                Start a grip test <IconArrow />
              </Link>
              <Link className="btn btn-ghost btn-lg" style={{ color: "var(--bg)", borderColor: "color-mix(in oklab, var(--bg) 30%, transparent)" }} to="/results/sample-demo">
                Sample report
              </Link>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}

// ---------------------------------------------------------------- hero

function Hero() {
  return (
    <section className="hero">
      <div className="container">
        <div>
          <span className="eyebrow">Open-source grip dynamometer · v3</span>
          <h1>
            Grip strength, measured as a <em>whole curve</em>, not one number.
          </h1>
          <p className="lead">
            GripCheck is a 3D-printed hand dynamometer built around a 100 kg load cell, and the browser software that runs a standard grip test on
            it: live force, five force-time metrics, an automatic trial check and a comparison with published norms.
          </p>
          <div className="btn-row">
            <Link className="btn btn-primary btn-lg" to="/test">
              Start a grip test <IconArrow />
            </Link>
            <Link className="btn btn-secondary btn-lg" to="/results/sample-demo">
              View sample report
            </Link>
            <Link className="btn btn-ghost btn-lg" to="/how-it-works">
              How it works
            </Link>
          </div>
          <div className="hero-meta">
            <span>
              <IconUsb size={16} /> Plug in by USB, runs in Chrome or Edge
            </span>
            <span>
              <IconWave size={16} /> Simulator for everyone else
            </span>
            <a href="#cad" style={{ display: "inline-flex", gap: 6, alignItems: "center", fontWeight: 600, color: "var(--accent)" }}>
              Interactive 3D CAD <IconArrow size={14} />
            </a>
          </div>
        </div>
        <div className="hero-visual">
          <img src="/images/compact_v3_assembled.png" alt="CAD render of the GripCheck v3 dynamometer: a black finger half and grey palm half on a compact electronics base" width={600} height={600} />
          <HeroScope />
        </div>
      </div>
    </section>
  );
}

const SCOPE_KINDS: { kind: TrialKind; label: string }[] = [
  { kind: "good", label: "Good" },
  { kind: "slip", label: "Slip" },
  { kind: "false_start", label: "False start" },
  { kind: "submaximal", label: "Slow rise" },
];

/** A simulated squeeze drawn on a loop, like a small oscilloscope. Interactive so visitors can inspect curve shapes. */
function HeroScope() {
  const [kind, setKind] = useState<TrialKind>("good");
  const [runKey, setRunKey] = useState(0);
  const [curve, setCurve] = useState<Reading[]>(() => newCurve("good"));
  const [shown, setShown] = useState(curve.length);

  function trigger(nextKind: TrialKind) {
    setKind(nextKind);
    setCurve(newCurve(nextKind));
    setRunKey((k) => k + 1);
  }

  useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduced) {
      setShown(curve.length);
      return;
    }
    let raf = 0;
    let start = performance.now();
    let current = curve;
    setShown(1);
    const loop = (now: number) => {
      const ms = now - start;
      const n = current.findIndex((r) => r.time_ms > ms);
      setShown(n === -1 ? current.length : n);
      if (ms > 6400) {
        current = newCurve(kind);
        setCurve(current);
        start = now;
      }
      raf = requestAnimationFrame(loop);
    };
    raf = requestAnimationFrame(loop);
    return () => cancelAnimationFrame(raf);
  }, [kind, runKey]);

  const visible = curve.slice(0, Math.max(1, shown));
  const finished = shown >= curve.length;
  const w = 300;
  const h = 140;
  const x = (ms: number) => (ms / 5000) * w;
  const y = (kg: number) => h - 6 - (kg / 40) * (h - 12);
  const d = visible.map((r, i) => `${i ? "L" : "M"}${x(r.time_ms).toFixed(1)},${y(r.force_kg).toFixed(1)}`).join("");
  const now = visible[visible.length - 1];
  const peak = visible.reduce((m, r) => Math.max(m, r.force_kg), 0);

  const summary = useMemo(() => {
    const p = findPeak(curve).force_kg;
    const ttp = timeToPeakMs(curve);
    const rfd = rfdNPerS(curve);
    const q = checkTrial(curve);
    return { peak: p, ttp, rfd, q };
  }, [curve]);

  const strokeColor = kind === "good" ? "var(--accent)" : "var(--left)";

  return (
    <div className="scope">
      <div className="scope-head">
        <span className="eyebrow">Live force</span>
        <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
          {finished ? (
            <span className={`tag ${summary.q === "good" ? "ok" : "warn"}`}>{QUALITY_TEXT[summary.q].title}</span>
          ) : (
            <span className="tag">Simulated</span>
          )}
          <button
            type="button"
            className="scope-replay"
            onClick={() => trigger(kind)}
            title="Replay simulated squeeze"
            aria-label="Replay simulated squeeze"
          >
            <IconRefresh size={13} />
          </button>
        </div>
      </div>
      <div className="scope-value" style={{ marginTop: 8 }}>
        {now.force_kg.toFixed(1)}
        <small>kg</small>
      </div>
      <div className="scope-stats mono small muted">
        <span>peak {peak.toFixed(1)} kg</span>
        <span>·</span>
        <span>{finished ? `TTP ${summary.ttp} ms` : `${(now.time_ms / 1000).toFixed(1)} / 5.0 s`}</span>
        {finished && summary.rfd !== null && (
          <>
            <span>·</span>
            <span>{Math.round(summary.rfd)} N/s</span>
          </>
        )}
      </div>
      <svg viewBox={`0 0 ${w} ${h}`} aria-hidden="true">
        {[0, 10, 20, 30, 40].map((kg) => (
          <line key={kg} x1={0} x2={w} y1={y(kg)} y2={y(kg)} stroke="var(--rule)" />
        ))}
        {visible.length > 1 && (
          <>
            <path d={`${d}L${x(now.time_ms)},${y(0)}L0,${y(0)}Z`} fill={strokeColor} opacity={0.12} />
            <path d={d} fill="none" stroke={strokeColor} strokeWidth={2.2} strokeLinejoin="round" />
            <circle cx={x(now.time_ms)} cy={y(now.force_kg)} r={3.5} fill={strokeColor} />
          </>
        )}
      </svg>
      <div className="scope-pills" role="group" aria-label="Try simulated curve shapes">
        {SCOPE_KINDS.map((item) => (
          <button
            key={item.kind}
            type="button"
            className={`scope-pill${kind === item.kind ? " active" : ""}`}
            onClick={() => trigger(item.kind)}
          >
            {item.label}
          </button>
        ))}
      </div>
    </div>
  );
}

function newCurve(kind: TrialKind = "good"): Reading[] {
  return filterReadings(linesToReadings(makeLines("right", "max", 5, Math.random, kind)).readings);
}

// ---------------------------------------------------------------- mission

function Mission() {
  return (
    <section className="section band" id="mission">
      <div className="container two-col">
        <div className="section-head" style={{ marginBottom: 0 }}>
          <span className="eyebrow">Mission</span>
          <h2>Make a key measure of muscle health cheap to take and rich to read.</h2>
        </div>
        <div className="prose">
          <p>
            <strong>Grip strength is one of the simplest indicators of overall muscle function.</strong> It is linked to mobility, recovery after
            surgery and all-cause mortality, and it is a core criterion in current definitions of sarcopenia (age-related muscle loss).
          </p>
          <p>
            Clinical dynamometers such as the Jamar cost several hundred dollars and show a single peak on a dial. This project asks whether a
            device built from about <strong>CA$90 of parts</strong> can reproduce that peak, and also record the <strong>entire force-time curve</strong>
            : how fast force rises, and how well it is held.
          </p>
          <p>
            The goal is an instrument a student lab, a classroom or a researcher on a budget could build, check and trust, with every design file,
            line of code and calibration step in the open.
          </p>
        </div>
      </div>
      <div className="container" style={{ marginTop: 48 }}>
        <div className="stats">
          <div className="stat">
            <span className="value">≈140k</span>
            <p>people in the PURE study, where grip strength predicted mortality better than systolic blood pressure.</p>
          </div>
          <div className="stat">
            <span className="value">27 / 16 kg</span>
            <p>EWGSOP2 cut-offs for low grip strength in men / women aged 65+.</p>
          </div>
          <div className="stat">
            <span className="value">≈CA$90</span>
            <p>parts and printing for one device, from the project's bill of materials (including spare boards).</p>
          </div>
          <div className="stat">
            <span className="value">5 metrics</span>
            <p>from every session, where a dial gives one: peak, time to peak, RFD, fatigue index and asymmetry.</p>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- what it achieves

function Capabilities() {
  const features = [
    {
      icon: <IconTarget />,
      title: "Standardized protocol",
      text: "Three maximal squeezes per hand, alternating, then a 30 s hold. Posture and encouragement are fixed in code, following ASHT recommendations, so every trial is given the same way.",
    },
    {
      icon: <IconChart />,
      title: "The full force-time curve",
      text: "Every sample is kept. Peak, time to peak, rate of force development, fatigue index and left/right asymmetry come from the curve, not from a needle.",
    },
    {
      icon: <IconShield />,
      title: "Automatic trial check",
      text: "Each squeeze is checked for a false start, a slip or a less-than-full effort from the curve's shape, so a bad trial can be repeated straight away.",
    },
    {
      icon: <IconClock />,
      title: "Compared with norms",
      text: "The best grip is placed on age- and sex-specific centiles from Dodds et al. (2014), with a Z-score, T-score and, for 65+, clinical cut-offs.",
    },
    {
      icon: <IconUsb />,
      title: "Nothing to install",
      text: "The browser reads the device over USB (Web Serial). The analysis runs on the page itself, so results never leave the computer.",
    },
    {
      icon: <IconChip />,
      title: "Honest about accuracy",
      text: "The firmware's scale factor is a datasheet estimate until the known-mass calibration is done, and every screen and report says so.",
    },
  ];
  return (
    <section className="section" id="what">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">What it achieves</span>
          <h2>A clinical-style grip test, with more information per squeeze.</h2>
          <p className="lead">The device measures force. The software turns it into a test anyone can run the same way twice.</p>
        </div>
        <div className="feature-grid">
          {features.map((f) => (
            <article className="card feature" key={f.title}>
              <span className="icon">{f.icon}</span>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </article>
          ))}
        </div>
        <div className="metric-strip" style={{ marginTop: 16 }}>
          {[
            ["Peak force", "kg", "Highest filtered force; best of three per hand."],
            ["Time to peak", "ms", "From onset (5 % of peak) to the peak."],
            ["RFD", "N/s", "Slope of force over the first 200 ms after onset."],
            ["Fatigue index", "%", "Drop from peak to the last second of a 30 s hold."],
            ["Asymmetry", "L/R", "Ratio of the best left to the best right squeeze."],
          ].map(([name, unit, text]) => (
            <div className="metric-tile" key={name}>
              <span className="unit">{unit}</span>
              <b>{name}</b>
              <span>{text}</span>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- device

function Device() {
  return (
    <section className="section band" id="device">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">The device</span>
          <h2>Every squeeze goes through the load cell.</h2>
          <p className="lead">
            The barrel handle splits lengthwise. The palm half bolts to one end of the load cell, the finger half to the other, and a 3 mm seam keeps
            them apart, so squeezing the halves together bends the cell and nothing else. Switch below between the current v3 build and the next
            Jamar-style prototype.
          </p>
        </div>

        <div id="cad" style={{ marginBottom: 28 }}>
          <Suspense
            fallback={
              <div className="card cad-shell" style={{ padding: 48, display: "grid", placeItems: "center", gap: 12, minHeight: 460 }}>
                <div className="spinner" aria-hidden="true" />
                <span className="muted small">Loading 3D CAD viewer…</span>
              </div>
            }
          >
            <CadViewer />
          </Suspense>
        </div>

        <div className="two-col">
          <div className="gallery" style={{ gridTemplateColumns: "1fr 1fr" }}>
            <figure className="figure" style={{ gridColumn: "span 2" }}>
              <div className="frame">
                <img className="render" src="/images/compact_v3_section.png" alt="Section view of the v3 dynamometer showing the load cell between the palm and finger halves" loading="lazy" />
              </div>
              <figcaption>Section through the v3 design: the cell is the only path between the two halves.</figcaption>
            </figure>
            <figure className="figure">
              <div className="frame">
                <img className="render" src="/images/compact_v3_inside.png" alt="Inside the electronics box, with the Arduino Nano and HX711 board" loading="lazy" />
              </div>
              <figcaption>The 57 × 82 mm base holds the Nano, HX711 and coiled cable.</figcaption>
            </figure>
            <figure className="figure">
              <div className="frame">
                <img src="/images/2026-10-12_cell_side.jpg" alt="Photo of the CZL601 load cell" loading="lazy" />
              </div>
              <figcaption>The CZL601 100 kg parallel-beam load cell.</figcaption>
            </figure>
          </div>
          <dl className="spec-list">
            <dt>Sensor</dt>
            <dd>CZL601 single-point parallel-beam load cell, 100 kg, 2.0 mV/V</dd>
            <dt>Amplifier</dt>
            <dd>HX711 24-bit ADC, 10 samples/s now (80 with the RATE pin tied high)</dd>
            <dt>Controller</dt>
            <dd>Arduino Nano (ATmega328P), USB serial at 115200 baud</dd>
            <dt>Body</dt>
            <dd>Printed PETG, split barrel handle on a closed 57 × 82 mm base, about 204 mm tall</dd>
            <dt>Fasteners</dt>
            <dd>6 × M6 × 25 button heads into the cell, 4 × M3 for the cover</dd>
            <dt>CAD</dt>
            <dd>CadQuery Python scripts + Onshape STEP assemblies for both the v3 Split-Grip and v4 Jamar-style 5-position prototype</dd>
            <dt>Load limit</dt>
            <dd>Printed parts are not yet tested above 34 kg (75 lb), so calibration loads stay below that</dd>
          </dl>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- software

function Software() {
  return (
    <section className="section" id="software">
      <div className="container two-col">
        <div className="section-head" style={{ marginBottom: 0 }}>
          <span className="eyebrow">The software</span>
          <h2>From raw counts to a report, in the browser.</h2>
          <p className="lead">The firmware streams one line per sample. GripCheck does everything else.</p>
          <div className="btn-row" style={{ marginTop: 8 }}>
            <Link className="btn btn-secondary" to="/how-it-works">
              Read the details <IconArrow />
            </Link>
            <a className="btn btn-ghost" href={REPO_URL} target="_blank" rel="noreferrer">
              <IconGithub /> Source code
            </a>
          </div>
        </div>
        <ol className="timeline">
          {[
            ["1", "Stream", "The Nano prints t_ms,raw,net,force_kg about 10 times a second and re-zeroes on “T”."],
            ["2", "Filter", "A zero-phase 4th-order Butterworth low-pass removes noise without shifting the curve in time."],
            ["3", "Measure", "Onset, peak, time to peak, RFD and fatigue index are computed on the filtered curve."],
            ["4", "Check", "Five shape features flag false starts, slips and submaximal efforts."],
            ["5", "Compare", "The best grip is placed on Dodds 2014 centiles for the participant's age and sex."],
          ].map(([n, title, text]) => (
            <li key={n}>
              <span className="gate">{n}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
              <span />
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- status

function Status() {
  const gates: [string, string, string, "done" | "next" | ""][] = [
    ["G0", "Printed parts fit the cell", "Fit coupon printed and checked, October 2026.", "done"],
    ["G1", "First signal on the bench", "Rest about +52,400 counts, noise about ±70 counts (≈2 g). Passed 6 Nov 2026.", "done"],
    ["G2", "Assembled grip reads and returns to zero", "A squeeze reads positive and returns on release. Passed 12 Nov 2026.", "done"],
    ["→", "First full test with GripCheck on the device", "Zero, six squeezes, the 30 s hold and a report from the real Nano, logged in the build log.", "next"],
    ["G3", "Calibration with known masses", "Fit counts per kg, linearity, hysteresis and repeatability up to 34 kg. Until then forces are datasheet estimates (about ±10 %).", "next"],
    ["V", "Agreement with a clinical device", "Paired tests against a Jamar dynamometer, analysed with Bland-Altman (bias and 95 % limits of agreement), not correlation alone.", ""],
  ];
  return (
    <section className="section band" id="status">
      <div className="container two-col">
        <div className="section-head" style={{ marginBottom: 0 }}>
          <span className="eyebrow">Status · November 2026</span>
          <h2>Built and reading. Not yet calibrated.</h2>
          <p className="lead">
            The device works end to end on the bench. Its forces are scaled from the load-cell datasheet, so they are estimates until gate G3 is done.
            Everything shown on this site that is labelled simulated was generated, not measured.
          </p>
        </div>
        <ol className="timeline">
          {gates.map(([g, title, text, state]) => (
            <li key={g} className={state}>
              <span className="gate">{g}</span>
              <div>
                <h3>{title}</h3>
                <p>{text}</p>
              </div>
              <span className={`tag ${state === "done" ? "ok" : state === "next" ? "accent" : ""}`}>
                {state === "done" ? "Passed" : state === "next" ? "Next" : "Planned"}
              </span>
            </li>
          ))}
        </ol>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------- team

function Team() {
  return (
    <section className="section" id="team">
      <div className="container">
        <div className="section-head">
          <span className="eyebrow">Team</span>
          <h2>Two builders, one instrument.</h2>
        </div>
        <div className="team">
          <article className="card person">
            <span className="avatar">TK</span>
            <div>
              <h3>Thomas Kim</h3>
              <p>Hardware design, CAD, mechanical assembly, Arduino firmware and the calibration procedure.</p>
            </div>
          </article>
          <article className="card person">
            <span className="avatar alt">SK</span>
            <div>
              <h3>Samuel Koo</h3>
              <p>The GripCheck application: test protocol, signal analysis, trial-quality check and normative comparison.</p>
            </div>
          </article>
        </div>
      </div>
    </section>
  );
}

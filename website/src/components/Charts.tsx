// Charts, written by hand (no chart library): a canvas for the live recording, interactive SVGs for reports & history.
// Colours come from CSS variables, so charts follow light/dark mode and print correctly.

import { useEffect, useMemo, useRef, useState, type PointerEvent } from "react";
import type { NormRow } from "../data/norms";
import { findPeak } from "../lib/metrics";
import type { Reading } from "../lib/types";
import { convertKg, type ForceUnit } from "../lib/units";

export interface Pt {
  t: number; // ms
  f: number; // kg
}

const cssVar = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/** "Nice" axis maximum: 40, 50, 60 ... with 15 % headroom above the data. */
export function niceMax(peak: number, floor = 40): number {
  return Math.max(floor, Math.ceil((peak * 1.15) / 10) * 10);
}

/** Binary search nearest reading by time_ms. */
function nearestReading(readings: Reading[], targetMs: number): Reading | null {
  if (readings.length === 0) return null;
  let lo = 0;
  let hi = readings.length - 1;
  while (lo < hi) {
    const mid = (lo + hi) >> 1;
    if (readings[mid].time_ms < targetMs) lo = mid + 1;
    else hi = mid;
  }
  if (lo > 0 && Math.abs(readings[lo - 1].time_ms - targetMs) < Math.abs(readings[lo].time_ms - targetMs)) {
    return readings[lo - 1];
  }
  return readings[lo];
}

// ---------------------------------------------------------------- live canvas

interface LiveProps {
  points: Pt[]; // mutated in place while recording; `tick` tells us to redraw
  tick: number;
  seconds: number;
  colorVar: string;
  ghosts: Pt[][]; // earlier trials of the same hand, drawn faintly
  label: string;
  unit?: ForceUnit;
}

export function LiveChart(props: LiveProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  // the resize/theme listeners are set up once, so they read the newest props from this ref
  const latest = useRef(props);
  latest.current = props;

  const draw = () => {
    const { points, seconds, colorVar, ghosts, unit = "kg" } = latest.current;
    const canvas = ref.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const w = canvas.clientWidth;
    const h = canvas.clientHeight;
    if (w === 0 || h === 0) return;
    if (canvas.width !== Math.round(w * dpr) || canvas.height !== Math.round(h * dpr)) {
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
    }
    const ctx = canvas.getContext("2d")!;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);

    const ink = { muted: cssVar("--muted"), rule: cssVar("--rule"), faint: cssVar("--trace-faint"), mono: cssVar("--mono") };
    const color = cssVar(colorVar);
    const pad = { l: 44, r: 12, t: 12, b: 28 };
    const peakKg = Math.max(0, ...points.map((p) => p.f), ...ghosts.flat().map((p) => p.f));
    const yMax = niceMax(convertKg(peakKg, unit), unit === "lb" ? 90 : 40);
    const x = (ms: number) => pad.l + (ms / 1000 / seconds) * (w - pad.l - pad.r);
    const y = (kg: number) => h - pad.b - (Math.max(0, convertKg(kg, unit)) / yMax) * (h - pad.t - pad.b);

    ctx.font = `11px ${ink.mono}`;
    ctx.lineWidth = 1;
    const yStep = yMax > 140 ? 40 : yMax > 100 ? 20 : 10;
    for (let v = 0; v <= yMax; v += yStep) {
      const yy = h - pad.b - (v / yMax) * (h - pad.t - pad.b);
      ctx.strokeStyle = ink.rule;
      ctx.beginPath();
      ctx.moveTo(pad.l, Math.round(yy) + 0.5);
      ctx.lineTo(w - pad.r, Math.round(yy) + 0.5);
      ctx.stroke();
      ctx.fillStyle = ink.muted;
      ctx.textAlign = "right";
      ctx.fillText(String(v), pad.l - 8, yy + 4);
    }
    const xStep = seconds > 10 ? 5 : 1;
    ctx.textAlign = "center";
    for (let s = 0; s <= seconds; s += xStep) ctx.fillText(`${s}s`, x(s * 1000), h - pad.b + 18);
    ctx.save();
    ctx.translate(12, (h - pad.b) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText(unit, 0, 0);
    ctx.restore();

    const path = (pts: Pt[]) => {
      ctx.beginPath();
      pts.forEach((p, i) => (i ? ctx.lineTo(x(p.t), y(p.f)) : ctx.moveTo(x(p.t), y(p.f))));
    };
    for (const g of ghosts) {
      if (g.length < 2) continue;
      path(g);
      ctx.strokeStyle = ink.faint;
      ctx.globalAlpha = 0.55;
      ctx.lineWidth = 1.5;
      ctx.lineJoin = "round";
      ctx.stroke();
      ctx.globalAlpha = 1;
    }
    if (points.length < 2) return;

    // area under the live curve, then the curve
    const grad = ctx.createLinearGradient(0, pad.t, 0, h - pad.b);
    grad.addColorStop(0, color);
    grad.addColorStop(1, "transparent");
    path(points);
    ctx.lineTo(x(points[points.length - 1].t), y(0));
    ctx.lineTo(x(points[0].t), y(0));
    ctx.closePath();
    ctx.globalAlpha = 0.16;
    ctx.fillStyle = grad;
    ctx.fill();
    ctx.globalAlpha = 1;
    path(points);
    ctx.strokeStyle = color;
    ctx.lineWidth = 2.5;
    ctx.lineJoin = "round";
    ctx.stroke();

    // peak marker and label
    const top = points.reduce((a, b) => (b.f > a.f ? b : a));
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(x(top.t), y(top.f), 4.5, 0, Math.PI * 2);
    ctx.fill();
    ctx.font = `500 12px ${ink.mono}`;
    ctx.textAlign = "left";
    ctx.fillText(
      `${convertKg(top.f, unit).toFixed(1)} ${unit}`,
      Math.min(x(top.t) + 8, w - 76),
      Math.max(14, y(top.f) - 8),
    );

    // "now" cursor
    const last = points[points.length - 1];
    ctx.strokeStyle = ink.muted;
    ctx.setLineDash([3, 4]);
    ctx.beginPath();
    ctx.moveTo(x(last.t), pad.t);
    ctx.lineTo(x(last.t), h - pad.b);
    ctx.stroke();
    ctx.setLineDash([]);
  };

  useEffect(draw, [props.tick, props.points, props.ghosts, props.seconds, props.colorVar, props.unit]);
  useEffect(() => {
    const ro = new ResizeObserver(() => draw());
    if (ref.current) ro.observe(ref.current);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onScheme = () => draw();
    mq.addEventListener("change", onScheme);
    const mo = new MutationObserver(() => requestAnimationFrame(draw));
    mo.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
    return () => {
      ro.disconnect();
      mq.removeEventListener("change", onScheme);
      mo.disconnect();
    };
  }, []);

  return <canvas ref={ref} role="img" aria-label={props.label} />;
}

// ---------------------------------------------------------------- static / interactive SVG force chart

export interface Series {
  name?: string;
  readings: Reading[];
  colorVar: string;
  width?: number;
  opacity?: number;
  markPeak?: boolean;
  area?: boolean;
  dashed?: boolean;
  hoverable?: boolean;
}

interface ForceChartProps {
  series: Series[];
  seconds?: number;
  height?: number;
  width?: number;
  label: string;
  compact?: boolean;
  yMax?: number;
  unit?: ForceUnit;
  annotate?: { atMs: number; text: string }[];
  rfdWindow?: { onsetMs: number; windowMs?: number; colorVar?: string; label?: string } | null;
}

export function ForceChart({
  series,
  seconds,
  height = 240,
  width = 640,
  label,
  compact,
  yMax: fixedY,
  unit = "kg",
  annotate,
  rfdWindow,
}: ForceChartProps) {
  const [hoverMs, setHoverMs] = useState<number | null>(null);
  const pad = compact ? { l: 32, r: 8, t: 8, b: 20 } : { l: 42, r: 12, t: 14, b: 26 };
  const allPeakKg = Math.max(0, ...series.flatMap((s) => s.readings.map((r) => r.force_kg)));
  const yMax = fixedY ? Math.ceil(convertKg(fixedY, unit) / 10) * 10 : niceMax(convertKg(allPeakKg, unit), unit === "lb" ? 40 : 20);
  const lastMs = Math.max(1, ...series.map((s) => s.readings[s.readings.length - 1]?.time_ms ?? 0));
  const xMax = (seconds ?? Math.ceil(lastMs / 1000)) * 1000;
  const x = (ms: number) => pad.l + (ms / xMax) * (width - pad.l - pad.r);
  const y = (kg: number) => height - pad.b - (Math.max(0, convertKg(kg, unit)) / yMax) * (height - pad.t - pad.b);
  const yStep = yMax > 140 ? 40 : yMax > 60 ? 20 : 10;
  const xStepS = xMax > 12000 ? 5 : 1;
  const yTicks = Array.from({ length: Math.floor(yMax / yStep) + 1 }, (_, i) => i * yStep);
  const xTicks = Array.from({ length: Math.floor(xMax / 1000 / xStepS) + 1 }, (_, i) => i * xStepS);
  const d = (rs: Reading[]) => rs.map((r, i) => `${i ? "L" : "M"}${x(r.time_ms).toFixed(1)},${y(r.force_kg).toFixed(1)}`).join("");

  const handlePointer = (e: PointerEvent<SVGSVGElement>) => {
    if (compact) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const svgX = ((e.clientX - rect.left) / rect.width) * width;
    if (svgX < pad.l || svgX > width - pad.r) {
      setHoverMs(null);
      return;
    }
    const ms = ((svgX - pad.l) / (width - pad.l - pad.r)) * xMax;
    setHoverMs(Math.max(0, Math.min(xMax, ms)));
  };

  const hoverSamples = useMemo(() => {
    if (hoverMs === null || compact) return null;
    return series
      .filter((s) => s.readings.length > 0 && s.hoverable !== false)
      .map((s) => ({
        name: s.name,
        colorVar: s.colorVar,
        reading: nearestReading(s.readings, hoverMs)!,
      }))
      .filter((item) => item.reading !== null);
  }, [hoverMs, compact, series]);

  const activeTimeMs = hoverSamples && hoverSamples.length > 0 ? hoverSamples[0].reading.time_ms : null;

  return (
    <div className="chart-wrap">
      <svg
        className={`chart-svg${compact ? "" : " interactive"}`}
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={label}
        onPointerMove={handlePointer}
        onPointerLeave={() => setHoverMs(null)}
      >
        {yTicks.map((v) => {
          const yy = height - pad.b - (v / yMax) * (height - pad.t - pad.b);
          return (
            <g key={v}>
              <line x1={pad.l} x2={width - pad.r} y1={yy} y2={yy} stroke="var(--rule)" />
              <text x={pad.l - 6} y={yy + 4} textAnchor="end">
                {v}
              </text>
            </g>
          );
        })}
        {xTicks.map((s) => (
          <text key={s} x={x(s * 1000)} y={height - pad.b + 15} textAnchor="middle">
            {s}s
          </text>
        ))}
        {rfdWindow && (
          <g>
            <rect
              x={x(rfdWindow.onsetMs)}
              y={pad.t}
              width={Math.max(3, x(rfdWindow.onsetMs + (rfdWindow.windowMs ?? 200)) - x(rfdWindow.onsetMs))}
              height={height - pad.t - pad.b}
              fill={`var(${rfdWindow.colorVar ?? "--accent"})`}
              opacity={0.12}
            />
            <line
              x1={x(rfdWindow.onsetMs)}
              x2={x(rfdWindow.onsetMs)}
              y1={pad.t}
              y2={height - pad.b}
              stroke={`var(${rfdWindow.colorVar ?? "--accent"})`}
              strokeDasharray="2 3"
              opacity={0.75}
            />
            {rfdWindow.label && (
              <text x={x(rfdWindow.onsetMs) + 5} y={pad.t + 11} style={{ fill: `var(${rfdWindow.colorVar ?? "--accent"})` }}>
                {rfdWindow.label}
              </text>
            )}
          </g>
        )}
        {annotate?.map((a) => (
          <g key={a.text}>
            <line x1={x(a.atMs)} x2={x(a.atMs)} y1={pad.t} y2={height - pad.b} stroke="var(--rule-strong)" strokeDasharray="3 4" />
            <text x={x(a.atMs) + 4} y={pad.t + 10}>
              {a.text}
            </text>
          </g>
        ))}
        {series.map((s, i) => {
          if (s.readings.length < 2) return null;
          const peak = findPeak(s.readings);
          const last = s.readings[s.readings.length - 1];
          return (
            <g key={i} opacity={s.opacity ?? 1}>
              {s.area && (
                <path
                  d={`${d(s.readings)}L${x(last.time_ms)},${y(0)}L${x(s.readings[0].time_ms)},${y(0)}Z`}
                  fill={`var(${s.colorVar})`}
                  opacity={0.12}
                />
              )}
              <path
                d={d(s.readings)}
                fill="none"
                stroke={`var(${s.colorVar})`}
                strokeWidth={s.width ?? 2}
                strokeLinejoin="round"
                strokeDasharray={s.dashed ? "4 3" : undefined}
              />
              {s.markPeak && (
                <g>
                  <circle cx={x(peak.time_ms)} cy={y(peak.force_kg)} r={4} fill={`var(${s.colorVar})`} />
                  {!compact && (
                    <text
                      x={Math.min(x(peak.time_ms) + 7, width - 68)}
                      y={i === 0 ? y(peak.force_kg) - 8 : y(peak.force_kg) + 16}
                      style={{ fill: "var(--ink)" }}
                    >
                      {convertKg(peak.force_kg, unit).toFixed(1)} {unit}
                    </text>
                  )}
                </g>
              )}
            </g>
          );
        })}
        {activeTimeMs !== null && hoverSamples && (
          <g pointerEvents="none">
            <line x1={x(activeTimeMs)} x2={x(activeTimeMs)} y1={pad.t} y2={height - pad.b} stroke="var(--ink-2)" strokeDasharray="3 3" opacity={0.6} />
            {hoverSamples.map((item, idx) => (
              <circle
                key={idx}
                cx={x(item.reading.time_ms)}
                cy={y(item.reading.force_kg)}
                r={4.5}
                fill={`var(${item.colorVar})`}
                stroke="var(--surface)"
                strokeWidth={2}
              />
            ))}
          </g>
        )}
      </svg>
      {!compact && activeTimeMs !== null && hoverSamples && hoverSamples.length > 0 && (
        <div
          className="chart-tooltip"
          style={{
            left: `${Math.min(78, Math.max(12, (x(activeTimeMs) / width) * 100))}%`,
          }}
          aria-hidden="true"
        >
          <span className="mono muted">t = {(activeTimeMs / 1000).toFixed(2)} s</span>
          {hoverSamples.map((item, idx) => (
            <span key={idx} className="mono">
              <i className="dot" style={{ background: `var(${item.colorVar})` }} />
              {item.name ? `${item.name}: ` : ""}
              <b>
                {convertKg(item.reading.force_kg, unit).toFixed(1)} {unit}
              </b>
            </span>
          ))}
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- centile chart

interface CentileProps {
  rows: NormRow[];
  age: number;
  force: number;
  sexLabel: string;
  unit?: ForceUnit;
  cutoffKg?: number;
}

export function CentileChart({ rows, age, force, sexLabel, unit = "kg", cutoffKg }: CentileProps) {
  const [hoverAge, setHoverAge] = useState<number | null>(null);
  const width = 640;
  const height = 300;
  const pad = { l: 42, r: 14, t: 14, b: 32 };
  const maxVal = Math.max(convertKg(force, unit), ...rows.map((r) => convertKg(r.p90, unit)));
  const yMax = niceMax(maxVal, unit === "lb" ? 90 : 40);
  const x = (a: number) => pad.l + ((a - 5) / 95) * (width - pad.l - pad.r);
  const y = (kg: number) => height - pad.b - (convertKg(kg, unit) / yMax) * (height - pad.t - pad.b);
  const band = (lo: keyof NormRow, hi: keyof NormRow) =>
    rows.map((r, i) => `${i ? "L" : "M"}${x(r.age)},${y(r[hi] as number)}`).join("") +
    [...rows].reverse().map((r) => `L${x(r.age)},${y(r[lo] as number)}`).join("") +
    "Z";
  const median = rows.map((r, i) => `${i ? "L" : "M"}${x(r.age)},${y(r.p50)}`).join("");
  const yStep = yMax > 140 ? 40 : yMax > 90 ? 20 : 10;
  const yTicks = useMemo(() => Array.from({ length: Math.floor(yMax / yStep) + 1 }, (_, i) => i * yStep), [yMax, yStep]);

  const hoveredRow = useMemo(() => {
    if (hoverAge === null) return null;
    let best = rows[0];
    let gap = Infinity;
    for (const r of rows) {
      const g = Math.abs(r.age - hoverAge);
      if (g < gap) {
        gap = g;
        best = r;
      }
    }
    return best;
  }, [hoverAge, rows]);

  const onPointer = (e: PointerEvent<SVGSVGElement>) => {
    const rect = e.currentTarget.getBoundingClientRect();
    const svgX = ((e.clientX - rect.left) / rect.width) * width;
    if (svgX < pad.l || svgX > width - pad.r) {
      setHoverAge(null);
      return;
    }
    const a = 5 + ((svgX - pad.l) / (width - pad.l - pad.r)) * 95;
    setHoverAge(Math.max(5, Math.min(100, a)));
  };

  return (
    <div className="chart-wrap">
      <svg
        className="chart-svg interactive"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Grip strength norms for ${sexLabel} by age, with this measurement of ${convertKg(force, unit).toFixed(1)} ${unit} at age ${age}.`}
        onPointerMove={onPointer}
        onPointerLeave={() => setHoverAge(null)}
      >
        {yTicks.map((v) => {
          const yy = height - pad.b - (v / yMax) * (height - pad.t - pad.b);
          return (
            <g key={v}>
              <line x1={pad.l} x2={width - pad.r} y1={yy} y2={yy} stroke="var(--rule)" />
              <text x={pad.l - 6} y={yy + 4} textAnchor="end">
                {v}
              </text>
            </g>
          );
        })}
        {[5, 20, 40, 60, 80, 100].map((a) => (
          <text key={a} x={x(a)} y={height - pad.b + 16} textAnchor="middle">
            {a}
          </text>
        ))}
        <text x={width - pad.r} y={height - 2} textAnchor="end">
          age (years)
        </text>
        <path d={band("p10", "p90")} fill="var(--band-outer)" />
        <path d={band("p25", "p75")} fill="var(--band-inner)" />
        <path d={median} fill="none" stroke="var(--muted)" strokeWidth={2} />
        {cutoffKg !== undefined && age >= 65 && (
          <g>
            <line
              x1={x(65)}
              x2={width - pad.r}
              y1={y(cutoffKg)}
              y2={y(cutoffKg)}
              stroke="var(--warn)"
              strokeDasharray="4 4"
              opacity={0.85}
            />
            <text x={width - pad.r - 4} y={y(cutoffKg) - 5} textAnchor="end" style={{ fill: "var(--warn)" }}>
              65+ cut-off ({convertKg(cutoffKg, unit).toFixed(0)} {unit})
            </text>
          </g>
        )}
        <line x1={x(age)} x2={x(age)} y1={pad.t} y2={height - pad.b} stroke="var(--accent)" strokeDasharray="3 4" opacity={0.6} />
        <circle cx={x(age)} cy={y(force)} r={7} fill="var(--accent)" stroke="var(--surface)" strokeWidth={2.5} />
        <text
          x={x(age) + (age > 75 ? -12 : 12)}
          y={y(force) - 10}
          textAnchor={age > 75 ? "end" : "start"}
          style={{ fill: "var(--ink)", fontWeight: 500 }}
        >
          {convertKg(force, unit).toFixed(1)} {unit}
        </text>
        {hoveredRow && (
          <g pointerEvents="none">
            <line
              x1={x(hoveredRow.age)}
              x2={x(hoveredRow.age)}
              y1={pad.t}
              y2={height - pad.b}
              stroke="var(--ink-2)"
              strokeDasharray="3 3"
              opacity={0.5}
            />
            <circle cx={x(hoveredRow.age)} cy={y(hoveredRow.p50)} r={4} fill="var(--muted)" stroke="var(--surface)" strokeWidth={1.5} />
          </g>
        )}
      </svg>
      {hoveredRow && (
        <div
          className="chart-tooltip"
          style={{
            left: `${Math.min(76, Math.max(16, (x(hoveredRow.age) / width) * 100))}%`,
          }}
          aria-hidden="true"
        >
          <span className="mono muted">Age ~{hoveredRow.age} y</span>
          <span className="mono">
            Median: <b>{convertKg(hoveredRow.p50, unit).toFixed(1)} {unit}</b>
          </span>
          <span className="mono muted">
            25–75th: {convertKg(hoveredRow.p25, unit).toFixed(0)}–{convertKg(hoveredRow.p75, unit).toFixed(0)} · 10–90th: {convertKg(hoveredRow.p10, unit).toFixed(0)}–{convertKg(hoveredRow.p90, unit).toFixed(0)}
          </span>
        </div>
      )}
    </div>
  );
}

// ---------------------------------------------------------------- multi-session trend chart

export interface TrendPoint {
  id: string;
  label: string;
  rightKg: number;
  leftKg: number;
  bestKg: number;
}

export function TrendChart({ points, unit = "kg" }: { points: TrendPoint[]; unit?: ForceUnit }) {
  const [hoverIdx, setHoverIdx] = useState<number | null>(null);
  const width = 820;
  const height = 220;
  const pad = { l: 42, r: 16, t: 16, b: 30 };
  const maxKg = Math.max(10, ...points.map((p) => Math.max(p.rightKg, p.leftKg, p.bestKg)));
  const yMax = niceMax(convertKg(maxKg, unit), unit === "lb" ? 60 : 30);
  const x = (i: number) =>
    points.length === 1 ? (pad.l + width - pad.r) / 2 : pad.l + (i / (points.length - 1)) * (width - pad.l - pad.r);
  const y = (kg: number) => height - pad.b - (convertKg(kg, unit) / yMax) * (height - pad.t - pad.b);
  const yStep = yMax > 140 ? 40 : yMax > 60 ? 20 : 10;
  const yTicks = Array.from({ length: Math.floor(yMax / yStep) + 1 }, (_, i) => i * yStep);

  const linePath = (vals: number[]) => vals.map((v, i) => `${i ? "L" : "M"}${x(i).toFixed(1)},${y(v).toFixed(1)}`).join("");

  const onPointer = (e: PointerEvent<SVGSVGElement>) => {
    if (points.length === 0) return;
    const rect = e.currentTarget.getBoundingClientRect();
    const svgX = ((e.clientX - rect.left) / rect.width) * width;
    let best = 0;
    let dist = Infinity;
    for (let i = 0; i < points.length; i++) {
      const d = Math.abs(x(i) - svgX);
      if (d < dist) {
        dist = d;
        best = i;
      }
    }
    setHoverIdx(best);
  };

  return (
    <div className="chart-wrap">
      <svg
        className="chart-svg interactive"
        viewBox={`0 0 ${width} ${height}`}
        role="img"
        aria-label={`Best right and left hand peak force across ${points.length} sessions.`}
        onPointerMove={onPointer}
        onPointerLeave={() => setHoverIdx(null)}
      >
        {yTicks.map((v) => {
          const yy = height - pad.b - (v / yMax) * (height - pad.t - pad.b);
          return (
            <g key={v}>
              <line x1={pad.l} x2={width - pad.r} y1={yy} y2={yy} stroke="var(--rule)" />
              <text x={pad.l - 6} y={yy + 4} textAnchor="end">
                {v}
              </text>
            </g>
          );
        })}
        <path d={linePath(points.map((p) => p.rightKg))} fill="none" stroke="var(--right)" strokeWidth={2.2} strokeLinejoin="round" />
        <path d={linePath(points.map((p) => p.leftKg))} fill="none" stroke="var(--left)" strokeWidth={2.2} strokeLinejoin="round" />
        {points.map((p, i) => (
          <g key={p.id}>
            <circle cx={x(i)} cy={y(p.rightKg)} r={hoverIdx === i ? 5.5 : 3.8} fill="var(--right)" stroke="var(--surface)" strokeWidth={1.5} />
            <circle cx={x(i)} cy={y(p.leftKg)} r={hoverIdx === i ? 5.5 : 3.8} fill="var(--left)" stroke="var(--surface)" strokeWidth={1.5} />
            {(points.length <= 8 || i === 0 || i === points.length - 1 || i === hoverIdx) && (
              <text x={x(i)} y={height - pad.b + 16} textAnchor="middle">
                {p.label}
              </text>
            )}
          </g>
        ))}
      </svg>
      {hoverIdx !== null && points[hoverIdx] && (
        <div
          className="chart-tooltip"
          style={{ left: `${Math.min(76, Math.max(16, (x(hoverIdx) / width) * 100))}%` }}
          aria-hidden="true"
        >
          <span className="mono muted">{points[hoverIdx].label}</span>
          <span className="mono">
            <i className="dot" style={{ background: "var(--right)" }} />
            Right: <b>{convertKg(points[hoverIdx].rightKg, unit).toFixed(1)} {unit}</b>
          </span>
          <span className="mono">
            <i className="dot" style={{ background: "var(--left)" }} />
            Left: <b>{convertKg(points[hoverIdx].leftKg, unit).toFixed(1)} {unit}</b>
          </span>
        </div>
      )}
    </div>
  );
}

// Charts, written by hand (no chart library): a canvas for the live recording, SVG for reports.
// Colours come from CSS variables, so charts follow light/dark mode and print correctly.

import { useEffect, useMemo, useRef } from "react";
import { findPeak } from "../lib/metrics";
import type { NormRow } from "../data/norms";
import type { Reading } from "../lib/types";

export interface Pt {
  t: number; // ms
  f: number; // kg
}

const cssVar = (name: string) => getComputedStyle(document.documentElement).getPropertyValue(name).trim();

/** "Nice" axis maximum: 40, 50, 60 ... with 15 % headroom above the data. */
export function niceMax(peak: number, floor = 40): number {
  return Math.max(floor, Math.ceil((peak * 1.15) / 10) * 10);
}

// ---------------------------------------------------------------- live canvas

interface LiveProps {
  points: Pt[]; // mutated in place while recording; `tick` tells us to redraw
  tick: number;
  seconds: number;
  colorVar: string;
  ghosts: Pt[][]; // earlier trials of the same hand, drawn faintly
  label: string;
}

export function LiveChart(props: LiveProps) {
  const ref = useRef<HTMLCanvasElement>(null);
  // the resize/theme listeners are set up once, so they read the newest props from this ref
  const latest = useRef(props);
  latest.current = props;

  const draw = () => {
    const { points, seconds, colorVar, ghosts } = latest.current;
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
    const peak = Math.max(0, ...points.map((p) => p.f), ...ghosts.flat().map((p) => p.f));
    const yMax = niceMax(peak);
    const x = (ms: number) => pad.l + (ms / 1000 / seconds) * (w - pad.l - pad.r);
    const y = (kg: number) => h - pad.b - (Math.max(0, kg) / yMax) * (h - pad.t - pad.b);

    ctx.font = `11px ${ink.mono}`;
    ctx.lineWidth = 1;
    const yStep = yMax > 100 ? 20 : 10;
    for (let kg = 0; kg <= yMax; kg += yStep) {
      ctx.strokeStyle = ink.rule;
      ctx.beginPath();
      ctx.moveTo(pad.l, Math.round(y(kg)) + 0.5);
      ctx.lineTo(w - pad.r, Math.round(y(kg)) + 0.5);
      ctx.stroke();
      ctx.fillStyle = ink.muted;
      ctx.textAlign = "right";
      ctx.fillText(String(kg), pad.l - 8, y(kg) + 4);
    }
    const xStep = seconds > 10 ? 5 : 1;
    ctx.textAlign = "center";
    for (let s = 0; s <= seconds; s += xStep) ctx.fillText(`${s}s`, x(s * 1000), h - pad.b + 18);
    ctx.save();
    ctx.translate(12, (h - pad.b) / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.fillText("kg", 0, 0);
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
    ctx.fillText(`${top.f.toFixed(1)} kg`, Math.min(x(top.t) + 8, w - 70), Math.max(14, y(top.f) - 8));

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

  useEffect(draw, [props.tick, props.points, props.ghosts, props.seconds, props.colorVar]);
  useEffect(() => {
    const ro = new ResizeObserver(() => draw());
    if (ref.current) ro.observe(ref.current);
    const mq = window.matchMedia("(prefers-color-scheme: dark)");
    const onScheme = () => draw();
    mq.addEventListener("change", onScheme);
    return () => {
      ro.disconnect();
      mq.removeEventListener("change", onScheme);
    };
  }, []);

  return <canvas ref={ref} role="img" aria-label={props.label} />;
}

// ---------------------------------------------------------------- static SVG force chart

export interface Series {
  readings: Reading[];
  colorVar: string;
  width?: number;
  opacity?: number;
  markPeak?: boolean;
  area?: boolean;
}

interface ForceChartProps {
  series: Series[];
  seconds?: number;
  height?: number;
  width?: number;
  label: string;
  compact?: boolean;
  yMax?: number;
  annotate?: { atMs: number; text: string }[];
}

export function ForceChart({ series, seconds, height = 240, width = 640, label, compact, yMax: fixedY, annotate }: ForceChartProps) {
  const pad = compact ? { l: 30, r: 8, t: 8, b: 20 } : { l: 40, r: 12, t: 14, b: 26 };
  const allPeak = Math.max(0, ...series.flatMap((s) => s.readings.map((r) => r.force_kg)));
  const yMax = fixedY ?? niceMax(allPeak, 20);
  const lastMs = Math.max(1, ...series.map((s) => s.readings[s.readings.length - 1]?.time_ms ?? 0));
  const xMax = (seconds ?? Math.ceil(lastMs / 1000)) * 1000;
  const x = (ms: number) => pad.l + (ms / xMax) * (width - pad.l - pad.r);
  const y = (kg: number) => height - pad.b - (Math.max(0, kg) / yMax) * (height - pad.t - pad.b);
  const yStep = yMax > 60 ? 20 : 10;
  const xStepS = xMax > 12000 ? 5 : 1;
  const yTicks = Array.from({ length: Math.floor(yMax / yStep) + 1 }, (_, i) => i * yStep);
  const xTicks = Array.from({ length: Math.floor(xMax / 1000 / xStepS) + 1 }, (_, i) => i * xStepS);
  const d = (rs: Reading[]) => rs.map((r, i) => `${i ? "L" : "M"}${x(r.time_ms).toFixed(1)},${y(r.force_kg).toFixed(1)}`).join("");

  return (
    <svg className="chart-svg" viewBox={`0 0 ${width} ${height}`} role="img" aria-label={label}>
      {yTicks.map((kg) => (
        <g key={kg}>
          <line x1={pad.l} x2={width - pad.r} y1={y(kg)} y2={y(kg)} stroke="var(--rule)" />
          <text x={pad.l - 6} y={y(kg) + 4} textAnchor="end">
            {kg}
          </text>
        </g>
      ))}
      {xTicks.map((s) => (
        <text key={s} x={x(s * 1000)} y={height - pad.b + 15} textAnchor="middle">
          {s}s
        </text>
      ))}
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
            <path d={d(s.readings)} fill="none" stroke={`var(${s.colorVar})`} strokeWidth={s.width ?? 2} strokeLinejoin="round" />
            {s.markPeak && (
              <g>
                <circle cx={x(peak.time_ms)} cy={y(peak.force_kg)} r={4} fill={`var(${s.colorVar})`} />
                {!compact && (
                  <text
                    x={Math.min(x(peak.time_ms) + 7, width - 60)}
                    y={i === 0 ? y(peak.force_kg) - 8 : y(peak.force_kg) + 16}
                    style={{ fill: "var(--ink)" }}
                  >
                    {peak.force_kg.toFixed(1)} kg
                  </text>
                )}
              </g>
            )}
          </g>
        );
      })}
    </svg>
  );
}

// ---------------------------------------------------------------- centile chart

interface CentileProps {
  rows: NormRow[];
  age: number;
  force: number;
  sexLabel: string;
}

export function CentileChart({ rows, age, force, sexLabel }: CentileProps) {
  const width = 640;
  const height = 300;
  const pad = { l: 40, r: 14, t: 14, b: 32 };
  const yMax = niceMax(Math.max(force, ...rows.map((r) => r.p90)), 40);
  const x = (a: number) => pad.l + ((a - 5) / 95) * (width - pad.l - pad.r);
  const y = (kg: number) => height - pad.b - (kg / yMax) * (height - pad.t - pad.b);
  const band = (lo: keyof NormRow, hi: keyof NormRow) =>
    rows.map((r, i) => `${i ? "L" : "M"}${x(r.age)},${y(r[hi] as number)}`).join("") +
    [...rows].reverse().map((r) => `L${x(r.age)},${y(r[lo] as number)}`).join("") +
    "Z";
  const median = rows.map((r, i) => `${i ? "L" : "M"}${x(r.age)},${y(r.p50)}`).join("");
  const yTicks = useMemo(() => Array.from({ length: Math.floor(yMax / 10) + 1 }, (_, i) => i * 10), [yMax]);

  return (
    <svg
      className="chart-svg"
      viewBox={`0 0 ${width} ${height}`}
      role="img"
      aria-label={`Grip strength norms for ${sexLabel} by age, with this measurement of ${force.toFixed(1)} kg at age ${age}.`}
    >
      {yTicks.map((kg) => (
        <g key={kg}>
          <line x1={pad.l} x2={width - pad.r} y1={y(kg)} y2={y(kg)} stroke="var(--rule)" />
          <text x={pad.l - 6} y={y(kg) + 4} textAnchor="end">
            {kg}
          </text>
        </g>
      ))}
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
      <line x1={x(age)} x2={x(age)} y1={pad.t} y2={height - pad.b} stroke="var(--accent)" strokeDasharray="3 4" opacity={0.6} />
      <circle cx={x(age)} cy={y(force)} r={7} fill="var(--accent)" stroke="var(--surface)" strokeWidth={2.5} />
      <text
        x={x(age) + (age > 75 ? -12 : 12)}
        y={y(force) - 10}
        textAnchor={age > 75 ? "end" : "start"}
        style={{ fill: "var(--ink)", fontWeight: 500 }}
      >
        {force.toFixed(1)} kg
      </text>
    </svg>
  );
}

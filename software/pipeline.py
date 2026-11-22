"""
pipeline.py - the host-side data pipeline for the dynamometer, as testable functions.

    firmware lines -> parse -> stream checks -> (calibration) -> kg / N / lb -> session log

Pieces:
    parse_firmware_lines   "t_ms,raw,net,force_kg" lines -> samples, comments, skipped lines
    check_stream           sample rate, dropouts, Nano restarts, out-of-order timestamps
    rest_stats             noise and drift while nothing touches the handle
    fit_calibration        counts-per-kg line from known masses, with the G3 report numbers
    convert                kg <-> N <-> lb
    SessionLog             CSV of samples with a metadata header (calibration source, rate, units)

Honesty rule: a calibration is "measured" only when fit_calibration ran on real known-mass data.
The firmware's 42952 counts/kg is a datasheet estimate. Synthetic data must be labelled SIMULATED.
"""
from __future__ import annotations

import csv
import io
import json
import math
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone

G = 9.81                    # same value as metrics.G, so N figures match the app
LB_PER_KG = 1 / 0.45359237  # exact definition of the pound
FULL_SCALE_KG = 100.0       # rated capacity of the CZL601
DATASHEET_COUNTS_PER_KG = 42952.0


# ----------------------------------------------------------------- parsing

@dataclass
class Sample:
    t_ms: int
    raw: int | None
    net: int | None
    force_kg: float


@dataclass
class Parsed:
    samples: list[Sample] = field(default_factory=list)
    comments: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)

    @property
    def calibration(self) -> str | None:
        """'estimated' / 'measured' from the firmware's '# calibration=' boot line, if seen."""
        for c in self.comments:
            if c.lower().startswith("# calibration="):
                return c.split("=", 1)[1].split()[0].strip().lower()
        return None


def parse_firmware_lines(lines) -> Parsed:
    """Accepts the firmware's 4 columns or the simulator's 2 (t_ms,force_kg). Never raises on bad lines."""
    out = Parsed()
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("#"):
            out.comments.append(line)
            continue
        parts = [p.strip() for p in line.split(",")]
        try:
            t = int(parts[0])
            if len(parts) == 4:
                raw, net, kg = int(float(parts[1])), int(float(parts[2])), float(parts[3])
            elif len(parts) == 2:
                raw, net, kg = None, None, float(parts[1])
            else:
                raise ValueError
            if not math.isfinite(kg):
                raise ValueError
        except ValueError:
            out.skipped.append(line)
            continue
        out.samples.append(Sample(t, raw, net, kg))
    return out


# ----------------------------------------------------------------- stream checks

@dataclass
class StreamReport:
    n: int
    rate_hz: float
    median_dt_ms: float
    dropouts: int            # gaps longer than 1.5 x the median interval
    longest_gap_ms: int
    restarts: int            # timestamp jumped backwards a lot: the Nano rebooted (and re-tared!)
    out_of_order: int        # small backwards steps (should never happen)
    rfd_possible: bool       # at least 40 samples/s

    def problems(self) -> list[str]:
        p = []
        if self.restarts:
            p.append(f"{self.restarts} device restart(s): the Nano re-tares on boot, so a load applied before "
                     "the restart is now read as zero. Do not use data across a restart.")
        if self.dropouts:
            p.append(f"{self.dropouts} dropout(s), longest {self.longest_gap_ms} ms.")
        if self.out_of_order:
            p.append(f"{self.out_of_order} out-of-order timestamp(s).")
        if not self.rfd_possible:
            p.append(f"About {self.rate_hz:.0f} samples/s: RFD needs at least 40 and will be n/a.")
        return p


def check_stream(samples: list[Sample], restart_jump_ms: int = 1000) -> StreamReport:
    if len(samples) < 2:
        return StreamReport(len(samples), 0.0, 0.0, 0, 0, 0, 0, False)
    dts = [b.t_ms - a.t_ms for a, b in zip(samples, samples[1:])]
    forward = sorted(d for d in dts if d > 0)
    median = forward[len(forward) // 2] if forward else 0.0
    restarts = sum(1 for d in dts if d < -restart_jump_ms)
    out_of_order = sum(1 for d in dts if -restart_jump_ms <= d <= 0)
    gaps = [d for d in dts if median and d > 1.5 * median]
    # rate = gaps / time over the forward segments only (a restart would corrupt a plain end-start span)
    span = sum(d for d in dts if d > 0)
    rate = (len([d for d in dts if d > 0])) * 1000.0 / span if span else 0.0
    return StreamReport(len(samples), round(rate, 2), float(median), len(gaps), max(gaps, default=0),
                        restarts, out_of_order, rate >= 40)


@dataclass
class RestStats:
    mean_net: float
    sd_net: float            # noise: standard deviation AFTER removing the drift line
    drift_counts_per_s: float
    noise_kg: float          # sd_net converted with the given counts per kg


def rest_stats(samples: list[Sample], counts_per_kg: float = DATASHEET_COUNTS_PER_KG) -> RestStats:
    """Noise and drift of 'net' while nothing touches the handle (least-squares slope for drift)."""
    vals = [s.net for s in samples if s.net is not None]
    ts = [s.t_ms / 1000 for s in samples if s.net is not None]
    if len(vals) < 3:
        raise ValueError("Need at least 3 samples with raw counts.")
    n = len(vals)
    mean = sum(vals) / n
    mt = sum(ts) / n
    den = sum((t - mt) ** 2 for t in ts)
    slope = sum((t - mt) * (v - mean) for t, v in zip(ts, vals)) / den if den else 0.0
    resid = [v - (mean + slope * (t - mt)) for t, v in zip(ts, vals)]
    sd = math.sqrt(sum(r * r for r in resid) / (n - 2))      # 2 fitted parameters
    return RestStats(mean, sd, slope, sd / counts_per_kg)


# ----------------------------------------------------------------- calibration

@dataclass
class CalibrationFit:
    counts_per_kg: float
    intercept_counts: float
    r2: float
    nonlinearity_pct_fs: float
    max_residual_kg: float
    hysteresis_pct_fs: float | None
    repeatability_pct_fs: float | None
    range_kg: tuple[float, float]
    n_points: int
    n_runs: int
    curvature_counts_per_kg2: float     # quadratic term of a 2nd-order fit, for the nonlinearity check
    curvature_significant: bool         # quadratic term changes full-range reading by more than the noise
    source: str                         # "measured" only for real known masses; "simulated" otherwise

    def counts_to_kg(self, net_counts: float) -> float:
        return (net_counts - self.intercept_counts) / self.counts_per_kg

    def report(self) -> str:
        lo, hi = self.range_kg
        lines = [
            f"source: {self.source.upper()}",
            f"points: {self.n_points}   runs: {self.n_runs}   calibrated range: {lo:.2f} - {hi:.2f} kg",
            f"COUNTS_PER_KG      = {self.counts_per_kg:.4f}      <-- paste into firmware",
            f"intercept          = {self.intercept_counts:.1f} counts   (should be near 0 after tare)",
            f"R^2                = {self.r2:.6f}",
            f"max nonlinearity   = {self.nonlinearity_pct_fs:.3f} % FS   (max residual {self.max_residual_kg:.3f} kg)",
            f"hysteresis         = " + ("n/a" if self.hysteresis_pct_fs is None else f"{self.hysteresis_pct_fs:.3f} % FS"),
            f"repeatability      = " + ("n/a" if self.repeatability_pct_fs is None else f"{self.repeatability_pct_fs:.3f} % FS"),
            f"curvature          = {self.curvature_counts_per_kg2:.3f} counts/kg^2 "
            f"({'significant: consider a 2-point or curved calibration' if self.curvature_significant else 'not significant'})",
            f"(FS = {FULL_SCALE_KG:.0f} kg rated. Report only the calibrated range as validated.)",
        ]
        return "\n".join(lines)


def _polyfit(xs, ys, deg):
    """Least squares polynomial fit via normal equations (deg 1 or 2). Returns highest power first."""
    n = deg + 1
    A = [[sum(x ** (i + j) for x in xs) for j in range(n)] for i in range(n)]
    b = [sum(y * x ** i for x, y in zip(xs, ys)) for i in range(n)]
    for col in range(n):                                 # Gaussian elimination with partial pivoting
        piv = max(range(col, n), key=lambda r: abs(A[r][col]))
        A[col], A[piv] = A[piv], A[col]
        b[col], b[piv] = b[piv], b[col]
        if abs(A[col][col]) < 1e-12:
            raise ValueError("Calibration points do not span enough different masses.")
        for r in range(col + 1, n):
            f = A[r][col] / A[col][col]
            for c in range(col, n):
                A[r][c] -= f * A[col][c]
            b[r] -= f * b[col]
    coef = [0.0] * n
    for r in range(n - 1, -1, -1):
        coef[r] = (b[r] - sum(A[r][c] * coef[c] for c in range(r + 1, n))) / A[r][r]
    return list(reversed(coef))


def read_points_csv(text: str) -> list[dict]:
    """Rows of mass_kg (or mass_lb), net_counts, direction, run. Same format as calibrate.py."""
    rows = []
    for r in csv.DictReader(io.StringIO(text)):
        if (r.get("mass_kg") or "").strip():
            m = float(r["mass_kg"])
        elif (r.get("mass_lb") or "").strip():
            m = float(r["mass_lb"]) / LB_PER_KG
        else:
            continue
        if not (r.get("net_counts") or "").strip():
            continue                                     # template row not filled in yet
        rows.append({"mass_kg": m, "net_counts": float(r["net_counts"]),
                     "direction": (r.get("direction") or "up").strip().lower(), "run": int(r.get("run") or 1)})
    return rows


def fit_calibration(points: list[dict], source: str, full_scale_kg: float = FULL_SCALE_KG,
                    noise_counts: float = 70.0) -> CalibrationFit:
    """Fit counts = slope * mass + intercept. `source` must be 'measured' or 'simulated'."""
    if source not in ("measured", "simulated"):
        raise ValueError("source must be 'measured' (real known masses) or 'simulated'.")
    if len(points) < 4:
        raise ValueError("Need at least 4 calibration points.")
    m = [p["mass_kg"] for p in points]
    c = [p["net_counts"] for p in points]
    if len(set(m)) < 3:
        raise ValueError("Need at least 3 different masses.")
    slope, intercept = _polyfit(m, c, 1)
    resid = [ci - (slope * mi + intercept) for mi, ci in zip(m, c)]
    mean_c = sum(c) / len(c)
    ss_tot = sum((ci - mean_c) ** 2 for ci in c)
    r2 = 1 - sum(r * r for r in resid) / ss_tot
    fs = abs(slope * full_scale_kg)

    def by(mass, direction=None):
        return [p["net_counts"] for p in points if p["mass_kg"] == mass and (direction is None or p["direction"] == direction)]

    hyst = []
    for mass in sorted(set(m)):
        up, dn = by(mass, "up"), by(mass, "down")
        if up and dn:
            hyst.append(abs(sum(up) / len(up) - sum(dn) / len(dn)))
    reps = []
    for mass in sorted(set(m)):
        for d in ("up", "down"):
            v = by(mass, d)
            if len(v) >= 2:
                mv = sum(v) / len(v)
                reps.append(math.sqrt(sum((x - mv) ** 2 for x in v) / (len(v) - 1)))

    quad = _polyfit(m, c, 2)[0]
    span = max(m) - min(m)
    curvature_effect = abs(quad) * (span / 2) ** 2        # bow of the curve at mid-range, in counts
    return CalibrationFit(
        counts_per_kg=slope, intercept_counts=intercept, r2=r2,
        nonlinearity_pct_fs=100 * max(abs(r) for r in resid) / fs,
        max_residual_kg=max(abs(r) for r in resid) / abs(slope),
        hysteresis_pct_fs=100 * max(hyst) / fs if hyst else None,
        repeatability_pct_fs=100 * max(reps) / fs if reps else None,
        range_kg=(min(m), max(m)), n_points=len(points), n_runs=len({p["run"] for p in points}),
        curvature_counts_per_kg2=quad, curvature_significant=curvature_effect > 3 * noise_counts,
        source=source)


# ----------------------------------------------------------------- units

def convert(value: float, frm: str, to: str) -> float:
    """Convert force between 'kg' (kgf), 'N' and 'lb' (lbf)."""
    to_kg = {"kg": 1.0, "N": 1 / G, "lb": 1 / LB_PER_KG}
    if frm not in to_kg or to not in to_kg:
        raise ValueError("units must be 'kg', 'N' or 'lb'")
    return value * to_kg[frm] / to_kg[to]


def apply_calibration(samples: list[Sample], fit: CalibrationFit) -> list[float]:
    """Re-scale recorded 'net' counts with a new fit (e.g. data logged before G3 was done)."""
    return [fit.counts_to_kg(s.net) for s in samples if s.net is not None]


# ----------------------------------------------------------------- session log

class SessionLog:
    """
    A CSV of samples with a JSON metadata header line ('# meta {...}'), so a file always says how its
    forces were obtained. Read back with SessionLog.read().
    """
    COLUMNS = ["t_ms", "raw", "net", "force_kg"]

    def __init__(self, calibration: str, counts_per_kg: float, source: str, label: str = "", **extra):
        if source not in ("device", "simulated"):
            raise ValueError("source must be 'device' or 'simulated'")
        if calibration not in ("estimated", "measured"):
            raise ValueError("calibration must be 'estimated' or 'measured'")
        self.meta = {"created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                     "source": source, "calibration": calibration, "counts_per_kg": counts_per_kg,
                     "label": label, **extra}
        self.samples: list[Sample] = []

    def add(self, s: Sample):
        self.samples.append(s)

    def to_csv(self) -> str:
        buf = io.StringIO()
        buf.write("# meta " + json.dumps(self.meta, sort_keys=True) + "\n")
        w = csv.writer(buf, lineterminator="\n")
        w.writerow(self.COLUMNS)
        for s in self.samples:
            w.writerow([s.t_ms, "" if s.raw is None else s.raw, "" if s.net is None else s.net, f"{s.force_kg:.4f}"])
        return buf.getvalue()

    @staticmethod
    def read(text: str) -> tuple[dict, list[Sample]]:
        lines = text.splitlines()
        if not lines or not lines[0].startswith("# meta "):
            raise ValueError("Not a session log: the first line must be '# meta {...}'.")
        meta = json.loads(lines[0][len("# meta "):])
        samples = []
        for r in csv.DictReader(lines[1:]):
            samples.append(Sample(int(r["t_ms"]), int(r["raw"]) if r["raw"] else None,
                                  int(r["net"]) if r["net"] else None, float(r["force_kg"])))
        return meta, samples


def asdict_fit(fit: CalibrationFit) -> dict:
    return asdict(fit)

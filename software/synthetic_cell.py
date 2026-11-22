"""
synthetic_cell.py - a documented, deterministic model of the CZL601 + HX711 + firmware, for testing.

[SIMULATED] Nothing produced here is a measurement. It exists so the calibration and analysis code
can be tested against data whose true answers are known.

Where each default comes from:
    rest_raw = 52_400     G1 bench test, 2026-11-06: rest about +52,400 raw counts
    noise_counts = 70     G1 bench test: noise about +/-70 counts (treated here as 1 standard deviation)
    counts_per_kg = 42952 datasheet estimate in the firmware (2.0 mV/V x 5 V, gain 128, 100 kg)
    rate_hz = 10          HX711 RATE pin low (current hardware); 80 after the RATE mod
    sign = -1             this cell reads negative under load; the firmware multiplies by SIGN = -1
    nonlinearity, hysteresis, drift: assumed small values, chosen to be visible in tests.
        Real values are unknown until the G3 known-mass calibration.

The model, for an applied mass m (kg) at time t (s):
    net(t) = round( k*m*(1 + a*m/FS) + h(m) + drift*t + noise )
    raw(t) = rest_raw + sign * net(t)
    force_kg = net / counts_per_kg_firmware          (what the firmware prints)
where k = true counts per kg, a = nonlinearity coefficient, FS = 100 kg, and h is a hysteresis offset
that is +h0*m/FS while loading and -h0*m/FS while unloading.

Lines are printed exactly like firmware/grip_firmware_tillaart: "t_ms,raw,net,force_kg" with
whole-millisecond timestamps, plus "#" comment lines at boot and after a tare.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

FULL_SCALE_KG = 100.0
FIRMWARE_COUNTS_PER_KG = 42952.0


@dataclass
class CellModel:
    true_counts_per_kg: float = 44_100.0   # deliberately not the firmware value: calibration must find it
    rest_raw: int = 52_400
    noise_counts: float = 70.0
    rate_hz: float = 10.0
    sign: int = -1
    nonlinearity: float = 0.002            # a: +0.2 % of reading at full scale
    hysteresis_counts_fs: float = 300.0    # h0: offset at full scale, + loading / - unloading
    drift_counts_per_s: float = 0.0
    firmware_counts_per_kg: float = FIRMWARE_COUNTS_PER_KG
    seed: int = 1
    _rng: random.Random = field(init=False, repr=False)

    def __post_init__(self):
        self._rng = random.Random(self.seed)

    # ---- the physics, without noise ----
    def ideal_net(self, mass_kg: float, loading: bool = True) -> float:
        k, a = self.true_counts_per_kg, self.nonlinearity
        hyst = self.hysteresis_counts_fs * mass_kg / FULL_SCALE_KG
        return k * mass_kg * (1 + a * mass_kg / FULL_SCALE_KG) + (hyst if loading else -hyst)

    # ---- one sample, as the firmware would print it ----
    def sample(self, mass_kg: float, t_s: float, loading: bool = True) -> tuple[int, int, float]:
        net = round(self.ideal_net(mass_kg, loading) + self.drift_counts_per_s * t_s
                    + self._rng.gauss(0.0, self.noise_counts))
        raw = self.rest_raw + self.sign * net
        return raw, net, net / self.firmware_counts_per_kg

    def stream(self, masses_kg, start_ms: int = 1234, loading=None, boot=False) -> list[str]:
        """Firmware lines for a sequence of applied masses, one mass per sample."""
        lines = []
        if boot:
            lines += ["# hand_dynamometer_v1", "# calibration=estimated (datasheet, about +/-10 %)",
                      "t_ms,raw,net,force_kg"]
        dt = 1000.0 / self.rate_hz
        for i, m in enumerate(masses_kg):
            t_ms = start_ms + int(round(i * dt))
            load = True if loading is None else loading[i]
            raw, net, kg = self.sample(m, (t_ms - start_ms) / 1000.0, load)
            lines.append(f"{t_ms},{raw},{net},{kg:.3f}")
        return lines


def staircase(model: CellModel, plan_kg, hold_s: float = 10.0, runs: int = 3, settle_s: float = 2.0):
    """
    A G3-style calibration session: up the plan, back down (skipping the top step), repeated `runs`
    times. Returns (points, lines): `points` are dicts like a filled calibration_points.csv row, using
    the mean 'net' of the last `settle_s` seconds of each hold; `lines` is the full firmware stream.
    """
    n = int(hold_s * model.rate_hz)
    last = int(settle_s * model.rate_hz)
    up = list(plan_kg)
    sequence = [(m, "up") for m in up] + [(m, "down") for m in reversed(up[:-1])]
    points, lines, t0 = [], [], 1234
    for run in range(1, runs + 1):
        for mass, direction in sequence:
            block = model.stream([mass] * n, start_ms=t0, loading=[direction == "up"] * n)
            t0 += int(n * 1000 / model.rate_hz)
            nets = [int(line.split(",")[2]) for line in block[-last:]]
            points.append({"mass_kg": mass, "net_counts": sum(nets) / len(nets), "direction": direction, "run": run})
            lines += block
    return points, lines


def squeeze_profile(peak_kg: float, seconds: float, rate_hz: float, kind: str = "max") -> list[float]:
    """Applied force over time for a simulated squeeze: 'max' (5 s) or 'hold' (30 s decaying hold)."""
    import math
    out = []
    for i in range(int(seconds * rate_hz)):
        t = i / rate_hz
        if kind == "max":
            f = 0.0 if t < 0.5 or t > 3.5 else peak_kg * (1 - math.exp(-(t - 0.5) / 0.15)) * (1 - 0.03 * (t - 0.5))
        else:
            f = 0.0 if t < 1 or t > 31 else peak_kg * (1 - math.exp(-(t - 1) / 0.2)) * (0.5 + 0.5 * math.exp(-(t - 1) / 15))
        out.append(max(0.0, f))
    return out

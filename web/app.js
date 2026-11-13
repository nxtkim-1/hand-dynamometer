// GripCheck - browser side.
// The server (webapp.py) does all the maths; this file shows screens, runs the 3-2-1 countdown
// and draws the live graph. The points come either from the server (simulator, or a device
// plugged into the server) or, with Web Serial, straight from a device plugged into THIS computer.

const $ = (id) => document.getElementById(id);
// colours and the font come from web/tokens.css, so the graph always matches the page
const css = getComputedStyle(document.documentElement);
const token = (name) => css.getPropertyValue(name).trim();
const COLORS = { right: token("--color-right"), left: token("--color-left"), fatigue: token("--color-fatigue") };
const INK = { muted: token("--color-muted"), rule: token("--color-rule"), font: token("--font-body") };

const app = {
  config: null,
  sid: null,         // this visitor's test id, sent with every request
  plan: [],
  index: 0,          // which step of the plan we are on
  points: [],        // points of the trial being recorded: {t (ms), f (kg)}
  traces: {},        // finished trials, kept to draw faintly behind the next one
  flags: {},         // steps whose quality was not "good"
  phase: "idle",     // idle | countdown | recording | resting | done
  restTimer: null,
  device: null,      // Web Serial connection: { port, onLine } (Chrome / Edge only)
  restSeconds: null, // rest length for this test, given by the server
};

// ---------- small helpers ----------

function show(screenId) {
  for (const s of document.querySelectorAll(".screen")) s.hidden = s.id !== screenId;
}

async function api(path, body) {
  const res = await fetch(path, body === undefined ? {} : {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Something went wrong.");
  return data;
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const cap = (s) => s[0].toUpperCase() + s.slice(1);

function stepColor(step) {
  return step.test === "fatigue" ? COLORS.fatigue : COLORS[step.hand];
}

// ---------- progress pills ----------

function renderProgress() {
  const list = $("progress");
  list.hidden = false;
  list.innerHTML = "";
  app.plan.forEach((step, i) => {
    const li = document.createElement("li");
    li.textContent = step.test === "fatigue" ? "30 s" : `${step.hand[0].toUpperCase()}${step.trial}`;
    li.title = step.test === "fatigue" ? "Fatigue test" : `${cap(step.hand)} hand, trial ${step.trial}`;
    if (i < app.index || (i === app.index && app.phase === "resting")) li.className = app.flags[i] ? "flag" : "done";
    if (i === app.index && app.phase !== "resting") { li.className = "current"; li.setAttribute("aria-current", "step"); }
    list.appendChild(li);
  });
}

// ---------- chart (plain canvas, no library) ----------

function drawChart() {
  const canvas = $("chart");
  const step = app.plan[app.index];
  const dpr = window.devicePixelRatio || 1;
  const w = canvas.clientWidth, h = canvas.clientHeight;
  if (canvas.width !== w * dpr) { canvas.width = w * dpr; canvas.height = h * dpr; }
  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, w, h);

  const pad = { l: 48, r: 16, t: 16, b: 34 };
  const peak = Math.max(0, ...app.points.map((p) => p.f));
  const yMax = Math.max(40, Math.ceil((peak * 1.15) / 10) * 10);
  const xMax = step.seconds;
  const x = (s) => pad.l + (s / xMax) * (w - pad.l - pad.r);
  const y = (kg) => h - pad.b - (Math.max(0, kg) / yMax) * (h - pad.t - pad.b);

  // grid and labels
  ctx.font = `12px ${INK.font}`;
  ctx.fillStyle = INK.muted; ctx.strokeStyle = INK.rule; ctx.lineWidth = 1;
  const yStep = yMax > 100 ? 20 : 10;
  for (let kg = 0; kg <= yMax; kg += yStep) {
    ctx.beginPath(); ctx.moveTo(pad.l, y(kg)); ctx.lineTo(w - pad.r, y(kg)); ctx.stroke();
    ctx.textAlign = "right"; ctx.fillText(kg, pad.l - 8, y(kg) + 4);
  }
  const xStep = xMax > 10 ? 5 : 1;
  for (let s = 0; s <= xMax; s += xStep) {
    ctx.textAlign = "center"; ctx.fillText(`${s}s`, x(s), h - pad.b + 18);
  }
  ctx.save(); ctx.translate(14, (h - pad.b) / 2); ctx.rotate(-Math.PI / 2);
  ctx.textAlign = "center"; ctx.fillText("Force (kg)", 0, 0); ctx.restore();

  // earlier trials of the same hand and test, drawn faintly for comparison
  for (const [i, trace] of Object.entries(app.traces)) {
    const other = app.plan[i];
    if (Number(i) === app.index || other.hand !== step.hand || other.test !== step.test) continue;
    ctx.globalAlpha = 0.3; line(ctx, trace, x, y, INK.muted, 1.5); ctx.globalAlpha = 1;
  }

  if (app.points.length < 2) return;
  const color = stepColor(step);
  // area under the live curve
  ctx.beginPath(); ctx.moveTo(x(app.points[0].t / 1000), y(0));
  for (const p of app.points) ctx.lineTo(x(p.t / 1000), y(p.f));
  ctx.lineTo(x(app.points[app.points.length - 1].t / 1000), y(0)); ctx.closePath();
  ctx.fillStyle = color; ctx.globalAlpha = 0.12; ctx.fill(); ctx.globalAlpha = 1;
  line(ctx, app.points, x, y, color, 2.5);

  // peak marker
  const top = app.points.reduce((a, b) => (b.f > a.f ? b : a));
  ctx.fillStyle = color;
  ctx.beginPath(); ctx.arc(x(top.t / 1000), y(top.f), 5, 0, Math.PI * 2); ctx.fill();
  ctx.textAlign = "left"; ctx.font = `600 13px ${INK.font}`;
  ctx.fillText(`${top.f.toFixed(1)} kg`, Math.min(x(top.t / 1000) + 8, w - 70), y(top.f) - 8);
}

function line(ctx, pts, x, y, color, width) {
  ctx.beginPath();
  pts.forEach((p, i) => (i ? ctx.lineTo : ctx.moveTo).call(ctx, x(p.t / 1000), y(p.f)));
  ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineJoin = "round"; ctx.stroke();
}

let drawQueued = false;
function requestDraw() {
  if (drawQueued) return;
  drawQueued = true;
  requestAnimationFrame(() => { drawQueued = false; drawChart(); });
}
window.addEventListener("resize", () => { if (app.plan.length) requestDraw(); });

// ---------- trial flow ----------

function setPrimary(text, enabled = true) {
  const b = $("btn-primary");
  b.textContent = text; b.disabled = !enabled; b.hidden = false;
}

function showTrial() {
  const step = app.plan[app.index];
  app.phase = "idle";
  app.points = [];
  renderProgress();
  show("screen-trial");

  const isFatigue = step.test === "fatigue";
  const perHand = app.plan.filter((s) => s.test === "max").length / 2;
  $("trial-eyebrow").textContent = isFatigue ? "Fatigue test" : `Maximal grip, trial ${step.trial} of ${perHand}`;
  $("trial-title").textContent = isFatigue
    ? `Squeeze and hold for 30 seconds` : `Squeeze as hard as you can`;
  const chip = $("hand-chip");
  chip.textContent = `${cap(step.hand)} hand`;
  chip.className = `hand-chip ${isFatigue ? "fatigue" : step.hand}`;

  $("posture").innerHTML = app.config.prompt_posture.replace(/\.$/, "").split(", ")
    .map((p) => `<li>${cap(p)}</li>`).join("");

  $("live-force").textContent = "0.0";
  $("live-peak").textContent = "0.0";
  $("live-left").textContent = step.seconds;
  $("go-text").hidden = true;
  $("trial-result").hidden = true;
  $("trial-error").hidden = true;
  $("btn-repeat").hidden = true;
  $("rest").hidden = true;
  setPrimary("I’m ready");
  $("chart").setAttribute("aria-label", "Force over time. The graph fills in while you squeeze.");
  requestDraw();
  $("btn-primary").focus();
}

async function runTrial() {
  const step = app.plan[app.index];
  app.phase = "countdown";
  app.points = [];
  $("btn-repeat").hidden = true;
  $("trial-result").hidden = true;
  $("trial-error").hidden = true;
  setPrimary("Recording...", false);
  requestDraw();

  const overlay = $("overlay");
  overlay.hidden = false; overlay.classList.remove("go");
  for (const n of [3, 2, 1]) { overlay.textContent = n; await sleep(1000); }
  overlay.textContent = "Squeeze!"; overlay.classList.add("go");
  setTimeout(() => { overlay.hidden = true; }, 600);

  $("go-text").textContent = step.test === "fatigue" ? app.config.prompt_fatigue : app.config.prompt_go;
  $("go-text").hidden = false;
  app.phase = "recording";

  if (app.source === "browser") return recordFromDevice(step);

  const stream = new EventSource(`/api/${app.sid}/step/${app.index}/stream`);
  let peak = 0;
  stream.addEventListener("point", (e) => {
    const p = JSON.parse(e.data);
    app.points.push(p);
    peak = Math.max(peak, p.f);
    $("live-force").textContent = p.f.toFixed(1);
    $("live-peak").textContent = peak.toFixed(1);
    $("live-left").textContent = Math.max(0, step.seconds - p.t / 1000).toFixed(0);
    requestDraw();
  });
  stream.addEventListener("done", (e) => { stream.close(); finishTrial(JSON.parse(e.data)); });
  stream.addEventListener("failed", (e) => { stream.close(); failTrial(JSON.parse(e.data).message); });
  stream.onerror = () => {   // stream ended without "done": never let the browser silently retry
    if (app.phase === "recording") { stream.close(); failTrial("The connection to the device was lost."); }
  };
}

function finishTrial(result) {
  const step = app.plan[app.index];
  app.traces[app.index] = app.points.slice();
  $("go-text").hidden = true;
  $("live-left").textContent = "0";
  $("chart").setAttribute("aria-label", `Force over time. Peak ${result.peak_kg} kg, reached after ${result.time_to_peak_ms} ms.`);

  const chips = [`<span class="chip">Peak (filtered) <b>${result.peak_kg}</b> kg</span>`,
                 `<span class="chip">Time to peak <b>${result.time_to_peak_ms}</b> ms</span>`,
                 `<span class="chip">RFD <b>${result.rfd_n_per_s}</b> N/s</span>`];
  if (step.test === "fatigue") chips.push(`<span class="chip">Fatigue index <b>${result.fatigue_index_pct}</b> %</span>`);

  let notice = "";
  const flagged = result.quality && result.quality !== "good";
  app.flags[app.index] = flagged;
  if (flagged) {
    const why = { false_start: "the squeeze started before the countdown ended",
                  slip: "the force dropped suddenly, as if the hand slipped",
                  submaximal: "the force rose slowly, which suggests less than full effort" }[result.quality];
    notice = `<div class="notice"><b>This trial may not be valid:</b> ${why}. You can repeat it after resting.</div>`;
  } else if (result.quality === "good") {
    notice = `<div class="notice ok">Good trial.</div>`;
  }
  for (const n of result.notes) notice += `<div class="notice">${n}</div>`;
  $("trial-result").innerHTML = `<div class="chips">${chips.join("")}</div>${notice}`;
  $("trial-result").hidden = false;

  const last = app.index === app.plan.length - 1;
  if (last) {
    app.phase = "done";
    renderProgress();
    setPrimary("See my report");
    $("btn-primary").focus();
    return;
  }
  $("btn-repeat").hidden = false;
  startRest(flagged);
}

function failTrial(message) {
  app.phase = "idle";
  $("go-text").hidden = true;
  $("trial-error").textContent = message;
  $("trial-error").hidden = false;
  setPrimary("Try again");
}

function startRest(flagged) {
  app.phase = "resting";
  renderProgress();
  let left = app.restSeconds ?? app.config.rest_seconds;
  const nextStep = app.plan[app.index + 1];
  const nextLabel = nextStep.test === "fatigue" ? "Start fatigue test" : `Next: ${nextStep.hand} hand`;
  const tick = () => {
    $("rest-left").textContent = left;
    const ready = left <= 0;
    $("rest").hidden = ready;
    setPrimary(ready ? nextLabel : "Resting...", ready);
    $("btn-repeat").disabled = !ready;
    $("btn-repeat").className = `btn ${flagged ? "primary" : "secondary"}`;
    if (ready) { clearInterval(app.restTimer); (flagged ? $("btn-repeat") : $("btn-primary")).focus(); }
    left -= 1;
  };
  clearInterval(app.restTimer);
  tick();
  app.restTimer = setInterval(tick, 1000);
}

$("btn-skip").addEventListener("click", () => {
  clearInterval(app.restTimer);
  const flagged = app.flags[app.index];
  $("rest").hidden = true;
  const nextStep = app.plan[app.index + 1];
  setPrimary(nextStep.test === "fatigue" ? "Start fatigue test" : `Next: ${nextStep.hand} hand`);
  $("btn-repeat").disabled = false;
  (flagged ? $("btn-repeat") : $("btn-primary")).focus();
});

$("btn-primary").addEventListener("click", async () => {
  if (app.phase === "idle") return runTrial();
  if (app.phase === "resting") { clearInterval(app.restTimer); app.index += 1; return showTrial(); }
  if (app.phase === "done") return finish();
});

$("btn-repeat").addEventListener("click", () => {
  clearInterval(app.restTimer);
  delete app.traces[app.index];
  showTrial();
});

// Enter = press the highlighted button, like pressing Enter in the terminal version
document.addEventListener("keydown", (e) => {
  if (e.key !== "Enter" || e.target.closest("form")) return;
  const focused = document.activeElement;
  if (focused && focused.tagName === "BUTTON") return;   // the browser already clicks it
  const b = $("btn-primary");
  if (!$("screen-trial").hidden && !b.disabled && !b.hidden) b.click();
});


// ---------- device in this browser (Web Serial) ----------
// The firmware prints "t_ms,raw,net,force_kg" lines at 115200 baud and re-zeroes on "T".

function parseLine(line) {           // same rule as parse_line() in grip_test.py
  const parts = line.split(",");
  if (parts.length < 2 || !/^-?\d+$/.test(parts[0].trim())) return null;
  const t = parseInt(parts[0], 10), f = parseFloat(parts[parts.length - 1]);
  return Number.isFinite(t) && Number.isFinite(f) ? { t, f } : null;
}

async function readLines(port) {
  const decoder = new TextDecoderStream();
  port.readable.pipeTo(decoder.writable).catch(() => {});
  const reader = decoder.readable.getReader();
  let buffer = "";
  try {
    for (;;) {
      const { value, done } = await reader.read();
      if (done) break;
      buffer += value;
      let cut;
      while ((cut = buffer.indexOf("\n")) >= 0) {
        const line = buffer.slice(0, cut).trim();
        buffer = buffer.slice(cut + 1);
        if (app.device && app.device.onLine) app.device.onLine(line);
      }
    }
  } catch (err) { /* unplugged: handled by the disconnect event */ }
}

async function sendToDevice(text) {
  const writer = app.device.port.writable.getWriter();
  try { await writer.write(new TextEncoder().encode(text)); } finally { writer.releaseLock(); }
}

function deviceLost() {
  app.device = null;
  $("device-status").textContent = "Device disconnected.";
  $("btn-device").hidden = false;
  setBadge();
  if (app.phase === "recording" || app.phase === "countdown") failTrial("The device was unplugged.");
}

async function connectDevice() {
  const status = $("device-status");
  try {
    const port = await navigator.serial.requestPort();
    await port.open({ baudRate: app.config.baud });
    app.device = { port, onLine: null };
    readLines(port);
    $("btn-device").hidden = true;
    status.textContent = "Starting the device...";
    await sleep(2500);                           // opening the port restarts the Nano
    status.textContent = "Device connected. Your squeezes will be measured, not simulated.";
    setBadge();
  } catch (err) {
    if (err.name !== "NotFoundError") status.textContent = `Could not connect: ${err.message}`;
  }
}

async function tareDevice() {
  app.device.onLine = null;
  await sendToDevice("T");
  await sleep(2500);                             // the firmware averages 20 readings
}

// Record one trial from the device for step.seconds, drawing it live, then upload it.
async function recordFromDevice(step) {
  const lines = [];
  let first = null, peak = 0;
  app.device.onLine = (line) => {
    lines.push(line);
    const p = parseLine(line);
    if (!p) return;
    if (first === null) first = p.t;
    const point = { t: p.t - first, f: p.f };
    app.points.push(point);
    peak = Math.max(peak, point.f);
    $("live-force").textContent = point.f.toFixed(1);
    $("live-peak").textContent = peak.toFixed(1);
    requestDraw();
  };
  const started = performance.now();
  while (app.device && performance.now() - started < step.seconds * 1000) {
    $("live-left").textContent = Math.max(0, step.seconds - (performance.now() - started) / 1000).toFixed(0);
    await sleep(100);
  }
  if (!app.device) return;                       // unplugged: deviceLost() already reported it
  app.device.onLine = null;
  try { finishTrial(await api(`/api/${app.sid}/step/${app.index}/upload`, { lines })); }
  catch (err) { failTrial(err.message); }
}

function setBadge() {
  const badge = $("mode-badge");
  const real = app.device || !app.config.use_fake;
  badge.hidden = false;
  badge.textContent = app.device ? "Device connected" : app.config.demo ? "Online demo"
    : app.config.use_fake ? "Simulated data" : "Device connected";
  badge.classList.toggle("device", Boolean(real));
  const cal = $("cal-note");
  cal.hidden = !(real && app.config.calibration !== "measured");
  cal.innerHTML = `<b>Estimated calibration.</b> ${app.config.calibration_note}`;
}

$("btn-device").addEventListener("click", connectDevice);

// ---------- start, details form, zeroing, finish ----------

$("btn-welcome").addEventListener("click", () => { show("screen-form"); document.querySelector("[name=age]").focus(); });

$("user-form").addEventListener("input", () => { $("form-error").hidden = true; });

$("user-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = new FormData(e.target);
  const body = Object.fromEntries(form.entries());
  body.injury = form.has("injury");
  if (app.device) body.source = "browser";
  $("form-error").hidden = true;
  $("btn-form").disabled = true;
  try {
    const data = await api("/api/start", body);
    app.sid = data.session_id; app.plan = data.plan; app.index = 0; app.traces = {}; app.flags = {};
    app.source = data.source; app.restSeconds = data.rest_seconds;
    if (data.needs_tare) { show("screen-tare"); $("btn-tare").focus(); }
    else showTrial();
  } catch (err) {
    $("form-error").textContent = err.message; $("form-error").hidden = false;
  } finally {
    $("btn-form").disabled = false;
  }
});

$("btn-tare").addEventListener("click", async () => {
  const b = $("btn-tare");
  b.disabled = true; b.textContent = "Zeroing... do not touch";
  try {
    if (app.source === "browser") {
      if (!app.device) throw new Error("The device is not connected. Reload the page and connect it again.");
      await tareDevice();
    } else {
      await api(`/api/${app.sid}/tare`, {});
    }
    showTrial();
  }
  catch (err) { $("tare-error").textContent = err.message; $("tare-error").hidden = false; }
  finally { b.disabled = false; b.textContent = "Zero now"; }
});

async function finish() {
  show("screen-finish");
  $("progress").hidden = true;
  try {
    const data = await api(`/api/${app.sid}/finish`, {});
    window.location.href = data.report_url;
  } catch (err) {
    $("finish-error").textContent = err.message; $("finish-error").hidden = false;
  }
}

(async function init() {
  app.config = await api("/api/config");
  if (app.config.demo) $("demo-note").hidden = false;
  setBadge();
  // offer a device in this browser only when the server is not already reading one
  if (app.config.browser_device && app.config.use_fake) {
    $("device-box").hidden = false;
    if ("serial" in navigator) {
      navigator.serial.addEventListener("disconnect", (e) => { if (app.device && e.target === app.device.port) deviceLost(); });
    } else {
      $("btn-device").hidden = true;
      $("device-status").textContent = "To use the device, open this page in Chrome or Edge on a computer.";
    }
  }
})();

"""
webapp.py - Browser version of the grip test.

Run:   python webapp.py        (a browser tab opens at http://localhost:8000)

The protocol, metrics, filtering, quality check, saving and report are the SAME code
as grip_test.py. Only the interaction changes: buttons, a countdown and a live graph
in the browser instead of typing in the terminal.

How the live graph works (Server-Sent Events):
  the browser opens /api/step/<n>/stream and keeps the connection open;
  every new force sample is sent down that connection as one small message,
  and the page redraws the graph each time a message arrives.
"""

import json
import threading
import time
import webbrowser
from datetime import datetime
from pathlib import Path

import matplotlib
matplotlib.use("Agg")   # draw figures to files only: a web server must never open plot windows (it can freeze on macOS)

from flask import Flask, Response, jsonify, request, send_from_directory

import fake_data
import filters
import grip_test
import metrics
import quality
from grip_compare import assess, plot_on_centiles
from report import fmt, make_report

WEB_DIR = Path(__file__).parent / "web"
HOST, PORT_NUMBER = "127.0.0.1", 8000          # 127.0.0.1 = only this computer can open the app
                                              # (not 5000: macOS AirPlay already uses that port)
PLAYBACK_DELAY = 1 / fake_data.SAMPLE_RATE_HZ   # play simulated curves at real speed (tests set 0)

app = Flask(__name__, static_folder=None)
state = {}   # the one test currently running on this computer


# ---------- helpers -------------------------------------------------------

def build_plan(dominant):
    """Same order as the terminal app: alternate hands 3 times, then the fatigue test."""
    other = "left" if dominant == "right" else "right"
    plan = []
    for trial in range(1, grip_test.TRIALS_PER_HAND + 1):
        for hand in [dominant, other]:
            plan.append({"hand": hand, "trial": trial, "test": "max",
                         "seconds": grip_test.TRIAL_SECONDS})
    plan.append({"hand": dominant, "trial": 1, "test": "fatigue",
                 "seconds": grip_test.FATIGUE_SECONDS})
    return plan


def read_number(data, key, low, high, required):
    """Return a number from the form, None if optional and empty, or raise ValueError."""
    value = data.get(key)
    if value in (None, ""):
        if required:
            raise ValueError(f"Please enter {key.replace('_', ' ')}.")
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"{key.replace('_', ' ').capitalize()} must be a number.")
    if not low <= number <= high:
        raise ValueError(f"{key.replace('_', ' ').capitalize()} must be between {low} and {high}.")
    return number


def read_user(data):
    """Check every form field. The same limits as the terminal app, plus optional extras."""
    age = read_number(data, "age", 5, 100, required=True)
    if age != int(age):
        raise ValueError("Age must be a whole number.")
    sex = str(data.get("sex", "")).lower()
    dominant = str(data.get("dominant", "")).lower()
    if sex not in ("male", "female"):
        raise ValueError("Please choose male or female (the normative data are reported by sex).")
    if dominant not in ("right", "left"):
        raise ValueError("Please choose the dominant hand.")
    return {
        "age": int(age), "sex": sex, "dominant": dominant,
        "participant_id": str(data.get("participant_id", "")).strip()[:40],
        "height_cm": read_number(data, "height_cm", 100, 230, required=False),
        "weight_kg": read_number(data, "weight_kg", 20, 250, required=False),
        "injury": bool(data.get("injury")),
    }


def live_lines(ser, hand, test, seconds):
    """Yield text lines in real time, from the simulator or from the Arduino."""
    if ser is None:
        for line in fake_data.make_lines(hand, test, seconds):
            time.sleep(PLAYBACK_DELAY)
            yield line
    else:
        ser.reset_input_buffer()
        start = time.time()
        while time.time() - start < seconds:
            yield ser.readline().decode(errors="ignore").strip()


def sse(event, data):
    """Format one Server-Sent Event message."""
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def close_serial():
    ser = state.get("ser")
    if ser is not None:
        ser.close()
        state["ser"] = None


# ---------- pages ---------------------------------------------------------

@app.get("/")
def home():
    return send_from_directory(WEB_DIR, "index.html")


@app.get("/web/<path:name>")
def web_files(name):
    return send_from_directory(WEB_DIR, name)


@app.get("/report")
@app.get("/report/<path:name>")
def report_page(name=None):
    """Short addresses for reports: /report is the newest, /report/<date_time> a specific one.
    The report's pictures are requested as /report/session_....png and served from the same folder."""
    folder = grip_test.SESSIONS_DIR
    if name is None:
        reports = sorted(folder.glob("session_*_report.html"))
        if not reports:
            return "No reports yet - run a test first.", 404
        name = reports[-1].name
    elif not name.startswith("session_"):
        name = f"session_{name}_report.html"
    # send_from_directory refuses paths like ../../ so only the sessions folder is reachable
    return send_from_directory(folder, name)


# ---------- API -----------------------------------------------------------

@app.get("/api/config")
def config():
    return jsonify({
        "use_fake": grip_test.USE_FAKE,
        "rest_seconds": grip_test.REST_SECONDS,
        "prompt_posture": grip_test.PROMPT_POSTURE,
        "prompt_go": grip_test.PROMPT_GO,
        "prompt_fatigue": grip_test.PROMPT_FATIGUE,
    })


@app.post("/api/start")
def start():
    try:
        user = read_user(request.get_json(force=True) or {})
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    close_serial()
    ser = None
    if not grip_test.USE_FAKE:
        try:
            ser = grip_test.connect_serial()
        except RuntimeError as e:
            return jsonify({"error": str(e)}), 400

    state.clear()
    state.update({
        "stamp": datetime.now().strftime("%Y-%m-%d_%H-%M-%S"),
        "user": user,
        "plan": build_plan(user["dominant"]),
        "results": {},
        "ser": ser,
    })
    return jsonify({"plan": state["plan"], "needs_tare": ser is not None})


@app.post("/api/tare")
def do_tare():
    if state.get("ser") is None:
        return jsonify({"error": "No device connected."}), 400
    grip_test.tare(state["ser"])
    return jsonify({"ok": True})


@app.get("/api/step/<int:index>/stream")
def stream_step(index):
    if "plan" not in state or not 0 <= index < len(state["plan"]):
        return jsonify({"error": "Start a test first."}), 400
    step = state["plan"][index]

    def events():
        readings, skipped, first_ms = [], [], None
        for line in live_lines(state["ser"], step["hand"], step["test"], step["seconds"]):
            parsed = grip_test.parse_line(line)
            if parsed is None:
                if line:
                    skipped.append(line)
                continue
            time_ms, force_kg = parsed
            if first_ms is None:
                first_ms = time_ms
            point = {"time_ms": time_ms - first_ms, "force_kg": force_kg}
            readings.append(point)
            yield sse("point", {"t": point["time_ms"], "f": round(force_kg, 2)})

        if not readings:
            hint = f" First non-data line: {skipped[0]!r}" if skipped else ""
            yield sse("failed", {"message": "No data received - check the USB cable and PORT." + hint})
            return

        notes = []
        rate = filters.estimate_rate_hz(readings)
        if rate < grip_test.MIN_RATE_HZ:
            notes.append(f"Data arrived at about {rate:.0f} samples/s; RFD needs at least "
                         f"{grip_test.MIN_RATE_HZ} and is reported as n/a.")
        try:
            grip_test.check_recording(readings, warned=True)   # calibration check (rate shown above)
        except RuntimeError as e:
            yield sse("failed", {"message": str(e)})
            return

        smooth = filters.filter_readings(readings)
        m = metrics.trial_metrics(smooth)
        result = {"hand": step["hand"], "trial": step["trial"], "test": step["test"],
                  "readings": readings, "smooth": smooth, "metrics": m}
        if step["test"] == "max":
            result["quality"] = quality.check_trial(smooth)["label"]
        else:
            m["fatigue_index_pct"] = metrics.fatigue_index_pct(smooth)
        state["results"][index] = result      # repeating a trial simply replaces it

        yield sse("done", {
            "peak_kg": fmt(m["peak_kg"]),
            "time_to_peak_ms": m["time_to_peak_ms"],
            "rfd_n_per_s": fmt(m["rfd_n_per_s"], 0),
            "fatigue_index_pct": fmt(m.get("fatigue_index_pct")),
            "quality": result.get("quality"),
            "notes": notes,
        })

    return Response(events(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@app.post("/api/finish")
def finish():
    plan = state.get("plan")
    if not plan or len(state["results"]) != len(plan):
        return jsonify({"error": "Not every trial has been recorded yet."}), 400
    close_serial()

    results = [state["results"][i] for i in range(len(plan))]
    trials, fatigue = results[:-1], results[-1]
    stamp, user = state["stamp"], state["user"]
    folder = grip_test.SESSIONS_DIR

    summary = grip_test.summarize(trials, fatigue)
    grip_test.save_session(stamp, trials, fatigue, summary)     # save first, as in the terminal app
    result = assess(summary["overall_peak_kg"], user["age"], user["sex"])
    plot_on_centiles(result, save_path=folder / f"session_{stamp}_centiles.png", show=False)
    report = make_report(stamp, user, trials, folder, grip_test.USE_FAKE,
                         fatigue=fatigue, summary=summary, result=result,
                         open_browser=False, home_url="/")
    return jsonify({"report_url": f"/report/{stamp}"})


if __name__ == "__main__":
    url = f"http://localhost:{PORT_NUMBER}"
    print(f"GripCheck is running at {url}  (press Ctrl+C here to stop)")
    threading.Timer(1.0, lambda: webbrowser.open(url)).start()
    app.run(host=HOST, port=PORT_NUMBER, threaded=True)

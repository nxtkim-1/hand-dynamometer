import csv
import random
import time
import fake_data
import metrics
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from grip_compare import assess, print_report, plot_on_centiles
from datetime import datetime


USE_FAKE = True
PORT = "/dev/cu.usbserial-XXXX"
BAUD = 115200 #match with arduino code

TRIALS_PER_HAND = 3
TRIAL_SECONDS = 5
FATIGUE_SECONDS = 32
REST_SECONDS = 3 if USE_FAKE else 60

SESSIONS_DIR = Path(__file__).parent / "sessions"

PROMPT_POSTURE = "Sit upright, elbow at 90 degrees, forearm neutral, wrist straight."
PROMPT_GO = "Squeeze as hard as you can! Harder... harder... harder..."
PROMPT_FATIGUE = "Squeeze as hard as you can and KEEP squeezing for 30 seconds!"

def ask_user_info():
    age = int(input("Enter age:"))
    sex = input("Enter sex (male/female): ").strip().lower() #strip = erase space, lower = make it lower case
    while sex not in ("male", "female"):
        sex = input("Please type male or female: ").strip().lower()
    dominant = input("Dominant hand (right/left): ").strip().lower()
    while dominant not in ("right", "left"):
        dominant = input("Please type right or left: ").strip().lower()
    return age, sex, dominant

def open_serial():
    import serial                       # arduino data
    ser = serial.Serial(PORT, BAUD, timeout=1) #이 줄이 실제로 Arduino와 연결하는 부분이야, Arduino에게 데이터를 기다릴 때 최대 1초까지만 기다려
    time.sleep(2)                       # the Arduino restarts when we connect
    input("Remove all force from the handle, then press Enter to zero it...")
    ser.write(b"T")                     # serial 통로를 통해 Arduino에게 데이터를 보내라 T = tare (set zero)
    time.sleep(1)
    ser.reset_input_buffer()
    return ser

def countdown(seconds=3):
    for n in range(seconds, 0, -1):
        print(f"  {n}...")
        plt.pause(1)

def rest(seconds):
    if seconds > 0:
        print(f"Rest for {seconds} seconds...")
        plt.pause(seconds)

def record(ser, ax, hand, title, test, sounds):
    """Record one squeeze and draw it live. Returns the raw curve."""
    if ser is None:
        fake_lines = fake_data.make_lines(hand, test, seconds)
    else:
        ser.reset_input_buffer()

    readings = []
    first_ms = None
    start = time.time()
    i = 0
    while True:
        if ser is None:
            if i>= len(fake_lines):
                break
            line = fake_lines[i]
        else:
            if time.time() - start >= seconds:
                break
            line = ser.readline().decode(errors = "ignore").strip()
        i += 1

        try:
            time_str, force_str = line.split(",")
            time_ms = int(time_str)
            force_kg = float(force_str)
        except ValueError:
            continue

        if first_ms is None:
            first_ms = time_ms
        readings.append({"time_ms": time_ms - first_ms, "force_kg": force_kg})

        if len(readings) % 5 == 0:
            now_s = readings[-1]["time_ms"]/1000
            ax.clear()
            ax.plot([r["time_ms"]/ 1000 for r in readings], [r["force_kg"] for r in readings])
            ax.set_xlim(max(0, now_s - 5), max(5, now_s))
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Force (kg)")
            ax.set_title(title)
            plt.pause(0.1 if ser is None else 0.001)

        if len(readings) == 0:
            raise RuntimeError("No data received - check the USB cable and the PORT setting.")
        return readings


def fake_reading(t):
    if t < 20:
        force = t * 1.5
    elif t < 60:
        force = 30 + random.uniform(-1, 1)
    else:
        force = max(0, 30 - (t - 60) * 0.8)
    return f"{t * 20},{force:.1f}"   

def ask_user_info():
    age = int(input("Enter age: "))
    sex = input("Enter gender (male/female): ").strip().lower()
    if sex not in ["male", "female"]:
        print("Invalid gender input. Please enter 'male' or 'female'.")
        return ask_user_info()
    return age, sex

def make_session_path():
    SESSIONS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SESSIONS_DIR / f"session_{timestamp}.csv"


def classify_grip(force, sex="female"):
    cutoff = 27 if sex == "male" else 16 
    return "Normal" if force >= cutoff else "Risk (Below Standard)"

def make_session_path():
    SESSIONS_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return SESSIONS_DIR / f"session_{stamp}.csv"

def run_grip_test(age, sex, num_samples=80):
    plt.ion()
    fig, ax = plt.subplots()
    xs, ys = [], []
    readings = []

    for t in range(num_samples):
        line = fake_reading(t)
        timestamp_str, force_str = line.split(",")
        timestamp = int(timestamp_str)
        force = float(force_str)
        readings.append({"timestamp": timestamp, "force": force})
        xs.append(timestamp)
        ys.append(force)
        ax.clear()
        ax.plot(xs, ys)
        ax.set_xlabel("time (ms)")
        ax.set_ylabel("force (kg)")
        ax.set_title("time vs force")
        plt.pause(0.03)
    plt.ioff()
    plt.show()

    peak_force = max(r["force"] for r in readings)
    result = assess(peak_force, age, sex)
    print_report(result)

    print(f"Peak Force: {peak_force} kg")
    print(f"Verdict: {classify_grip(peak_force, sex)}")

    save_path = make_session_path()

    with open(save_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_ms", "force_kg"])
        for r in readings:
            writer.writerow([r["timestamp"], r["force"]])
    print(f"{save_path} saved!")
    plot_on_centiles(result)
    return readings, result


if __name__ == "__main__":
    age,sex = ask_user_info()
    run_grip_test(age,sex)


def run_protocal(ser, doeminant):
    other = "left" if dominant == "right" else "right"
    trials = []

    plt.ion()
    fig,ax = plt.subplots()

    for tiral in range(1, TRIALS_PER_HAND + 1):
        for hand in [dominant, other]:
            print(f"\n--- {hand.upper()} hand, trial {trial} of {TRIALS_PER_HAND} ---")
            print(PROMPT_POSTURE)
            input("Press Enter when ready...")
            countdown()
            print(PROMPT_GO)
            readings = record(ser, ax, hand, f"{hand} hand - {trial}", "max", TRIAL_SECONDS)
            m = metrics.trial_metrics(readings)
            print(f"Relax. Peak: {m['peak_kg']:.1f} kg")
            trials.append({"hand": hand, "trials": trial, "test": "max", "readings": readings, "metrics": m})
            rest(REST_SECONDS)

    print(f"\n--- FATIGUE TEST ({dominant.upper()} hand) ---")
    print(PROMPT_POSTURE)
    input("Press Enter when ready...")
    countdown()
    print(PROMPT_FATIGUE)
    readings = record(ser, ax, dominant, "30-second fatigue test",
                      "fatigue", FATIGUE_SECONDS)
    fatigue = {"hand": dominant, "trial": 1, "test": "fatigue",
               "readings": readings, "metrics": metrics.trial_metrics(readings)}
    fatigue["metrics"]["fatigue_index_pct"] = metrics.fatigue_index_pct(readings)
    print("Relax. Fatigue test done.")    

    plt.ioff()
    plt.close(fig)
    return trials, fatigue

def best_trial(trials, hand):
    best = None
    for t in trials: 
        if t["hand"] == hand:
            if best is None or r["metrics"]["peak_kg"] > best["metrics"]["peak_kg"]:
                best = t
    return best

def summarize(trials, fatigue):
    best_right = best_trial(trials, "right")
    best_left = best_trial(trials, "left")
    ratio, weaker_pct = metrics.asymmetry(best_left["metrics"]["peak_kg"], best_right["metrics"]["peak_kg"])

    return {
        "right": best_right["metrics"],
        "left": best_left["metrics"],
        "ratio": ratio,
        "weaker_pct": weaker_pct,
        "fatigue_index_pct": fatigue["metrics"]["fatigue_index_pct"],
        "overall_peak_kg": max(best_right["metrics"]["peak_kg"],
                               best_left["metrics"]["peak_kg"]),
    }
               
def print_summary(summary):
    print("\n" + "=" * 50)
    print("GRIP TEST SUMMARY (best of 3 trials per hand)")
    print("-" * 50)  
    for hadn in ["right", "left"]:
        m = summary[hand]
        print(f"{hand.capitalize():5} peak{m['peak_kg']:5.1f} kg | "
              f"time to peak {m["time_to_peak_ms"]:4d} ms |"
              f"RFD {m['rfd_n_per_s']:6.0f} N/s")
        print(f"Fatigue index: {summary['fatigue_index_pct']:.1f}% decline over 30 s")
        print(f"Left/right ratio: {summary['ratio']:.2f} "
          f"(weaker hand {summary['weaker_pct']:.1f}% weaker)")
        print("=" * 50)

def save_session (stamp, trials, fatigue, summary):
    SESSIONS_DIR.mkdir(exist_ok = True)

    raw_path = SESSIONS_DIR / f"session_{stamp}_raw.csv"
    with open(raw_path, "w", newline = "") as f:
        writer = csv.writer(f)
        writer.writerow(["hand", "trial", "test", "peak_kg", "time_to_peak_ms", "rfd_n_per_s", "fatigue_index_pct"])

    summary_path = SESSIONS_DIR / f"session_{stamp}_summary.csv"
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hand", "trial", "test", "peak_kg",
                         "time_to_peak_ms", "rfd_n_per_s", "fatigue_index_pct"])

        for t in trials + [fatigue]:
            m = t["metrics"]
            writer.writerow([t["hand"], t["trial"], t["test"], m["peak_kg"],
                             m["time_to_peak_ms"], round(m["rfd_n_per_s"], 1),
                             m.get("fatigue_index_pct", "")])
        
        writer.writerow(["left_right_ratio", round(summary["ratio"], 3)])
        writer.writerow(["weaker_hand_pct", round(summary["weaker_pct"], 1)])

    print(f"Saved {raw_path.name} and {summary_path.name}")

def main():
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    age, sex, dominant = ask_user_info()
    ser = None if USE_FAKE else open_serial()

    trials, fatigue = run_protocal(ser, dominant)
    if ser is not None:
        ser.close()
        

    summary = summarize(trials, fatigue)
    print_summary(summary)

    result = assess(summary["overall_peak_kg"], age, sex)
    print_report(result)

    save_session(stamp, trials, fatigue, summary)
    plot_on_centiles(result, save_path=  SESSIONS_DIR)

if __name__ == "__main__":
    main()



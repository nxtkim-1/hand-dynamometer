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

TRIALS_PERHAND = 3
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







import csv
import random
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
from grip_compare import asses, print_report, plot_on_centiles

SESSIONS_DIR = Path(__file__).parent / "sessions"


def fake_reading(t):
    if t < 20:
        force = t * 1.5
    elif t < 60:
        force = 30 + random.uniform(-1, 1)
    else:
        force = max(0, 30 - (t - 60) * 0.8)
    return f"{t * 20},{force:.1f}"   


def classify_grip(force, sex="female"):
    cutoff = 27 if sex == "male" else 16 
    return "정상" if force >= cutoff else "위험 (기준 미만)"


def run_grip_test(sex="female", num_samples=80, save_path="session_test.csv"):
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

    forces_only = [r["force"] for r in readings]
    peak_force = max(forces_only)
    verdict = classify_grip(peak_force, sex)

    print(f"최고 힘: {peak_force} kg")
    print(f"판정: {verdict}")

    with open(save_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_ms", "force_kg"])
        for r in readings:
            writer.writerow([r["timestamp"], r["force"]])

    print(f"{save_path} saved!")
    return readings, peak_force, verdict



if __name__ == "__main__":
    run_grip_test(sex="female", num_samples=80)




import csv
import random
import matplotlib.pyplot as plt


# ── Day 7: 가짜 아두이노 데이터 생성기 ──────────────────────────────
# 나중에 진짜 하드웨어가 오면 이 함수 호출 자리를 아래처럼 바꾸면 됨:
#   import serial
#   ser = serial.Serial('COM5', 9600)
#   line = ser.readline().decode().strip()
def fake_reading(t):
    if t < 20:
        force = t * 1.5
    elif t < 60:
        force = 30 + random.uniform(-1, 1)
    else:
        force = max(0, 30 - (t - 60) * 0.8)
    return f"{t * 20},{force:.1f}"   # "timestamp_ms,force_kg" 형태 (Day 6에서 나온 그 계약)


# ── Day 4: 근감소증 기준(EWGSOP/AWGS) 분류 함수 ─────────────────────
def classify_grip(force, sex="female"):
    cutoff = 27 if sex == "male" else 16   # Day 3: if/else 비교
    return "정상" if force >= cutoff else "위험 (기준 미만)"


def run_grip_test(sex="female", num_samples=80, save_path="session_test.csv"):
    # ── Day 9: 실시간 그래프 준비 ────────────────────────────────
    plt.ion()
    fig, ax = plt.subplots()
    xs, ys = [], []

    # ── Day 2 / Day 5: 측정값을 담을 리스트(안에 딕셔너리) ─────────
    readings = []

    for t in range(num_samples):
        # Day 7: 한 줄 읽기 (지금은 가짜, 나중엔 ser.readline())
        line = fake_reading(t)

        # Day 6: 문자열 split → 숫자로 변환
        timestamp_str, force_str = line.split(",")
        timestamp = int(timestamp_str)
        force = float(force_str)

        # Day 5: 딕셔너리로 정리해서 리스트에 저장
        readings.append({"timestamp": timestamp, "force": force})

        # Day 9: 실시간 그래프 갱신
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

    # ── Day 10: 지표 계산 ────────────────────────────────────────
    forces_only = [r["force"] for r in readings]
    peak_force = max(forces_only)
    verdict = classify_grip(peak_force, sex)

    # Day 1: f-string으로 결과 출력
    print(f"최고 힘: {peak_force} kg")
    print(f"판정: {verdict}")

    # ── Day 6: CSV로 저장 (raw curve 전체 보존) ───────────────────
    with open(save_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["timestamp_ms", "force_kg"])
        for r in readings:
            writer.writerow([r["timestamp"], r["force"]])

    print(f"{save_path} 저장 완료!")
    return readings, peak_force, verdict


with open("data/dodds2014_norms.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row)

def load_norms(path="data/dodds2014_norms.csv"):
    norms = []
    with open(path, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            norms.append({
                "sex": row["sex"],
                "age": int(row["age"]),
                "p10": float(row["p10"]), "p25": float(row["p25"]),
                "p50": float(row["p50"]), "p75": float(row["p75"]),
                "p90": float(row["p90"]),
                "mean": float(row["mean"]), "sd": float(row["sd"]),
            })
    return norms


norms = load_norms()
print(f"Rows loaded: {len(norms)}")
print(norms[0])


if __name__ == "__main__":
    run_grip_test(sex="female", num_samples=80)
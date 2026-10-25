from datetime import datetime

now = datetime.now()
print(now)
print(now.strftime("%Y-%m-%d %H:%M:%S"))

   # Old Day 2-3 version, kept for reference. Not used by grip_test.py.

def fake_reading(t):
    if t < 20:
        force = t * 1.5 #올라감 --> 가짜 데이타
    elif t < 60:
        force = 30 + random.uniform(-1, 1) #조금씩 흔들림
    else:
        force = max(0, 30 - (t - 60) * 0.8) #조금씩 내려가게끔 하지만 음수는 안나오게
    return f"{t * 20},{force:.1f}"   #측정값 하나와 다음 측정값 사이에는 20밀리초가 지남 --> ms로 보야줌

def make_session_path():
    SESSIONS_DIR.mkdir(exist_ok=True) #.mkdir()은 그 위치에 폴더를 만듬, mkdir = “make directory”
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S") #datetime.now() = 지금 날짜와 시간을 가져옴, strftime("%Y%m%d_%H%M%S") = 원하는 모양의 글자로 바꿈
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

    peak_force = max(r["force"] for r in readings) # reading에 저장된 거를 r이고 force라는 데이터를 가져옴
    result = assess(peak_force, age, sex)
    print_report(result)

    print(f"Peak Force: {peak_force} kg")
    print(f"Verdict: {classify_grip(peak_force, sex)}")

    save_path = make_session_path()

    with open(save_path, "w", newline="") as f: 
        #open = 파일을 쓰기 모드로 열음
        # save_path = 파일을 여기다가 저장함
        # "w" = write mode 파일에 새로운 데이터를 작성할 때 사용함
        #newline = "" 줄바꿈이 올바르게 처리되도록 설정
        #with = 자동으로 닫히게 함
        writer = csv.writer(f) #어느 파일에 CSV 데이터를 작성할지 알려주는 것
        writer.writerow(["timestamp_ms", "force_kg"])
        for r in readings:
            writer.writerow([r["timestamp"], r["force"]])
    print(f"{save_path} saved!")
    plot_on_centiles(result)
    return readings, result

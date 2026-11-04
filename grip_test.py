import csv
import time
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt

import fake_data
import filters
import metrics
import quality
from grip_compare import assess, print_report, plot_on_centiles
from report import fmt, make_report


USE_FAKE = True
PORT = "/dev/cu.usbserial-XXXX" #PORT는 컴퓨터가 Arduino와 통신하는 연결 경로야
BAUD = 115200 #match with arduino code

TRIALS_PER_HAND = 3
TRIAL_SECONDS = 5 #5초 동안 짜고 3번 함
FATIGUE_SECONDS = 32
REST_SECONDS = 3 if USE_FAKE else 60 #가짜 데이터는 60초동안 쉴 필요가 없어서 3초동안만 쉼

SESSIONS_DIR = Path(__file__).parent / "sessions" #파일을 만드는 경로만 만들어 놈

# Sanity limits for real hardware
MAX_PLAUSIBLE_KG = 150   # the load cell is rated 100 kg; anything far above means "not calibrated yet"
MIN_RATE_HZ = 40         # below this, RFD is unreliable (the firmware's default HX711 rate is 10 Hz)

PROMPT_POSTURE = "Sit upright, elbow at 90 degrees, forearm neutral, wrist straight."
PROMPT_GO = "Squeeze as hard as you can! Harder... harder... harder..."
PROMPT_FATIGUE = "Squeeze as hard as you can and KEEP squeezing for 30 seconds!"

def ask_user_info():
    while True:
        answer = input("Enter age (5-100): ").strip()
        if answer.isdigit() and 5 <= int(answer) <= 100:   # the normative table covers ages 5-100
            age = int(answer)
            break
        print("Please type a whole number between 5 and 100.")
    sex = input("Enter sex (male/female): ").strip().lower() #strip = erase space, lower = make it lower case
    while sex not in ("male", "female"):
        sex = input("Please type male or female: ").strip().lower()
    dominant = input("Dominant hand (right/left): ").strip().lower()
    while dominant not in ("right", "left"):
        dominant = input("Please type right or left: ").strip().lower()
    return age, sex, dominant

def open_serial():
    import serial                       # arduino data
    from serial.tools import list_ports
    try:
        ser = serial.Serial(PORT, BAUD, timeout=1) #이 줄이 실제로 Arduino와 연결하는 부분이야, Arduino에게 데이터를 기다릴 때 최대 1초까지만 기다려
    except serial.SerialException:
        ports = [p.device for p in list_ports.comports()]
        raise RuntimeError(f"Could not open PORT = {PORT!r}. Ports found on this computer: {ports}. "
                           "Copy the Arduino's port into PORT at the top of grip_test.py.")
    time.sleep(2.5)                     # the Arduino restarts when we connect, then tares itself
    input("Remove all force from the handle, then press Enter to zero it...")
    ser.write(b"T")                     # serial 통로를 통해 Arduino에게 데이터를 보내라 T = tare (set zero)
    time.sleep(2.5)                     # tare averages 20 samples: ~2 s at 10 Hz, ~0.25 s at 80 Hz
    ser.reset_input_buffer()
    return ser

def countdown(seconds=3):
    for n in range(seconds, 0, -1): #0초의 간격으로 -1씩 줄어듬 0은 포함 안함
        print(f"  {n}...") #3... 2.... 1.... 
        plt.pause(1) #1초 동안 기다리게 만듬

def rest(seconds):
    if seconds > 0:
        print(f"Rest for {seconds} seconds...")
        plt.pause(seconds) #그만큼 기다리게 함

def record(ser, ax, hand, title, test, seconds):
    """Record one squeeze and draw it live. Returns the raw curve."""
    if ser is None:
        fake_lines = fake_data.make_lines(hand, test, seconds) #fake data안에 make_lines variable 가짜 측정값
    else:
        ser.reset_input_buffer() #쌓여 있던 옛날 데이터를 전부 지워

    readings = []
    skipped = []   # lines that were not data, e.g. "# tared" or the firmware's header
    first_ms = None #첫번째 시간 저장 --> 아직은 0
    start = time.time() #몇초 지났는지 알려줌
    i = 0
    while True:
        if ser is None: #한줄 한줄 읽고 더 읽을게 없으면 반복을 끝냄
            if i>= len(fake_lines): #i 숫자가 fake_lines 갯수보다 높으면 
                break
            line = fake_lines[i] #i번째 코드를 읽음
        else:
            if time.time() - start >= seconds: #시작하고 지난 시간
                break #멈춘다
            line = ser.readline().decode(errors = "ignore").strip()
            """
            ser.readline(): 아두이노가 보낸 한 줄 --> 컴퓨터용 바이트 형태
            .decode(errors="ignore"): 그걸 글자로 바꿔요. 바꿀 수 없는 깨진 부분은 무시해요
            .strip(): 줄 앞뒤의 빈칸과 줄바꿈 기호를 지워요.
            """
        i += 1 #다음줄을 읽기 위함

        # Works for both formats:
        #   simulator: "t_ms,force_kg"
        #   firmware:  "t_ms,raw,net,force_kg"  -> first column = time, last column = force
        parts = line.split(",")
        try:
            time_ms = int(parts[0])
            force_kg = float(parts[-1])
        except ValueError: #문제가 생기면 이번 줄은 버리고 맨 위로 돌아가
            if line:
                skipped.append(line)
            continue
        if len(parts) < 2:
            continue

        if first_ms is None: #아직 없으면
            first_ms = time_ms
        readings.append({"time_ms": time_ms - first_ms, "force_kg": force_kg}) #리스트 뒤에 추가함

        if len(readings) % 5 == 0: #나눈 나머지
            now_s = readings[-1]["time_ms"]/1000 #readings[-1] is last value on the list --> change ms --> s and save it
            ax.clear() 
            ax.plot([r["time_ms"]/ 1000 for r in readings], [r["force_kg"] for r in readings]) #r[] means in reading
            ax.set_xlim(max(0, now_s - 5), max(5, now_s)) #set_xlim(왼쪽 끝, 오른쪽 끝)은 가로축에서 보여줄 범위, max picks higher value
            ax.set_xlabel("Time (s)")
            ax.set_ylabel("Force (kg)")
            ax.set_title(title)
            plt.pause(0.1 if ser is None else 0.001)

    if len(readings) == 0:
        hint = f" First non-data line received: {skipped[0]!r}" if skipped else ""
        raise RuntimeError("No data received - check the USB cable and the PORT setting." + hint) #raise makes error on purpose
    return readings


def check_recording(readings, warned):
    """Catch the two silent hardware problems: wrong sample rate and missing calibration."""
    rate = filters.estimate_rate_hz(readings)
    if rate < MIN_RATE_HZ and not warned:
        print(f"  Warning: data arrive at about {rate:.0f} samples/s. RFD needs at least {MIN_RATE_HZ}; "
              "it will be reported as n/a. Set the HX711 to 80 Hz (RATE pin).")
        warned = True
    peak = max(r["force_kg"] for r in readings)
    if peak > MAX_PLAUSIBLE_KG:
        raise RuntimeError(f"Peak of {peak:.0f} 'kg' is not physically possible - the firmware is probably "
                           "not calibrated yet. Run software/calibrate.py and set COUNTS_PER_KG.")
    return warned


def run_protocol(ser, stamp, user):
    dominant = user["dominant"]
    other = "left" if dominant == "right" else "right"
    trials = []
    warned = False

    plt.ion()
    fig,ax = plt.subplots()

    for trial in range(1, TRIALS_PER_HAND + 1):
        for hand in [dominant, other]:
            print(f"\n--- {hand.upper()} hand, trial {trial} of {TRIALS_PER_HAND} ---")
            print(PROMPT_POSTURE)
            input("Press Enter when ready...")
            countdown()
            print(PROMPT_GO)
            readings = record(ser, ax, hand, f"{hand} hand - {trial}", "max", TRIAL_SECONDS)
            warned = check_recording(readings, warned)
            smooth = filters.filter_readings(readings)
            m = metrics.trial_metrics(smooth)
            q = quality.check_trial(smooth)
            print(f"Relax. Peak: {m['peak_kg']:.1f} kg")
            if q["label"] != "good":
                print(f"  Warning: possible {q['label']} - consider repeating this trial.")
            trials.append({"hand": hand, "trial": trial, "test": "max",
                           "readings": readings, "smooth": smooth,
                           "metrics": m, "quality": q["label"]})
            make_report(stamp, user, trials, SESSIONS_DIR, USE_FAKE)
            rest(REST_SECONDS)

    print(f"\n--- FATIGUE TEST ({dominant.upper()} hand) ---")
    print(PROMPT_POSTURE)
    input("Press Enter when ready...")
    countdown()
    print(PROMPT_FATIGUE)
    readings = record(ser, ax, dominant, "30-second fatigue test",
                      "fatigue", FATIGUE_SECONDS)
    check_recording(readings, warned)
    smooth = filters.filter_readings(readings)
    fatigue = {"hand": dominant, "trial": 1, "test": "fatigue",
               "readings": readings, "smooth": smooth, "metrics": metrics.trial_metrics(smooth)}
    fatigue["metrics"]["fatigue_index_pct"] = metrics.fatigue_index_pct(smooth)
    make_report(stamp, user, trials, SESSIONS_DIR, USE_FAKE, fatigue=fatigue)
    print("Relax. Fatigue test done.")    

    plt.ioff()
    plt.close(fig)
    return trials, fatigue

def best_trial(trials, hand):
    best = None
    for t in trials: 
        if t["hand"] == hand:
            if best is None or t["metrics"]["peak_kg"] > best["metrics"]["peak_kg"]:
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
    for hand in ["right", "left"]:
        m = summary[hand]
        print(f"{hand.capitalize():5} peak {fmt(m['peak_kg']):>5} kg | "
              f"time to peak {m['time_to_peak_ms']:4d} ms | "
              f"RFD {fmt(m['rfd_n_per_s'], 0):>6} N/s")
    print(f"Fatigue index: {fmt(summary['fatigue_index_pct'])}% decline over 30 s")
    print(f"Left/right ratio: {fmt(summary['ratio'], 2)} "
        f"(weaker hand {fmt(summary['weaker_pct'])}% weaker)")
    print("=" * 50)

def round_or_blank(x, digits):
    """round() that writes an empty cell instead of crashing when a metric could not be computed."""
    return "" if x is None else round(x, digits)

def save_session (stamp, trials, fatigue, summary):
    SESSIONS_DIR.mkdir(exist_ok = True)

    raw_path = SESSIONS_DIR / f"session_{stamp}_raw.csv"
    with open(raw_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hand", "trial", "test", "time_ms", "force_kg"])
        for t in trials + [fatigue]:
            for r in t["readings"]:
                writer.writerow([t["hand"], t["trial"], t["test"], r["time_ms"], r["force_kg"]])

    summary_path = SESSIONS_DIR / f"session_{stamp}_summary.csv"
    with open(summary_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["hand", "trial", "test", "peak_kg",
                         "time_to_peak_ms", "rfd_n_per_s", "fatigue_index_pct", "quality"])

        for t in trials + [fatigue]:
            m = t["metrics"]
            writer.writerow([t["hand"], t["trial"], t["test"], m["peak_kg"],
                             m["time_to_peak_ms"], round_or_blank(m["rfd_n_per_s"], 1),
                             m.get("fatigue_index_pct", ""), t.get("quality", "")])
        
        writer.writerow(["left_right_ratio", round_or_blank(summary["ratio"], 3)])
        writer.writerow(["weaker_hand_pct", round_or_blank(summary["weaker_pct"], 1)])

    print(f"Saved {raw_path.name} and {summary_path.name}")

def main():
    stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    age, sex, dominant = ask_user_info()
    user = {"age": age, "sex": sex, "dominant": dominant}
    ser = None if USE_FAKE else open_serial()

    trials, fatigue = run_protocol(ser, stamp, user)
    if ser is not None:
        ser.close()
        

    summary = summarize(trials, fatigue)
    save_session(stamp, trials, fatigue, summary)   # save first, so a later problem never loses the data
    print_summary(summary)

    result = assess(summary["overall_peak_kg"], age, sex)
    print_report(result)

    plot_on_centiles(result, save_path=SESSIONS_DIR / f"session_{stamp}_centiles.png", show=False)
    make_report(stamp, user, trials, SESSIONS_DIR, USE_FAKE,
                fatigue=fatigue, summary=summary, result=result)

if __name__ == "__main__":
    main()



import math
import random
import matplotlib.pyplot as plt

SAMPLE_RATE_HZ = 50 # how many measurements per second
DT_MS = 1000 // SAMPLE_RATE_HZ        #Ms = milliseconds
FAKE_PEAKS = {"right": 34.0, "left": 31.0} 

TRIAL_KINDS = ["good", "false_start", "slip", "submaximal"]
FAKE_BAD_RATE = 0.2


def max_grip_curve(peak_kg, duration_s=5, rise_tau_s = 0.15, noise_kg = 0.15, start_kg = 0.0, slip_s = None, slip_drop = 0.0): # person's peak force for 5 seconds, then release
    start_s = 0.5          
    release_s = 3.5         
    hold_drop = 0.03       

    held_kg = peak_kg * (1 - hold_drop * (release_s - start_s))

    lines = [] #making list
    for i in range(int(duration_s * SAMPLE_RATE_HZ)): #정해진 횟수만큼 반복해 = 250번 반복하라는 뜻이야
        t_s = i / SAMPLE_RATE_HZ #몇초인지 계산, 1초에 한번씩
        if t_s < start_s: #before squezing, before 0.5sec
            force = start_kg
        elif t_s < release_s:
            rise = 1 - math.exp(-(t_s - start_s) / rise_tau_s)  #힘 rises exponentially to peak
            hold = 1 - hold_drop * (t_s - start_s)  #how much force is lost during hold with equation
            force = start_kg + (peak_kg - start_kg) * rise * hold
            if slip_s is not None and slip_s <= t_s < slip_s + 0.3:
                force = force * (1 - slip_drop)
        else:
            force = held_kg * (1 - (t_s - release_s) / 0.3)   # drop to 0 in 0.3 s
        force = max(0.0, force + random.gauss(0, noise_kg))      # since sensor is not pergect, also put fake ups & downs
        lines.append(f"{i * DT_MS},{force:.2f}") #lines.appen = 맨뒤에 새로운 데이터 추가
    return lines

def generate_curve(peak_kg, kind, duration_s = 5):
    if kind == "good":
        return max_grip_curve(peak_kg, duration_s, rise_tau_s = random.unifrom(0.08, 0.30), 
                              stat_kg = peak_kg * random. unifrom(0, 0.05))

    if kind == "false_start": #false start → 쥐기 전 힘이 최대 힘의 5~35%. "good"(0~5%)과 5% 지점에서 맞닿아.
        return max_grip_curve(peak_kg, duration_s,
                              rise_tau_s = random.uniform(0.08, 0.30),
                              start_kg=peak_kg * random.uniform(0.05, 0.35))

    if kind == "slip": #slip → 1.2~2.8초 사이 아무 때나 미끄러지고, 힘이 15~50% 떨어져.
        return max_grip_curve(peak_kg, duration_s,
                              rise_tau_s = random.uniform(0.08, 0.30),
                              slip_s = random.uniform(1.2, 2.8),
                              slip_drop = random.uniform(0.15, 0.50))

    if kind == "submaximal": #submaximal → 최대 힘이 원래의 50~80%, 오르는 속도가 느리고(0.30~0.70초), 흔들림이 더 커 (힘을 덜 줄 때 손이 더 떨려
        return max_grip_curve(peak_kg * random.uniform(0.5, 0.8), duration_s,
                              rise_tau_s = random.uniform(0.30, 0.70),
                              noise_kg = 0.3)
    raise ValueError(f"Unknown kind: {kind}")


def fatigue_curve(peak_kg, duration_s=32): #힘을 얼마나 오래 유지할 수 있는지
    """Squeeze as hard as possible for 30 s: force slowly fades."""
    start_s = 1.0          
    squeeze_s = 30.0      
    rise_tau_s = 0.2
    fade_tau_s = 15.0      

    lines = []
    for i in range(int(duration_s * SAMPLE_RATE_HZ)):
        t_s = i / SAMPLE_RATE_HZ
        if t_s < start_s or t_s > start_s + squeeze_s:
            force = 0.0
        else:
            rise = 1 - math.exp(-(t_s - start_s) / rise_tau_s)
            fade = 0.5 + 0.5 * math.exp(-(t_s - start_s) / fade_tau_s)
            force = peak_kg * rise * fade
        force = max(0.0, force + random.gauss(0, 0.3))       
        lines.append(f"{i * DT_MS},{force:.2f}")
    return lines



def make_lines(hand, test, duration_s):
    """Pick a curve for this hand. Each trial is a little different."""
    peak = FAKE_PEAKS[hand] * random.uniform(0.93, 1.0) #multiply random number between 0.93 -1.00
    if test == "fatigue":
        return fatigue_curve(peak, duration_s)
    kind = "good"
    if random.random() < FAKE_BAD_RATE:
        kind = random.choice(TRIAL_KINDS[1:]) #[1:] = 1번째부터 끝까지 잘라내기 --> "good"을 뺀 ["false_start", "slip", "submaximal"]이야
        #random.choice = pick anything from the list 
    return max_grip_curve(peak, duration_s)

def lines_to_readings(lines):
    """Turn "time,force" text lines into a list of dictionaries."""
    readings = []
    for line in lines:
        time_str, force_str = line.split(",")
        readings.append({"time_ms": int(time_str), "force_kg": float(force_str)})
    return readings

if __name__ == "__main__": #if I am running this code directly by pressing play button
    fig, axes = plt.subplots(2, 2, figsize = (9,6)) #가로 2 × 세로 2 = 칸 4개, 전체 그림의 가로 9인치, 세로 6인치
    for kind, ax in zip(TRIAL_KINDS, axes.flatten()): #axes.flatten() → 2줄짜리 칸 묶음 [[칸1, 칸2], [칸3, 칸4]]을 한 줄로 핌
        #zip(TRIAL_KINDS, axes.flatten()) → 종류 4개와 칸 4개를 순서대로 짝지어. "good"은 칸1, "false_start"는 칸2, ...
        readings = lines_to_readings(generate_curve(34.0, kind))
        ax.plot([r["time_ms"] / 1000 for r in readings], [r["force_kg"] for r in readings])
        ax.set_title(kind)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Force (kg)")
    plt.tight_layout()
    plt.show()
import math
import random
import matplotlib.pyplot as plt

SAMPLE_RATE_HZ = 50 # how many measurements per second
DT_MS = 1000 // SAMPLE_RATE_HZ        #Ms = milliseconds
FAKE_PEAKS = {"right": 34.0, "left": 31.0} 


def max_grip_curve(peak_kg, duration_s=5): # person's peak force for 5 seconds, then release
    start_s = 0.5          
    release_s = 3.5        
    rise_tau_s = 0.15      
    hold_drop = 0.03       

    held_kg = peak_kg * (1 - hold_drop * (release_s - start_s))

    lines = [] #making list
    for i in range(int(duration_s * SAMPLE_RATE_HZ)): #정해진 횟수만큼 반복해 = 250번 반복하라는 뜻이야
        t_s = i / SAMPLE_RATE_HZ #몇초인지 계산, 1초에 한번씩
        if t_s < start_s: #before squezing, before 0.5sec
            force = 0.0
        elif t_s < release_s:
            rise = 1 - math.exp(-(t_s - start_s) / rise_tau_s)  #힘 rises exponentially to peak
            hold = 1 - hold_drop * (t_s - start_s)  #how much force is lost during hold with equation
            force = peak_kg * rise * hold
        else:
            force = held_kg * (1 - (t_s - release_s) / 0.3)   # drop to 0 in 0.3 s
        force = max(0.0, force + random.gauss(0, 0.15))      # since sensor is not pergect, also put fake ups & downs
        lines.append(f"{i * DT_MS},{force:.2f}") #lines.appen = 맨뒤에 새로운 데이터 추가
    return lines


def fatigue_curve(peak_kg, duration_s=32): #how fast the force fades over time
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
    return max_grip_curve(peak, duration_s)


if __name__ == "__main__": #if I am running this code directly by pressing play button
    fig, (ax1, ax2) = plt.subplots(2, 1) #전체, 그래프 자리들
    for name, lines, ax in [
        ("Max grip", max_grip_curve(34.0), ax1),
        ("Fatigue", fatigue_curve(34.0), ax2)
        ]:
        times = [int(line.split(",")[0]) for line in lines] # divide the time by spliting them based on comma and take the first number
        forces = [float(line.split(",")[1]) for line in lines] #this time the second number which is decimal
        ax.plot(times, forces)
        ax.set_title(name)
        ax.set_ylabel("Force (kg)")
    ax2.set_xlabel("Time (ms)")
    plt.tight_layout()
    plt.show()
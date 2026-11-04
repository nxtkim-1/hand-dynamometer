"""
filters.py - Remove sensor noise from a force-time curve.

Two filters are compared:
  1. Moving average (written by hand)
  2. 4th-order Butterworth low-pass, applied forwards and backwards (scipy)
"""

from scipy.signal import butter, filtfilt
#scipy = 과학 계산 도구상자, signal =  신호 처리 칸, butter = Butterworth 필터의 설계도를 만드는 함수
#filtfilt = 설계도로 신호를 앞뒤로 거르는 함수

SAMPLE_RATE_HZ = 50
CUTOFF_HZ = 10
MIN_POINTS = 16          # filtfilt needs more points than its padding (3 x filter length)


def estimate_rate_hz(readings):
    """Measure how many samples per second a curve really has.

    Uses (number of gaps) / (total time) instead of one gap, because Arduino millis()
    timestamps are whole numbers: at 80 Hz the gaps alternate 12 and 13 ms.
    """
    if len(readings) < 2:
        return SAMPLE_RATE_HZ
    span_ms = readings[-1]["time_ms"] - readings[0]["time_ms"]
    if span_ms <= 0:
        return SAMPLE_RATE_HZ
    return (len(readings) - 1) * 1000 / span_ms

def moving_average(values, window = 5):
    half = window // 2 #앞뒤로 두개씩 봄
    smooth = []
    for i in range(len(values)):
        chunk = values[max(0, i - half): i + half + 1]
        smooth.append(sum(chunk)/ len(chunk))
    return smooth 

def butter_lowpass(values, cutoff_hz = CUTOFF_HZ, fs = SAMPLE_RATE_HZ, order = 4):
    b,a = butter(order, cutoff_hz, fs = fs)
    #필터의 설계도(숫자 두 묶음 b, a)를 만들어. 
    #4차, 10 Hz, 50 Hz 신호용 필터"
    return list(filtfilt(b,a, values))
    #filtfilt(b,a, values) = 설계도로 신호를 앞으로 한 번, 뒤로 한 번 걸러
    #list() = numpy list so change to normal list

def filter_readings(readings, method = "butter"):
    """Return a new, smoothed copy of a curve. The original is not changed.

    The filter is designed for the curve's MEASURED sample rate, so it stays correct
    whether the data come from the 50 Hz simulator or a slower/faster Arduino.
    """
    forces = [r["force_kg"] for r in readings] #only take force #
    fs = estimate_rate_hz(readings)
    cutoff = min(CUTOFF_HZ, 0.4 * fs)   # cutoff must stay below half the sample rate (Nyquist)
    if len(readings) < MIN_POINTS:
        smooth = forces                  # too short to filter safely -> keep as is
    elif method == "moving_average": #basic is butterwoth, moving_average is average movement
        smooth = moving_average(forces)
    else:
        smooth = butter_lowpass(forces, cutoff_hz=cutoff, fs=fs)
    return [{"time_ms": r["time_ms"], "force_kg": round(f, 3)}
        for r, f in zip(readings, smooth)] #takes two or more lists and pairs up their items by their position

if __name__  == "__main__":
    import statistics
    import matplotlib.pyplot as plt
    import fake_data
    import metrics

    true_curve = fake_data.lines_to_readings(fake_data.max_grip_curve(34.0, noise_kg = 0))
    true_rfd = metrics.rfd_n_per_s(true_curve)
    print(f"TRUE RFD (no noise): {true_rfd:.0f} N/s\n")

    errors = {"raw": [], "moving_average": [], "butter": []}
    for _ in range(300): #몇 번째인지는 안 쓰니까 이름을 _로
        noisy = fake_data.lines_to_readings(fake_data.max_grip_curve(34.00, noise_kg = 0.5)) #흔들림을 일부러 크게 (평소의 3배). 필터 차이가 잘 보이게
        errors["raw"].append(metrics.rfd_n_per_s(noisy)- true_rfd)
        for method in ["moving_average", "butter"]:
            smooth = filter_readings(noisy, method)
            errors[method].append(metrics.rfd_n_per_s(smooth) - true_rfd)

    print(f"{'Method':16} {'Mean error':>11} {'SD or error':>12}")
    """
    :16 → Displays "Method" left-aligned in a field of 16 characters.
    :>11 → Displays "Mean error" right-aligned in a field of 11 characters.
    :>12 → Displays "SD or error" right-aligned in a field of 12 characters.
    """
    for method, errs in errors.items():
        print(f"{method:16} {statistics.mean(errs):9.1f} N/s" 
              f"{statistics.stdev(errs):9.1f} N/s")
                #stdev = sample standard deviation
                #9 → 최소 9칸을 사용해 출력
                # .1 → 소수점 아래 1자리까지 표시

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    t = [r["time_ms"] / 1000 for r in noisy]
    ax1.plot(t, [r["force_kg"] for r in noisy], color="lightgray", label="Raw")
    ax1.plot(t, [r["force_kg"] for r in filter_readings(noisy, "moving_average")],
             label="Moving average")
    ax1.plot(t, [r["force_kg"] for r in filter_readings(noisy, "butter")],
             label="Butterworth 10 Hz")
    ax1.set_xlim(0.3, 1.5)
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Force (kg)")
    ax1.set_title("Rising phase, one noisy trial")
    ax1.legend()

    ax2.boxplot(list(errors.values()), tick_labels=list(errors.keys()))
    ax2.axhline(0, color="gray", linestyle="--")
    ax2.set_ylabel("RFD error (N/s)")
    ax2.set_title("RFD error over 300 simulated trials")
    plt.tight_layout()
    fig.savefig("images/filter_comparison.png")
    plt.show()
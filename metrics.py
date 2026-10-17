G = 9.81 # 1 kg of force = 9.81 newtons

def find_peak(readings):
    """Return the reading with the highest score"""
    best = readings[0]
    for r in readings:
        if r["force_kg"] > best["force_kg"]:
            best = r
    return best

def find_onset(readings, fraction = 0.05): #처음으로 힘을 주기 시작하는 지점, 맥스에 5프로를 리치하는순간 시작했다 알아차림
    """First reading where force passes 5% of the peak = squeeze starts."""
    threshold = find_peak(readings)["force_kg"] * fraction
    for r in readings:
        if r["force_kg"] >= threshold:
            return r
    return None

def time_to_peak_ms(readings): #힘을 주기 시작한 뒤 최대 힘에 도달하기까지 얼마나 걸렸는지
    """Time from the start of the squess to the peak"""
    return find_peak(readings)["time_ms"] - find_onset(readings)["time_ms"]

def fit_line (xs,ys):
    """Least-squares straight lien through the points: y = slope * x + intercept"""
    n = len(xs) #lens = 몇개인지 센다
    mean_x = sum(xs)/n
    mean_y = sum(ys)/n
    top = 0.0
    bottom = 0.0
    for x,y in zip(xs,ys): #equation for slope = sum((x - mean_x) * (y - mean_y)) / sum((x - mean_x) ** 2)
        top += (x - mean_x) * (y - mean_y)
        bottom += (x - mean_x) ** 2
    slope = top / bottom
    intercept = mean_y - slope * mean_x
    return slope, intercept

def rfd_n_per_s(readings, window_ms=100): #힘이 얼마나 빠른 속도로 증가하는가
    """Rate of force development: slope of force over the first 200ms, in N/s."""
    onset = find_onset(readings)["time_ms"] #time_ms만 가져오기
    xs, ys = [], []
    for r in readings:
        if onset <= r["time_ms"] <= onset + window_ms: #오차범위 100안에 있는것만 가져오기
            xs.append(r["time_ms"]/1000) #1초로 만들기 위해서
            ys.append(r["force_kg"] * G)

    if len(xs) < 2: #직선에 기울기를 찾을려면 점이 2개가 필요해서 그 미만이면 애초에 필요없다
        return None
    slope, intercept = fit_line(xs, ys) #둘중에 slope만 필요해서 intercept는 필요없다
    return slope

def fatigue_index_pct(readings, squeeze_ms = 30000, final_window_ms = 1000): #힘을 30초 동안 쓰고 마지막 1초만 써
    """Percent drop form the peak to the average of the last second of a 30s squeeze."""
    peak_kg = find_peak(readings)["force_kg"]
    end_ms = find_onset(readings)["time_ms"] + squeeze_ms #힘주고 시작한뒤에 세기 시작해야돼
    final = [r["force_kg"] for r in readings
             if end_ms - final_window_ms <= r["time_ms"] <= end_ms]
    if len(final) == 0 or peak_kg == 0: #len = counting number of obj
        return None
    final_kg = sum(final) / len(final)
    return (peak_kg - final_kg) / peak_kg * 100 #최대 힘에서 마지막까지 얼마나 감소했는지

def asymmetry(left_kg, right_kg):
    """Left/right ratio, and how much weaker the weaker hand is (in %)"""
    ratio = left_kg / right_kg
    weaker_pct = abs(left_kg - right_kg) / max(left_kg, right_kg) * 100 #absolute sign
    return ratio, weaker_pct

def trial_metrics(readings): # readings = 악력 측정 데이터
    """All single-trial metrics in one dictionary."""
    return{
        "peak_kg": find_peak(readings)["force_kg"],
        "time_to_peak_ms": time_to_peak_ms(readings),
        "rfd_n_per_s": rfd_n_per_s(readings),
    }


if __name__ == "__main__":
    import fake_data
    for test, lines in [("max", fake_data.max_grip_curve(34.0)), #34가 peak_kg가 됨 fake_data.py에서
                        ("fatigue", fake_data.fatigue_curve(34.0))]:
        readings = []
        for line in lines:
            time_str, force_str = line.split(",") #still string so gotta write int, float next line
            readings.append({"time_ms": int(time_str), "force_kg": float(force_str)}) #append add the number to the list
            m = trial_metrics(readings)
            print(f"{test} peak {m['peak_kg']:.1f} kg," f"time to peak {m['time_to_peak_ms']} ms," f"RFD {m['rfd_n_per_s']:.1f} N/s")
            if test == "fatigue":
                print(f"[{test}] fatigue index {fatigue_index_pect(readings):.1f} %")

            ratio, weaker = asymmetry(31.0, 34.0) #위에 만들어 놓은 식을 씀
            print(f"Left/right ratio {ratio:.2f}, weaker hand {weaker:.1f} % weaker")

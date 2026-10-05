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
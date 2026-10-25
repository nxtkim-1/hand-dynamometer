import csv
from pathlib import Path
from statistics import NormalDist
 
NORMS_PATH = Path(__file__).parent / "data" / "dodds2014_norms.csv"
 
PEAK = {"male": (51.9, 9.9), "female": (31.4, 6.1)}
 
CUTOFFS = {
    "EWGSOP2":   {"male": 27, "female": 16},
    "AWGS 2019": {"male": 28, "female": 18},
}
 
 
def load_norms(path=NORMS_PATH):
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
 
 
def find_norm_row(norms, age, sex):
    best_row = None
    best_gap = 999
    for row in norms:
        if row["sex"] != sex:
            continue
        gap = abs(row["age"] - age)
        if gap < best_gap:
            best_gap = gap
            best_row = row
    return best_row
 
 
def percentile_band(force, row):
    if force < row["p10"]:
        return "below 10th percentile"
    elif force < row["p25"]:
        return "10th-25th percentile"
    elif force < row["p50"]:
        return "25th-50th percentile"
    elif force < row["p75"]:
        return "50th-75th percentile"
    elif force < row["p90"]:
        return "75th-90th percentile"
    else:
        return "above 90th percentile"
 
 
def z_score(force, row):
    return (force - row["mean"]) / row["sd"]
 
 
def estimated_percentile(z):
    return NormalDist().cdf(z) * 100
 
 
def t_score(force, sex):
    peak_mean, peak_sd = PEAK[sex]
    return (force - peak_mean) / peak_sd
 
 
def check_cutoffs(force, age, sex):
    results = {}
    for name, values in CUTOFFS.items():
        if age < 65:
            results[name] = "not applicable (defined for age 65+)"
        elif force < values[sex]:
            results[name] = f"below cut-off (< {values[sex]} kg)"
        else:
            results[name] = f"at or above cut-off (>= {values[sex]} kg)"
    return results
 
 
def assess(force, age, sex, norms=None):
    if norms is None:
        norms = load_norms()
    row = find_norm_row(norms, age, sex)
    z = z_score(force, row)
    return {
        "force": force,
        "age": age,
        "sex": sex,
        "ref_age": row["age"],
        "median": row["p50"],
        "band": percentile_band(force, row),
        "z": round(z, 2),
        "percentile": round(estimated_percentile(z), 1),
        "t": round(t_score(force, sex), 2),
        "cutoffs": check_cutoffs(force, age, sex),
    }
 
 
def print_report(result):
    print("=" * 50)
    print(f"Measured grip: {result['force']} kg  ({result['sex']}, age {result['age']})")
    print(f"Reference: Dodds 2014, {result['sex']} age {result['ref_age']} "
          f"(median {result['median']} kg)")
    print("-" * 50)
    print(f"Percentile band: {result['band']}")
    print(f"Z-score: {result['z']}  -> estimated percentile ~{result['percentile']}%")
    print(f"T-score: {result['t']}  (<= -2.5 indicates weak grip)")
    for name, verdict in result["cutoffs"].items():
        print(f"{name}: {verdict}")
    print("-" * 50)
    print("Educational use only - not a medical diagnosis.")
    print("=" * 50)
 
 
def plot_on_centiles(result, norms=None, save_path=None):
    import matplotlib.pyplot as plt
    if norms is None:
        norms = load_norms()
    rows = [r for r in norms if r["sex"] == result["sex"]]
    ages = [r["age"] for r in rows]
 
    fig, ax = plt.subplots()
    ax.fill_between(ages, [r["p10"] for r in rows], [r["p90"] for r in rows],
                    alpha=0.15, label="10th-90th centile")
    ax.fill_between(ages, [r["p25"] for r in rows], [r["p75"] for r in rows],
                    alpha=0.3, label="25th-75th centile")
    ax.plot(ages, [r["p50"] for r in rows], label="Median (50th)")
    ax.scatter([result["age"]], [result["force"]], color="red", s=80,
               zorder=5, label="My measurement")
    ax.set_xlabel("Age (years)")
    ax.set_ylabel("Grip strength (kg)")
    ax.set_title(f"Dodds et al. (2014) norms - {result['sex']}")
    ax.legend()
    if save_path is not None:
        fig.savefig(save_path)
    if save_path is not None:
        fig.savefig(save_path)
    if show:
        plt.show()
    else:
        plt.close(fig)
 
 
if __name__ == "__main__":
    for force, age, sex in [(31.0, 19, "male"), (31.0, 19, "female"),
                            (24.0, 72, "male"), (15.0, 80, "female")]:
        print_report(assess(force, age, sex))
 

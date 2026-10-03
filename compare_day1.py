import csv

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

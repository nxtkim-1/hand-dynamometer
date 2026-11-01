"""
history.py - Dashboard of every saved session, using pandas.
Reads all sessions/*_summary.csv files and writes sessions/history.html.
"""

import webbrowser
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd

SESSIONS_DIR = Path(__file__).parent / "sessions"

def load_all_sessions ():
    tables = []
    for path in sorted(SESSIONS_DIR.glob("session_*_summary.csv")):
        df = pd.read_csv(path)
        df = df[df["test"].isin(["max", "fatigue"])]
        stamp = path.name.replace("session_", "").replace("_summary.csv", "")
        df["session"] = pd.to_datetime(stamp, format = "%Y-%m-%d_%H-%M-%S")
        tables.append(df)

    if len(tables) == 0:
        return None
    all_rows = pd.concat(tables, ignore_index = True)
    for col in ["peak_kg", "time_to_peak_ms", "rfd_n_per_s", "fatigue_index_pct"]:
        all_rows[col] = pd.to_numarical(all_rows[col], errors = "coerce")
    return all_rows

def per_session(df):
    """One row per session: best peak and CV for each hand, fatigue index."""
    maxes = df[df["test"] == "max"]
    best = maxes.pivot_table(index="session", columns="hand",
                             values="peak_kg", aggfunc="max")
    cv = maxes.pivot_table(index="session", columns="hand", values="peak_kg",
                           aggfunc=lambda x: x.std() / x.mean() * 100)
    fatigue = df[df["test"] == "fatigue"].groupby("session")["fatigue_index_pct"].first()

    table = pd.DataFrame({
        "right_best_kg": best["right"],
        "left_best_kg": best["left"],
        "right_cv_pct": cv["right"],
        "left_cv_pct": cv["left"],
        "fatigue_index_pct": fatigue,
    })
    table["left_right_ratio"] = table["left_best_kg"] / table["right_best_kg"]
    return table.round(2)

def plot_history(table, save_path):
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(8, 6), sharex=True)
    ax1.plot(table.index, table["right_best_kg"], marker="o", label="Right")
    ax1.plot(table.index, table["left_best_kg"], marker="o", label="Left")
    ax1.set_ylabel("Best peak (kg)")
    ax1.set_title("Grip strength over time")
    ax1.legend()
    ax2.plot(table.index, table["fatigue_index_pct"], marker="o", color="tab:red")
    ax2.set_ylabel("Fatigue index (%)")
    ax2.set_xlabel("Session")
    fig.autofmt_xdate()
    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)

def make_history_page():
    df = load_all_sessions()
    if df is None:
        print("No sessions found yet - run grip_test.py first.")
        return
    table = per_session(df)
    plot_history(table, SESSIONS_DIR / "history.png")

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><title>Grip history</title>
<style>
  body {{ font-family: -apple-system, Helvetica, Arial, sans-serif; max-width: 900px;
         margin: 40px auto; padding: 0 16px; background: #f7f7f9; color: #222; }}
  table {{ border-collapse: collapse; background: white; width: 100%; }}
  th, td {{ padding: 6px 10px; border-bottom: 1px solid #eee; text-align: right; }}
  img {{ width: 100%; background: white; border-radius: 12px; }}
</style></head>
<body>
<h1>Grip Strength History</h1>
<p>{len(table)} sessions &middot; {len(df[df["test"] == "max"])} maximal trials</p>
<img src="history.png?v={len(table)}" alt="History plot">
<h2>Overall statistics</h2>
{table.describe().round(2).to_html()}
<h2>All sessions</h2>
{table.to_html()}
</body></html>"""
    page = SESSIONS_DIR / "history.html"
    with open(page, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Saved {page.name}")
    webbrowser.open(page.resolve().as_uri())


if __name__ == "__main__":
    make_history_page()
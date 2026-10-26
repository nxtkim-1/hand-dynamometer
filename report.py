import statistics
import webbrowser

import matplotlib.pyplot as plt

STYLE = """
<style>
  body { font-family: -apple-system, Helvetica, Arial, sans-serif;
         max-width: 900px; margin: 40px auto; padding: 0 16px;
         color: #222; background: #f7f7f9; }
  h1 { margin-bottom: 4px; }
  h2 { margin-top: 36px; }
  .sub { color: #666; margin-top: 0; }
  .banner { padding: 10px 14px; border-radius: 8px; font-weight: 600; margin: 8px 0; }
  .fake { background: #fff3cd; border: 1px solid #f0c36d; }
  .live { background: #dbeafe; border: 1px solid #93c5fd; }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
           gap: 12px; margin: 24px 0; }
  .card { background: white; border-radius: 12px; padding: 16px;
          box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08); }
  .label { font-size: 13px; color: #666; }
  .value { font-size: 26px; font-weight: 600; margin-top: 4px; }
  .unit { font-size: 14px; color: #666; font-weight: normal; }
  table { width: 100%; border-collapse: collapse; background: white; }
  th, td { padding: 8px 12px; text-align: left; border-bottom: 1px solid #eee; }
  th { background: #f0f0f4; font-size: 13px; color: #555; }
  .bad { color: #b45309; font-weight: 600; }
  img { width: 100%; background: white; border-radius: 12px; margin: 12px 0; }
  .note { font-size: 13px; color: #888; margin-top: 32px; }
</style>
"""


def fmt(x, digits=1):
    if x is None:
        return "n/a"
    return f"{x:.{digits}f}"


def card(label, value, unit=""):
    return (f'<div class="card"><div class="label">{label}</div>'
            f'<div class="value">{value} <span class="unit">{unit}</span></div></div>')


def best_peak(trials, hand):
    peaks = [t["metrics"]["peak_kg"] for t in trials if t["hand"] == hand]
    if len(peaks) == 0:
        return None
    return max(peaks)


def cv_pct(trials, hand):
    """Coefficient of variation of the peaks of one hand (needs 2+ trials)."""
    peaks = [t["metrics"]["peak_kg"] for t in trials if t["hand"] == hand]
    if len(peaks) < 2:
        return None
    return statistics.stdev(peaks) / statistics.mean(peaks) * 100


def plot_curves(trials, fatigue, save_path):
    rows = 2 if fatigue is not None else 1
    fig, axes = plt.subplots(rows, 1, figsize=(8, 3.2 * rows), squeeze=False)
    ax1 = axes[0][0]
    for t in trials:
        curve = t.get("smooth", t["readings"])
        ax1.plot([r["time_ms"] / 1000 for r in curve],
                 [r["force_kg"] for r in curve],
                 label=f"{t['hand']} {t['trial']}")
    ax1.set_title("Maximal grip trials (filtered)")
    ax1.set_xlabel("Time (s)")
    ax1.set_ylabel("Force (kg)")
    if len(trials) > 0:
        ax1.legend(fontsize=8)

    if fatigue is not None:
        ax2 = axes[1][0]
        curve = fatigue.get("smooth", fatigue["readings"])
        ax2.plot([r["time_ms"] / 1000 for r in curve], [r["force_kg"] for r in curve])
        ax2.set_title(f"30-second fatigue test ({fatigue['hand']} hand)")
        ax2.set_xlabel("Time (s)")
        ax2.set_ylabel("Force (kg)")

    fig.tight_layout()
    fig.savefig(save_path)
    plt.close(fig)


def make_report(stamp, user, trials, folder, is_fake=True,
                fatigue=None, summary=None, result=None, total_trials=7):
    """Write session_<stamp>_report.html. Opens the browser the first time."""
    live = summary is None
    report_path = folder / f"session_{stamp}_report.html"
    first_time = not report_path.exists()
    folder.mkdir(exist_ok=True)

    curves_name = f"session_{stamp}_curves.png"
    plot_curves(trials, fatigue, folder / curves_name)
    done = len(trials) + (1 if fatigue is not None else 0)
    version = f"?v={done}"                 # makes the browser load the new picture

    refresh = '<meta http-equiv="refresh" content="2">' if live else ""
    banners = ""
    if is_fake:
        banners += '<p class="banner fake">FAKE DATA - generated for testing, not a real measurement.</p>'
    if live:
        banners += f'<p class="banner live">Test in progress: {done} of {total_trials} recordings done</p>'

    cards = (card("Right best", fmt(best_peak(trials, "right")), "kg")
             + card("Left best", fmt(best_peak(trials, "left")), "kg")
             + card("Right CV", fmt(cv_pct(trials, "right")), "%")
             + card("Left CV", fmt(cv_pct(trials, "left")), "%"))
    if summary is not None:
        cards += (card("Left/right ratio", fmt(summary["ratio"], 2))
                  + card("Fatigue index", fmt(summary["fatigue_index_pct"]), "%"))

    rows = ""
    for t in trials:
        m = t["metrics"]
        q = t.get("quality", "")
        q_html = q if q in ("good", "") else f'<span class="bad">{q}</span>'
        rows += (f"<tr><td>{t['hand']}</td><td>{t['trial']}</td>"
                 f"<td>{fmt(m['peak_kg'])}</td><td>{m['time_to_peak_ms']}</td>"
                 f"<td>{fmt(m['rfd_n_per_s'], 0)}</td><td>{q_html}</td></tr>")

    comparison = ""
    if result is not None:
        cutoff_items = "".join(f"<li><b>{name}:</b> {v}</li>"
                               for name, v in result["cutoffs"].items())
        comparison = f"""
<h2>Comparison with normative data</h2>
<ul>
  <li><b>Best grip:</b> {result['force']} kg</li>
  <li><b>Percentile band:</b> {result['band']}
      (Dodds 2014, {result['sex']}, age {result['ref_age']}, median {result['median']} kg)</li>
  <li><b>Z-score:</b> {result['z']} &rarr; estimated percentile ~{result['percentile']}%</li>
  <li><b>T-score:</b> {result['t']}</li>
  {cutoff_items}
</ul>
<img src="session_{stamp}_centiles.png" alt="Centile plot">"""

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
{refresh}
<title>Grip test {stamp}</title>
{STYLE}
</head>
<body>
<h1>Grip Strength Report</h1>
<p class="sub">{stamp} &middot; {user['sex']}, age {user['age']} &middot; dominant hand: {user['dominant']}</p>
{banners}
<div class="cards">{cards}</div>
{comparison}
<h2>Force-time curves</h2>
<img src="{curves_name}{version}" alt="Force-time curves">
<h2>Maximal trials</h2>
<table>
  <tr><th>Hand</th><th>Trial</th><th>Peak (kg)</th>
      <th>Time to peak (ms)</th><th>RFD (N/s)</th><th>Quality</th></tr>
  {rows}
</table>
<p class="note">CV = coefficient of variation of the peaks of one hand (lower = more consistent).<br>
Educational project - not a medical device and not a diagnosis.</p>
</body>
</html>
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html)
    if first_time:
        webbrowser.open(report_path.resolve().as_uri())
    return report_path

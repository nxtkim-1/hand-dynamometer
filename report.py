import html
import math
import statistics
import webbrowser
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError:
    plt = None

WEB = Path(__file__).parent / "web"

# The report shares the web app's tokens (colours, type, spacing) so both look like one product.
# The CSS is copied into the page because the report is also opened as a local file.
REPORT_CSS = """
  body { max-width: 900px; margin: var(--space-xl) auto; padding: 0 var(--space-md); }
  h1 { font-size: var(--text-3xl); margin-bottom: var(--space-2xs); line-height: 1.15; }
  h2 { font-size: var(--text-xl); margin: var(--space-xl) 0 var(--space-sm); line-height: 1.2; }
  .sub { color: var(--color-muted); margin: 0 0 var(--space-md); }
  .banner { padding: var(--space-sm) var(--space-md); border-radius: var(--radius-control); font-weight: 600;
            margin: var(--space-xs) 0; border: var(--rule-hair) solid transparent; }
  .fake { background: var(--color-warn-bg); border-color: var(--color-warn-rule); color: var(--color-warn-ink); }
  .live { background: var(--color-accent-soft); border-color: var(--color-accent); color: var(--color-accent-deep); }
  .caution { background: var(--color-caution-bg); border-color: var(--color-caution-rule); }
  .cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
           gap: var(--space-sm); margin: var(--space-lg) 0; }
  .card { background: var(--color-paper-2); border-radius: var(--radius-control); padding: var(--space-md);
          box-shadow: var(--shadow-card); }
  .label { font-size: var(--text-sm); color: var(--color-muted); }
  .value { font-size: var(--text-2xl); font-weight: 700; margin-top: var(--space-2xs); font-variant-numeric: tabular-nums; }
  .unit { font-size: var(--text-sm); color: var(--color-muted); font-weight: 400; }
  .table-wrap { overflow-x: auto; border-radius: var(--radius-control); background: var(--color-paper-2);
                border: var(--rule-hair) solid var(--color-rule); }
  table { width: 100%; border-collapse: collapse; font-variant-numeric: tabular-nums; }
  th, td { padding: var(--space-xs) var(--space-sm); text-align: left; border-bottom: var(--rule-hair) solid var(--color-rule);
           white-space: nowrap; }
  tr:last-child td { border-bottom: 0; }
  th { background: var(--color-paper-3); font-size: var(--text-sm); font-weight: 600; color: var(--color-ink-2); }
  .bad { color: var(--color-warn-ink); font-weight: 600; }
  .block ul { padding-left: var(--space-lg); }
  .block li + li { margin-top: var(--space-2xs); }
  img, .chart-svg { width: 100%; height: auto; display: block; background: var(--color-paper-2);
                    border-radius: var(--radius-control); margin: var(--space-sm) 0;
                    border: var(--rule-hair) solid var(--color-rule); }
  .note { font-size: var(--text-sm); color: var(--color-muted); margin-top: var(--space-xl); }
  .toolbar { display: flex; flex-wrap: wrap; gap: var(--space-sm); margin: var(--space-md) 0; }
  .btn { font: inherit; font-weight: 600; line-height: 1.5; padding: var(--space-xs) var(--space-md); min-height: 44px;
         border-radius: var(--radius-control); border: 2px solid var(--color-accent); background: var(--color-accent);
         color: var(--color-accent-ink); cursor: pointer; text-decoration: none; display: inline-flex; align-items: center;
         transition: background-color var(--dur-micro) var(--ease-out); }
  .btn:hover { background: var(--color-accent-hover); }
  .btn:active { background: var(--color-accent-press); }
  .btn.secondary { background: var(--color-paper-2); color: var(--color-accent-deep); }
  .btn.secondary:hover, .btn.secondary:active { background: var(--color-accent-soft); }
  @media (max-width: 40rem) {
    body { margin: var(--space-lg) auto; }
    h1 { font-size: var(--text-2xl); }
    .cards { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  }
  /* PDF: the browser's "Save as PDF" prints exactly this page, minus the buttons */
  @page { size: A4; margin: 14mm; }
  @media print {
    body { background: var(--color-paper-2); margin: 0; max-width: none; }
    .no-print { display: none !important; }
    .card { box-shadow: none; border: var(--rule-hair) solid var(--color-rule-strong); }
    .card, img, .chart-svg, tr, .block { break-inside: avoid; }
    h2 { break-after: avoid; }
    img, .chart-svg { max-height: 105mm; width: auto; max-width: 100%; display: block; margin: var(--space-xs) auto; }
    * { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
  }
"""


def page_style():
    """tokens.css + base.css from the web app, then the report's own rules."""
    shared = "\n".join((WEB / name).read_text(encoding="utf-8") for name in ("tokens.css", "base.css"))
    return f"<style>\n{shared}\n{REPORT_CSS}</style>"


# the same hand colours as web/tokens.css (--color-right, --color-left, --color-fatigue)
HAND_COLORS = {"right": "#c2410c", "left": "#6d28d9", "fatigue": "#be185d"}
INK = {"ink": "#1c1917", "muted": "#57534e", "rule": "#e7e2dd"}


def fmt(x, digits=1):
    if x is None:
        return "n/a"
    return f"{x:.{digits}f}"


def card(label, value, unit=""):
    return (f'<div class="card"><div class="label">{label}</div>'
            f'<div class="value">{value} <span class="unit">{unit}</span></div></div>')


def describe_user(stamp, user):
    """One line with whatever participant details were given."""
    parts = [stamp]
    if user.get("participant_id"):
        parts.append(f"ID {html.escape(str(user['participant_id']))}")
    parts.append(f"{user['sex']}, age {user['age']}")
    parts.append(f"dominant hand: {user['dominant']}")
    if user.get("height_cm"):
        parts.append(f"{fmt(user['height_cm'], 0)} cm")
    if user.get("weight_kg"):
        parts.append(f"{fmt(user['weight_kg'])} kg")
    return ", ".join(parts)


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


def style_axes(ax, title):
    ax.set_title(title, loc="left", fontsize=13, fontweight="bold", color=INK["ink"])
    ax.set_xlabel("Time (s)", color=INK["muted"])
    ax.set_ylabel("Force (kg)", color=INK["muted"])
    ax.grid(True, color=INK["rule"], linewidth=0.8)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(INK["rule"])
    ax.tick_params(colors=INK["muted"], labelsize=11)


def plot_curves(trials, fatigue, save_path):
    if plt is None:
        return
    rows = 2 if fatigue is not None else 1
    fig, axes = plt.subplots(rows, 1, figsize=(8, 3.4 * rows), squeeze=False)
    ax1 = axes[0][0]
    dashes = {1: "-", 2: "--", 3: ":"}           # trial number by line style, hand by colour
    for t in trials:
        curve = t.get("smooth", t["readings"])
        ax1.plot([r["time_ms"] / 1000 for r in curve],
                 [r["force_kg"] for r in curve],
                 color=HAND_COLORS.get(t["hand"]), linestyle=dashes.get(t["trial"], "-"), linewidth=2,
                 label=f"{t['hand']} {t['trial']}")
    style_axes(ax1, "Maximal grip trials (filtered)")
    if len(trials) > 0:
        ax1.legend(fontsize=10, frameon=False, ncol=2)

    if fatigue is not None:
        ax2 = axes[1][0]
        curve = fatigue.get("smooth", fatigue["readings"])
        ax2.plot([r["time_ms"] / 1000 for r in curve], [r["force_kg"] for r in curve],
                 color=HAND_COLORS["fatigue"], linewidth=2)
        style_axes(ax2, f"30-second fatigue test ({fatigue['hand']} hand)")

    fig.tight_layout()
    fig.savefig(save_path, dpi=150)
    plt.close(fig)


def _svg_line_chart(title, series_list, x_max, y_max, x_label="Time (s)", y_label="Force (kg)", height=260):
    w, h = 680, height
    pad_l, pad_r, pad_t, pad_b = 56, 20, 42, 42
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    x_max = max(x_max, 1.0)
    y_max = max(y_max, 10.0)
    sx = lambda v: pad_l + (v / x_max) * plot_w
    sy = lambda v: pad_t + plot_h - (max(0.0, v) / y_max) * plot_h

    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {w} {h}" role="img" aria-label="{html.escape(title)}">',
        f'<text x="{pad_l}" y="24" font-size="15" font-weight="700" fill="{INK["ink"]}">{html.escape(title)}</text>',
    ]
    y_step = 20 if y_max > 80 else 10
    for yv in range(0, int(y_max) + 1, y_step):
        py = sy(yv)
        parts.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{py:.1f}" y2="{py:.1f}" stroke="{INK["rule"]}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l - 8}" y="{py + 4:.1f}" text-anchor="end" font-size="11" fill="{INK["muted"]}">{yv}</text>')

    x_step = 5 if x_max > 10 else 1
    xv = 0
    while xv <= x_max + 1e-6:
        px = sx(xv)
        parts.append(f'<line x1="{px:.1f}" x2="{px:.1f}" y1="{pad_t}" y2="{pad_t + plot_h}" stroke="{INK["rule"]}" stroke-width="1"/>')
        parts.append(f'<text x="{px:.1f}" y="{pad_t + plot_h + 17}" text-anchor="middle" font-size="11" fill="{INK["muted"]}">{int(round(xv))}</text>')
        xv += x_step

    parts.append(f'<text x="{pad_l + plot_w / 2:.1f}" y="{h - 6}" text-anchor="middle" font-size="11" fill="{INK["muted"]}">{html.escape(x_label)}</text>')
    parts.append(f'<text x="15" y="{pad_t + plot_h / 2:.1f}" text-anchor="middle" font-size="11" fill="{INK["muted"]}" transform="rotate(-90 15 {pad_t + plot_h / 2:.1f})">{html.escape(y_label)}</text>')

    for item in series_list:
        pts = item["points"]
        if not pts:
            continue
        p_str = " ".join(f"{sx(px):.1f},{sy(py):.1f}" for px, py in pts)
        dash = f' stroke-dasharray="{item["dash"]}"' if item.get("dash") else ""
        parts.append(f'<polyline fill="none" stroke="{item["color"]}" stroke-width="2.2" stroke-linejoin="round"{dash} points="{p_str}"/>')

    if len(series_list) > 1:
        lx, ly = pad_l + 10, pad_t + 14
        for idx, item in enumerate(series_list):
            col = idx % 3
            row = idx // 3
            ix = lx + col * 115
            iy = ly + row * 16
            dash = f' stroke-dasharray="{item["dash"]}"' if item.get("dash") else ""
            parts.append(f'<line x1="{ix}" x2="{ix + 18}" y1="{iy - 4}" y2="{iy - 4}" stroke="{item["color"]}" stroke-width="2.2"{dash}/>')
            parts.append(f'<text x="{ix + 24}" y="{iy}" font-size="11" fill="{INK["ink"]}">{html.escape(item["label"])}</text>')

    parts.append("</svg>")
    return "\n".join(parts)


def svg_curves(trials, fatigue):
    dashes = {1: "", 2: "6,4", 3: "2,4"}
    max_series = []
    max_x = 5.0
    max_y = 40.0
    for t in trials:
        curve = t.get("smooth", t.get("readings", []))
        pts = [(r["time_ms"] / 1000.0, r["force_kg"]) for r in curve]
        if pts:
            max_x = max(max_x, max(p[0] for p in pts))
            max_y = max(max_y, max(p[1] for p in pts))
        max_series.append({
            "points": pts,
            "color": HAND_COLORS.get(t["hand"], INK["ink"]),
            "dash": dashes.get(t["trial"], ""),
            "label": f"{t['hand']} {t['trial']}",
        })
    max_y = max(40.0, math.ceil(max_y * 1.12 / 10.0) * 10.0)
    svgs = [_svg_line_chart("Maximal grip trials (filtered)", max_series, math.ceil(max_x), max_y)]

    if fatigue is not None:
        curve = fatigue.get("smooth", fatigue.get("readings", []))
        pts = [(r["time_ms"] / 1000.0, r["force_kg"]) for r in curve]
        f_x = max(30.0, math.ceil(max((p[0] for p in pts), default=32.0) / 5.0) * 5.0)
        f_y = max(40.0, math.ceil(max((p[1] for p in pts), default=40.0) * 1.12 / 10.0) * 10.0)
        svgs.append(_svg_line_chart(
            f"30-second fatigue test ({fatigue['hand']} hand)",
            [{"points": pts, "color": HAND_COLORS["fatigue"], "dash": "", "label": fatigue["hand"]}],
            f_x, f_y,
        ))
    return "\n".join(svgs)


def svg_centiles(result, norms=None):
    from grip_compare import load_norms
    if norms is None:
        norms = load_norms()
    rows = [r for r in norms if r["sex"] == result["sex"]]
    if not rows:
        return ""
    w, h = 680, 340
    pad_l, pad_r, pad_t, pad_b = 56, 20, 42, 42
    plot_w = w - pad_l - pad_r
    plot_h = h - pad_t - pad_b
    min_age = min(r["age"] for r in rows)
    max_age = max(r["age"] for r in rows)
    y_max = max(70.0, math.ceil(max(max(r["p90"] for r in rows), result["force"]) * 1.08 / 10.0) * 10.0)
    sx = lambda age: pad_l + ((age - min_age) / max(1, max_age - min_age)) * plot_w
    sy = lambda kg: pad_t + plot_h - (max(0.0, kg) / y_max) * plot_h

    wide = [f"{sx(r['age']):.1f},{sy(r['p90']):.1f}" for r in rows] + [f"{sx(r['age']):.1f},{sy(r['p10']):.1f}" for r in reversed(rows)]
    narrow = [f"{sx(r['age']):.1f},{sy(r['p75']):.1f}" for r in rows] + [f"{sx(r['age']):.1f},{sy(r['p25']):.1f}" for r in reversed(rows)]
    med = " ".join(f"{sx(r['age']):.1f},{sy(r['p50']):.1f}" for r in rows)
    px = sx(result["age"])
    py = sy(result["force"])

    parts = [
        f'<svg class="chart-svg" viewBox="0 0 {w} {h}" role="img" aria-label="Dodds et al. (2014) norms, {html.escape(result["sex"])}">',
        f'<text x="{pad_l}" y="24" font-size="15" font-weight="700" fill="{INK["ink"]}">Dodds et al. (2014) norms, {html.escape(result["sex"])}</text>',
    ]
    for yv in range(0, int(y_max) + 1, 10):
        gy = sy(yv)
        parts.append(f'<line x1="{pad_l}" x2="{w - pad_r}" y1="{gy:.1f}" y2="{gy:.1f}" stroke="{INK["rule"]}" stroke-width="1"/>')
        parts.append(f'<text x="{pad_l - 8}" y="{gy + 4:.1f}" text-anchor="end" font-size="11" fill="{INK["muted"]}">{yv}</text>')
    for age in range(10, int(max_age) + 1, 10):
        gx = sx(age)
        parts.append(f'<text x="{gx:.1f}" y="{pad_t + plot_h + 17}" text-anchor="middle" font-size="11" fill="{INK["muted"]}">{age}</text>')

    parts.append(f'<polygon fill="#f3efeb" points="{" ".join(wide)}"/>')
    parts.append(f'<polygon fill="#e7ddd3" points="{" ".join(narrow)}"/>')
    parts.append(f'<polyline fill="none" stroke="{INK["muted"]}" stroke-width="2" points="{med}"/>')
    parts.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="5.5" fill="{HAND_COLORS["right"]}" stroke="#ffffff" stroke-width="2"/>')
    parts.append(f'<text x="{pad_l + plot_w / 2:.1f}" y="{h - 6}" text-anchor="middle" font-size="11" fill="{INK["muted"]}">Age (years)</text>')
    parts.append(f'<text x="15" y="{pad_t + plot_h / 2:.1f}" text-anchor="middle" font-size="11" fill="{INK["muted"]}" transform="rotate(-90 15 {pad_t + plot_h / 2:.1f})">Grip strength (kg)</text>')
    parts.append(
        f'<rect x="{pad_l + 10}" y="{pad_t + 6}" width="12" height="10" fill="#f3efeb" stroke="{INK["rule"]}"/>'
        f'<text x="{pad_l + 26}" y="{pad_t + 15}" font-size="11" fill="{INK["ink"]}">10th–90th</text>'
        f'<rect x="{pad_l + 95}" y="{pad_t + 6}" width="12" height="10" fill="#e7ddd3"/>'
        f'<text x="{pad_l + 111}" y="{pad_t + 15}" font-size="11" fill="{INK["ink"]}">25th–75th</text>'
        f'<line x1="{pad_l + 180}" x2="{pad_l + 196}" y1="{pad_t + 11}" y2="{pad_t + 11}" stroke="{INK["muted"]}" stroke-width="2"/>'
        f'<text x="{pad_l + 202}" y="{pad_t + 15}" font-size="11" fill="{INK["ink"]}">Median</text>'
        f'<circle cx="{pad_l + 264}" cy="{pad_t + 11}" r="4.5" fill="{HAND_COLORS["right"]}"/>'
        f'<text x="{pad_l + 274}" y="{pad_t + 15}" font-size="11" fill="{INK["ink"]}">My measurement</text>'
    )
    parts.append("</svg>")
    return "\n".join(parts)


def render_report(stamp, user, trials, is_fake=True, fatigue=None, summary=None, result=None,
                  total_trials=7, home_url=None, calibration=None, inline_charts=False,
                  curves_src="", centiles_src=""):
    """Build the complete GripCheck report HTML string."""
    live = summary is None
    done = len(trials) + (1 if fatigue is not None else 0)
    use_inline = inline_charts or plt is None

    refresh = '<meta http-equiv="refresh" content="2">' if live else ""
    banners = ""
    if user.get("injury"):
        banners += ('<p class="banner caution">Participant reported recent hand or wrist pain or injury. '
                    'Interpret the results with caution.</p>')
    toolbar = ""
    if not live:
        home = f'<a class="btn secondary" href="{home_url}">New test</a>' if home_url else ""
        toolbar = (f'<div class="toolbar no-print"><button class="btn" onclick="window.print()">'
                   f'Download PDF</button>{home}</div>')
    if is_fake:
        banners += '<p class="banner fake">FAKE DATA - generated for testing, not a real measurement.</p>'
    if calibration:
        # real device, but the scale factor is not measured yet (see grip_test.CALIBRATION)
        banners += f'<p class="banner caution">Estimated calibration. {html.escape(calibration)}</p>'
    if live:
        banners += f'<p class="banner live">Test in progress: {done} of {total_trials} recordings done</p>'

    cards = (card("Right best", fmt(best_peak(trials, "right")), "kg")
             + card("Left best", fmt(best_peak(trials, "left")), "kg")
             + card("Right CV", fmt(cv_pct(trials, "right")), "%")
             + card("Left CV", fmt(cv_pct(trials, "left")), "%"))
    weight = user.get("weight_kg")
    if summary is not None and weight:
        # grip relative to body weight: compares people of different sizes more fairly
        cards += card("Grip / body weight", fmt(summary["overall_peak_kg"] / weight, 2), "kg/kg")
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
        centile_chart = svg_centiles(result) if use_inline else f'<img src="{centiles_src}" alt="Centile plot">'
        comparison = f"""
<section class="block">
<h2>Comparison with normative data</h2>
<ul>
  <li><b>Best grip:</b> {fmt(result['force'])} kg</li>
  <li><b>Percentile band:</b> {result['band']}
      (Dodds 2014, {result['sex']}, age {result['ref_age']}, median {result['median']} kg)</li>
  <li><b>Z-score:</b> {result['z']} &rarr; estimated percentile ~{result['percentile']}%</li>
  <li><b>T-score:</b> {result['t']}</li>
  {cutoff_items}
</ul>
{centile_chart}
</section>"""

    curves_chart = svg_curves(trials, fatigue) if use_inline else f'<img src="{curves_src}" alt="Force-time curves">'
    # the page title becomes the default file name when the report is saved as a PDF
    page_title = " ".join(p for p in ["GripCheck report", html.escape(str(user.get("participant_id") or "")), stamp] if p)
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{refresh}
<title>{page_title}</title>
{page_style()}
</head>
<body>
<h1>GripCheck Report</h1>
<p class="sub">{describe_user(stamp, user)}</p>
{toolbar}
{banners}
<div class="cards">{cards}</div>
{comparison}
<section class="block">
<h2>Force-time curves</h2>
{curves_chart}
</section>
<h2>Maximal trials</h2>
<div class="table-wrap">
<table>
  <tr><th>Hand</th><th>Trial</th><th>Peak (kg)</th>
      <th>Time to peak (ms)</th><th>RFD (N/s)</th><th>Quality</th></tr>
  {rows}
</table>
</div>
<p class="note">CV = coefficient of variation of the peaks of one hand (lower = more consistent).<br>
Educational project - not a medical device and not a diagnosis.</p>
</body>
</html>
"""


def make_report(stamp, user, trials, folder, is_fake=True,
                fatigue=None, summary=None, result=None, total_trials=7,
                open_browser=True, home_url=None, calibration=None):
    """Write session_<stamp>_report.html. Opens the browser the first time (terminal app only)."""
    report_path = folder / f"session_{stamp}_report.html"
    first_time = not report_path.exists()
    folder.mkdir(exist_ok=True)

    curves_name = f"session_{stamp}_curves.png"
    plot_curves(trials, fatigue, folder / curves_name)
    done = len(trials) + (1 if fatigue is not None else 0)
    html_text = render_report(
        stamp, user, trials, is_fake=is_fake, fatigue=fatigue, summary=summary,
        result=result, total_trials=total_trials, home_url=home_url,
        calibration=calibration, inline_charts=(plt is None),
        curves_src=f"{curves_name}?v={done}",
        centiles_src=f"session_{stamp}_centiles.png",
    )
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(html_text)
    if first_time and open_browser:
        webbrowser.open(report_path.resolve().as_uri())
    return report_path

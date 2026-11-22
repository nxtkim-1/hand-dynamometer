"""
analyze_session.py - full analysis of one saved session (app or website raw CSV).

Usage:
    python software/analyze_session.py sessions/session_2026-11-22_14-00-00_raw.csv --dominant right
    python software/analyze_session.py gripcheck_..._raw.csv --dominant left --out results/p01 --plot
    python software/analyze_session.py raw.csv --calibration measured    # only after G3 is really done

Writes <out>_analysis.json and <out>_analysis.csv (and <out>_curves.png with --plot).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analysis  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser(description="Analyze a saved grip session")
    ap.add_argument("file")
    ap.add_argument("--dominant", choices=["right", "left"])
    ap.add_argument("--calibration", choices=["estimated", "measured"], default="estimated")
    ap.add_argument("--out", help="output path prefix (default: next to the input file)")
    ap.add_argument("--plot", action="store_true", help="also save a PNG of every filtered curve")
    a = ap.parse_args(argv)

    with open(a.file, newline="", encoding="utf-8") as f:
        trials = analysis.load_session_csv(f.read())
    if not trials:
        sys.exit("No trials found. Expected columns: hand,trial,test,time_ms,force_kg")
    result = analysis.analyze_session(trials, a.dominant, a.calibration)
    out = a.out or os.path.splitext(a.file)[0]
    with open(out + "_analysis.json", "w", encoding="utf-8") as f:
        f.write(analysis.summary_json(result))
    with open(out + "_analysis.csv", "w", encoding="utf-8", newline="") as f:
        f.write(analysis.summary_csv(result))

    lr = result["left_right"]
    print(result["note"])
    for t in result["trials"]:
        extra = f"  FI {analysis._num(t.get('fi_peak_last1s_pct'), 1)} %" if t["test"] == "fatigue" else ""
        print(f"{t['hand']:5} {t['test']:7} #{t['trial']}  peak {t['peak_kg']:6.2f} kg  best 1 s "
              f"{analysis._num(t.get('best_1s_kg'))} kg{extra}")
    print(f"L/R ratio {analysis._num(lr['ratio_l_over_r'], 3)}  asymmetry index {analysis._num(lr['asymmetry_index_pct'], 1)} %")
    print(f"wrote {out}_analysis.json and {out}_analysis.csv")

    if a.plot:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import filters
        fig, ax = plt.subplots(figsize=(9, 4.5))
        for (hand, trial, test), rs in sorted(trials.items()):
            sm = filters.filter_readings(rs)
            ax.plot([r["time_ms"] / 1000 for r in sm], [r["force_kg"] for r in sm],
                    label=f"{hand} {test} {trial}", lw=1.6 if test == "fatigue" else 1.1)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("force (kg, " + a.calibration + ")")
        ax.grid(alpha=0.3)
        ax.legend(fontsize=7, ncol=2)
        fig.tight_layout()
        fig.savefig(out + "_curves.png", dpi=140)
        print(f"wrote {out}_curves.png")


if __name__ == "__main__":
    main()

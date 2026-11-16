# GripCheck website

The public site for the hand dynamometer: the project overview, and **GripCheck**, the browser software that
runs the standard grip test on the device. A static React app. It has no server: the analysis runs on the page,
and results are stored only in the visitor's browser.

> Educational project. Not a medical device, and not for diagnosis.

## What is in it

| Route | Page |
|---|---|
| `/` | Project overview: mission, what the device does, hardware, software pipeline, build status, team |
| `/test` | The guided test: device or simulator, participant form, zeroing, 6 maximal squeezes + 30 s hold, live graph |
| `/results` | Sessions saved in this browser |
| `/results/:id` | Report: best grip on Dodds 2014 centiles, both hands, fatigue curve, every trial, CSV export, print to PDF |
| `/how-it-works` | Signal chain, protocol, filtering, metrics, trial check, norms, calibration status, limitations |

**Using the real device:** Chrome or Edge on a computer. Plug in the Nano, close the Arduino Serial Monitor,
press **Connect device** on `/test`. The page reads `t_ms,raw,net,force_kg` at 115200 baud over Web Serial,
sends `T` to zero and waits for the firmware's `# tared` reply. It also reads the `# calibration=` boot line,
and shows the estimated-calibration banner until the firmware says `measured`.
**Not yet tried with the real Nano.** So far it has been checked with simulated data only.

## Run it

```bash
cd website
npm install
npm run dev        # http://localhost:5173
npm test           # Vitest: parity with the Python app + behaviour tests
npm run build      # type-check, then build to dist/
```

## How the analysis stays correct

`src/lib/` is a port of the Python app (`filters.py`, `metrics.py`, `quality.py`, `grip_compare.py`, and the
protocol parts of `grip_test.py` / `webapp.py`). Function names match, so the two can be read side by side.

To keep the copies from drifting apart, `scripts/make_fixtures.py` runs the **original Python code** on fixed
curves (simulated, plus firmware-format curves at 10 and 50 Hz). It saves the answers to
`src/lib/__fixtures__/reference.json`, and `parity.test.ts` checks that the TypeScript gives the same filtered
curves, metrics, quality features, labels and norm assessments. After changing any of those Python files, run:

```bash
npm run fixtures && npm test
```

`protocol.test.ts` also checks that `src/data/norms.ts` still matches `../data/dodds2014_norms.csv` exactly.

Differences from the Python app, on purpose:
- The trial check uses the hand-written rules only. The Random Forest (`models/quality_model.joblib`) cannot
  run in a browser, and it was trained on simulated curves anyway.
- The simulator really produces faulty trials about 1 in 5 times. (`fake_data.make_lines` picks a fault type
  but then returns a clean curve.) The fault ranges are narrowed so each simulated fault is clear-cut.

## Deploy on Vercel

1. Vercel → **Add New → Project** → import `nxtkim-1/hand-dynamometer`.
2. Set **Root Directory** to `website`. Vercel detects Vite: build `npm run build`, output `dist`.
3. Deploy. `vercel.json` sends every page route to `index.html`, so links like `/results/...` work on reload.

Every merge to `main` then redeploys. Web Serial needs HTTPS, which Vercel provides.

## Layout

```
website/
├── index.html, vite.config.ts, vercel.json, tsconfig.json
├── public/            favicon and the images used on the pages (copied from ../images)
├── scripts/           make_fixtures.py (Python reference answers)
└── src/
    ├── lib/           analysis (parse, filters, metrics, quality, norms, protocol, simulator),
    │                  Web Serial device, local storage, CSV export, and their tests
    ├── data/norms.ts  Dodds et al. (2014) Table 2
    ├── components/    layout, device connection, charts (canvas for live, SVG for reports), icons
    ├── pages/         one file per route
    └── styles/app.css design tokens (light, dark, print) and components
```

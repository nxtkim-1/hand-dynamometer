import { Link } from "react-router-dom";
import { IconWarn } from "../components/Icons";
import { REPO_URL } from "../components/Layout";
import { CUTOFFS, PEAK } from "../lib/norms";
import { FATIGUE_SECONDS, MIN_RATE_HZ, TRIAL_SECONDS, TRIALS_PER_HAND } from "../lib/protocol";

const SECTIONS = [
  ["chain", "Signal chain"],
  ["protocol", "Protocol"],
  ["filtering", "Filtering"],
  ["metrics", "Metrics"],
  ["quality", "Trial check"],
  ["norms", "Norms"],
  ["calibration", "Calibration"],
  ["limits", "Limitations"],
];

export default function HowItWorksPage() {
  return (
    <>
      <div className="container page-head">
        <span className="eyebrow">How it works</span>
        <h1>From a squeeze to a percentile</h1>
        <p className="lead">
          What happens between your hand and the report, and why each step is done the way it is. Every formula here is the one the code uses.
        </p>
        <nav className="toc" aria-label="On this page">
          {SECTIONS.map(([id, label]) => (
            <a key={id} href={`#${id}`}>
              {label}
            </a>
          ))}
        </nav>
      </div>

      <section className="doc-section" id="chain">
        <div className="container">
          <h2>Signal chain</h2>
          <ol className="chain" style={{ padding: 0, margin: 0 }}>
            <li>
              <span className="step-n">01 · Load cell</span>
              <b>Force → strain</b>
              <span>A squeeze bends the CZL601 beam; its strain gauges form a Wheatstone bridge that outputs about 2 mV per volt at 100 kg.</span>
            </li>
            <li>
              <span className="step-n">02 · HX711</span>
              <b>Millivolts → counts</b>
              <span>A 24-bit ADC with gain 128 turns the bridge voltage into a signed integer, 10 (or 80) times a second.</span>
            </li>
            <li>
              <span className="step-n">03 · Arduino Nano</span>
              <b>Counts → kg</b>
              <span>Subtracts the zero offset, flips the sign so a squeeze is positive, divides by counts per kg.</span>
              <span className="out">1234,52410,0,0.000</span>
            </li>
            <li>
              <span className="step-n">04 · USB serial</span>
              <b>Lines of text</b>
              <span>115200 baud. Lines starting with # are comments; "T" re-zeroes.</span>
              <span className="out">t_ms,raw,net,force_kg</span>
            </li>
            <li>
              <span className="step-n">05 · This page</span>
              <b>Curve → results</b>
              <span>Web Serial reads the lines; the filter, metrics, trial check and norms all run in the browser.</span>
            </li>
          </ol>
          <figure className="figure" style={{ marginTop: 24, maxWidth: 720 }}>
            <div className="frame">
              <img src="/images/drawing_wiring.png" alt="Wiring drawing: HX711 VCC to 5V, GND to GND, DT to D3, SCK to D2 on the Arduino Nano" loading="lazy" />
            </div>
            <figcaption>Wiring: HX711 VCC → 5V, GND → GND, DT → D3, SCK → D2.</figcaption>
          </figure>
        </div>
      </section>

      <section className="doc-section" id="protocol">
        <div className="container two-col">
          <div className="prose">
            <h2 style={{ fontSize: "clamp(1.6rem, 3vw, 2.1rem)" }}>Protocol</h2>
            <p>
              The test follows the American Society of Hand Therapists (ASHT) approach, so results are comparable with the normative data, which were
              collected the same way: best of several maximal efforts, seated, elbow at 90°.
            </p>
            <p>
              <strong>{TRIALS_PER_HAND} maximal squeezes per hand</strong>, {TRIAL_SECONDS} s each, alternating hands (dominant first) so each hand
              rests while the other works. Then <strong>one {FATIGUE_SECONDS - 2} s hold</strong> with the dominant hand for the fatigue index. With the
              device, rests are 60 s.
            </p>
            <p>
              Posture and encouragement are fixed in the code. Saying “harder!” louder to one person than another changes the result, so the words
              never change.
            </p>
          </div>
          <dl className="spec-list">
            <dt>Posture</dt>
            <dd>Seated upright, elbow at 90°, forearm neutral, wrist straight</dd>
            <dt>Countdown</dt>
            <dd>3-2-1, then “Squeeze as hard as you can!”</dd>
            <dt>Order</dt>
            <dd>D1, N1, D2, N2, D3, N3, then the hold (D = dominant, N = non-dominant)</dd>
            <dt>Reported</dt>
            <dd>Best squeeze per hand; the higher of the two is compared with the norms</dd>
          </dl>
        </div>
      </section>

      <section className="doc-section" id="filtering">
        <div className="container two-col">
          <div className="prose">
            <h2 style={{ fontSize: "clamp(1.6rem, 3vw, 2.1rem)" }}>Filtering</h2>
            <p>
              Raw HX711 data carry about ±70 counts of noise (≈2 g). That barely moves the peak, but it badly disturbs anything that uses a slope,
              like the rate of force development.
            </p>
            <p>
              Metrics use a <strong>4th-order Butterworth low-pass at 10 Hz</strong>, run forwards and then backwards (“zero phase”). A normal filter
              delays the signal, which would make every squeeze look slower; running it both ways cancels the delay. The cutoff is kept below 0.4 × the
              measured sample rate so it stays valid at 10, 50 or 80 samples/s. The raw signal is saved unchanged.
            </p>
            <p>
              In a Monte Carlo test of 300 simulated trials, this filter reduced the spread of RFD error with little bias, while a 5-point moving
              average overestimated RFD consistently.
            </p>
          </div>
          <figure className="figure">
            <div className="frame">
              <img src="/images/filter_comparison.png" alt="Left: raw, moving average and Butterworth curves during the rise. Right: RFD error box plots over 300 simulated trials." loading="lazy" />
            </div>
            <figcaption>Raw vs moving average vs Butterworth on simulated trials.</figcaption>
          </figure>
        </div>
      </section>

      <section className="doc-section" id="metrics">
        <div className="container">
          <h2>Metrics</h2>
          <div className="table-wrap card">
            <table className="data">
              <thead>
                <tr>
                  <th>Metric</th>
                  <th>Definition</th>
                </tr>
              </thead>
              <tbody>
                {[
                  ["Onset", "First sample above 5 % of the trial's peak. A relative threshold, so sensor noise is not mistaken for the start of a squeeze."],
                  ["Peak force (kg)", "Highest filtered force in the trial. The best of three per hand is reported, matching how the norms were built."],
                  ["Time to peak (ms)", "Time from onset to the peak."],
                  [
                    "Rate of force development (N/s)",
                    `Slope of a least-squares line through force (in newtons, 1 kg = 9.81 N) over the first 200 ms after onset. Needs at least 5 samples in the window, so it is n/a below about ${MIN_RATE_HZ} samples/s.`,
                  ],
                  ["Fatigue index (%)", "(peak − mean of the final second of the 30 s hold) ÷ peak × 100."],
                  ["Asymmetry", "Left ÷ right peak, and how much weaker the weaker hand is (%). Shown without a verdict."],
                  ["Trial-to-trial CV (%)", "Standard deviation ÷ mean of a hand's three peaks: how repeatable the effort was."],
                ].map(([k, v]) => (
                  <tr key={k}>
                    <td style={{ fontWeight: 600, whiteSpace: "normal", minWidth: 160 }}>{k}</td>
                    <td style={{ whiteSpace: "normal", color: "var(--ink-2)" }}>{v}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="formula" style={{ marginTop: 16 }}>
            {"RFD = Σ(tᵢ − t̄)(Fᵢ − F̄) / Σ(tᵢ − t̄)²      for onset ≤ tᵢ ≤ onset + 200 ms"}
          </p>
        </div>
      </section>

      <section className="doc-section" id="quality">
        <div className="container two-col">
          <div className="prose">
            <h2 style={{ fontSize: "clamp(1.6rem, 3vw, 2.1rem)" }}>Trial check</h2>
            <p>
              A maximal squeeze has a typical shape: flat at zero, a fast rise, a steady hold. Four common faults change that shape, so each trial is
              described by five numbers and checked against simple rules, in this order:
            </p>
            <p>
              The Python version of the app can also use a Random Forest trained on 2,000 simulated curves (99 % test accuracy vs 92 % for the
              rules). Because it was trained only on simulated data, that number shows the pipeline works, not how it does on real people. This site
              uses the rules.
            </p>
          </div>
          <div className="card table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Flag</th>
                  <th>Rule</th>
                </tr>
              </thead>
              <tbody>
                <tr>
                  <td>False start</td>
                  <td className="mono" style={{ whiteSpace: "normal" }}>
                    mean force in first 300 ms &gt; 10 % of peak
                  </td>
                </tr>
                <tr>
                  <td>Slip</td>
                  <td className="mono" style={{ whiteSpace: "normal" }}>
                    biggest dip during the hold &gt; 25 % of peak
                  </td>
                </tr>
                <tr>
                  <td>Submaximal</td>
                  <td className="mono" style={{ whiteSpace: "normal" }}>
                    rise from 10 % to 90 % of peak &gt; 600 ms
                  </td>
                </tr>
                <tr>
                  <td>Good</td>
                  <td className="mono" style={{ whiteSpace: "normal" }}>
                    none of the above
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="doc-section" id="norms">
        <div className="container two-col">
          <div className="prose">
            <h2 style={{ fontSize: "clamp(1.6rem, 3vw, 2.1rem)" }}>Norms</h2>
            <p>
              Reference values come from Table 2 of <strong>Dodds et al. (2014)</strong>, which pooled twelve British studies (about 50,000 people,
              from childhood to over 90). The best grip is matched to the row with the same sex and the closest age.
            </p>
            <p>
              <strong>Z-score</strong> uses that row's mean and SD. The <strong>estimated percentile</strong> assumes grip strength is normally
              distributed within the age band. The <strong>T-score</strong> compares with the young-adult peak (men {PEAK.male.mean} ± {PEAK.male.sd}{" "}
              kg, women {PEAK.female.mean} ± {PEAK.female.sd} kg).
            </p>
            <p>
              The low-grip cut-offs equal a T-score of −2.5: for men 51.9 − 2.5 × 9.9 ≈ 27 kg, for women 31.4 − 2.5 × 6.1 ≈ 16 kg. They are defined for
              adults 65 and over, so they are only shown at those ages.
            </p>
          </div>
          <div className="card table-wrap">
            <table className="data">
              <thead>
                <tr>
                  <th>Cut-off</th>
                  <th className="num">Men</th>
                  <th className="num">Women</th>
                </tr>
              </thead>
              <tbody>
                {Object.entries(CUTOFFS).map(([name, v]) => (
                  <tr key={name}>
                    <td>{name}</td>
                    <td className="num mono">&lt; {v.male} kg</td>
                    <td className="num mono">&lt; {v.female} kg</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      <section className="doc-section" id="calibration">
        <div className="container two-col">
          <div className="prose">
            <h2 style={{ fontSize: "clamp(1.6rem, 3vw, 2.1rem)" }}>Calibration</h2>
            <div className="notice warn">
              <IconWarn />
              <div>
                <b>Current state: estimated.</b> The firmware uses 42,952 counts per kg, worked out from the datasheet (2.0 mV/V × 5 V, gain 128, 100
                kg). Real cells vary by about ±10 %, so forces and percentiles from the device are approximate until the known-mass calibration is done.
              </div>
            </div>
            <p>
              <strong>The plan (gate G3):</strong> load the cell exactly the way a squeeze does, with weighed plates from 0 to about 33 kg in ten
              steps, up and back down, three times. A straight-line fit gives counts per kg; the same data give nonlinearity, hysteresis and
              repeatability.
            </p>
            <p>
              Linearity will be reported as the largest deviation as a percentage of full scale, not as R². R² is close to 1 for almost any load cell,
              so it says little about accuracy.
            </p>
            <p>
              After that, agreement with a clinical Jamar dynamometer will be measured with <strong>Bland-Altman analysis</strong> (bias and limits of
              agreement). Correlation alone is not enough: two devices can be perfectly correlated and still disagree by a constant amount.
            </p>
          </div>
          <dl className="spec-list">
            <dt>Scale factor</dt>
            <dd className="mono">42,952 counts/kg (datasheet)</dd>
            <dt>Rest reading</dt>
            <dd className="mono">≈ +52,400 counts</dd>
            <dt>Noise</dt>
            <dd className="mono">≈ ±70 counts (≈ 2 g)</dd>
            <dt>Direction</dt>
            <dd>SIGN = −1: this cell reads negative under load, so the firmware flips it</dd>
            <dt>Sample rate</dt>
            <dd>10/s now; 80/s after tying the HX711 RATE pin high (enables RFD)</dd>
            <dt>Max test load</dt>
            <dd>34 kg (75 lb) including the hanger</dd>
          </dl>
        </div>
      </section>

      <section className="doc-section" id="limits">
        <div className="container">
          <h2>Limitations</h2>
          <ul className="refs" style={{ maxWidth: "80ch" }}>
            <li>The device is not yet calibrated with known masses, and not yet compared with a clinical dynamometer.</li>
            <li>Any validation will involve very few people (the builders), so it shows feasibility, not clinical accuracy.</li>
            <li>The norms come from British cohorts and may not represent other populations.</li>
            <li>The comparison uses the nearest age band instead of interpolating between bands.</li>
            <li>The estimated percentile assumes a normal distribution within each age band.</li>
            <li>The trial-check rules were tuned on simulated curves; they have not yet been tested on real faulty trials.</li>
            <li>This is an educational project. It is not a medical device and must not be used for diagnosis.</li>
          </ul>
          <h2 style={{ marginTop: 48 }}>References</h2>
          <ol className="refs" style={{ maxWidth: "90ch" }}>
            <li>
              Dodds RM, Syddall HE, Cooper R, et al. Grip strength across the life course: normative data from twelve British studies.{" "}
              <i>PLoS ONE</i> 2014;9(12):e113637.{" "}
              <a href="https://doi.org/10.1371/journal.pone.0113637" target="_blank" rel="noreferrer">
                doi:10.1371/journal.pone.0113637
              </a>
            </li>
            <li>Cruz-Jentoft AJ, et al. Sarcopenia: revised European consensus on definition and diagnosis (EWGSOP2). <i>Age and Ageing</i> 2019.</li>
            <li>Chen LK, et al. Asian Working Group for Sarcopenia: 2019 consensus update (AWGS 2019). <i>JAMDA</i> 2020.</li>
            <li>Leong DP, et al. Prognostic value of grip strength: findings from the PURE study. <i>The Lancet</i> 2015.</li>
          </ol>
          <div className="btn-row" style={{ marginTop: 32 }}>
            <Link className="btn btn-primary" to="/test">
              Run the test
            </Link>
            <a className="btn btn-secondary" href={REPO_URL} target="_blank" rel="noreferrer">
              Read the source
            </a>
          </div>
        </div>
      </section>
    </>
  );
}

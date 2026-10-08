# 13 — What you'll have learned (interview prep)

Read this once the device is built and calibrated. Everything below assumes you've actually done the work — the soldering, the firmware, the calibration runs. Interviewers find the gaps quickly, so only claim what you did.

---

## A word on honesty first

A lot of this project's design and documentation was drafted with an AI assistant. That's normal now and not something to hide — but **don't present the CAD script or the docs as work you wrote from scratch unless you rebuilt them yourself.** If you're asked, the strong answer is:

> "I used an AI assistant to generate and iterate on the CAD and documentation, and my job was to specify requirements, evaluate the designs, reject the ones that didn't work, and then build, wire, program and calibrate the device. I rebuilt the firmware myself step by step so I understood every line."

That's honest, and it describes a real skill: directing, checking and correcting a tool rather than trusting it. The "invalid geometry" story below is proof you did exactly that.

Things that are unambiguously yours once you've done them: the soldering, the firmware you rewrote, the wiring and debugging, the calibration data, the analysis, the report and the design decisions you made.

---

## 1. Skills, and how to say them

### Electronics and instrumentation (your core role)

| What you learned | How to say it in an interview |
|---|---|
| How a strain-gauge load cell works — a Wheatstone bridge turning microscopic bending into millivolts | "The full-scale signal is only about 10 mV. The whole instrument exists to measure that cleanly." |
| Why an amplifier/ADC (HX711) is needed and what gain means | "The HX711 amplifies 128× and digitizes to 24 bits — about 43,000 counts per kilogram." |
| Soldering, strain relief, continuity testing | "I learned the failure point is the solder joint on the cell's thin wires, so strain relief came first." |
| Reading a datasheet and using its numbers | "I used the rated output (2.0 mV/V) to predict the sensitivity before calibrating, as a wiring sanity check." |
| Systematic hardware debugging | "Isolate one thing at a time: board with Blink, then the sensor with the library example, then my own code." |

### Firmware (C++ on Arduino)

- Structure of embedded code: `setup()` runs once, `loop()` forever
- Reading a peripheral through a library, polling a "data ready" signal instead of using fixed delays
- Taring (averaging to set zero), scaling raw counts to engineering units, sign conventions
- Serial communication and designing a data format (`t_ms,raw,net,force_kg`) as an **interface contract** with your partner

**Say it:** "I wrote the firmware in four stages, testing each before the next — timing, raw read, zeroing, then scaling and output."

### Measurement and calibration (the most valuable skill here)

This is the part that separates an instrument from a gadget, and very few first-years can talk about it.

- **Calibration:** fitting a line from known masses to raw counts
- **Nonlinearity vs. hysteresis vs. repeatability** — three different kinds of error, measured three different ways
- **Why R² is misleading** and maximum residual as % of full scale is the honest figure
- **Verification with an independent point** — a mass you didn't calibrate with
- **Noise, drift and creep**, and how to measure each
- **Comparing to a spec:** anything worse than the load cell's datasheet came from your frame, mounting or reference masses
- **Calibrating through the real load path**, and checking direction before trusting any number

**Say it:** "My verification error on an unseen mass was X %. I measured nonlinearity, hysteresis and repeatability separately and compared each to the load cell's datasheet, which told me the extra error came from [the printed parts creeping / my reference masses]."

### Mechanical design

- **Load paths:** designing so force can only travel through the sensor, and why any other contact ruins the reading
- **Clearances and tolerances:** 3 mm seams, locating ledges instead of relying on hole positions
- **Designing for part variability:** slots so any supplier's hole spacing fits
- **Bolted joints:** thread engagement (1.5× diameter minimum), why axial loading makes slots safe
- **Design for manufacturing (3D printing):** print orientation, 45° self-supporting overhangs, layer direction vs. stress direction
- **Knowing when to remove a feature:** the overload stop, and why

**Say it:** "The one rule was that nothing except the load cell could connect the palm side to the finger side. Every feature either enforced that or made the part printable."

### CAD and 3D printing

- The CAD workflow: sketch, extrude/revolve, fillet, boolean cut, assembly
- Parametric design — change one number, everything updates
- STEP vs. STL, and opening/inspecting an assembly in Fusion 360 or FreeCAD
- Slicing in Bambu Studio: walls vs. infill, supports, brims, cost from mass

**Be precise here:** if you didn't write the CadQuery script, say you *specified, reviewed and modified* the design and inspected it in Fusion/FreeCAD. If you did the Onshape or CadQuery exercises in `10_software_and_skills.md`, say that.

### Software and data

- Python serial logging, CSV data handling
- Least-squares fitting with NumPy, residual plots with Matplotlib
- Writing a fake data source so software could be built before hardware existed
- Git and GitHub: commits, a public repo, collaborating on one codebase

### Engineering process

- Writing numeric, testable requirements before designing
- Verification checklist mapping each requirement to a test
- Gates with fallbacks planned in advance
- A build log recording decisions and failures
- Documenting limitations honestly

### Biomedical context

- Why grip strength matters clinically (sarcopenia cut-offs, the PURE mortality finding)
- Standardized testing protocols (seated, elbow at 90°) and why posture control matters
- The difference between an educational device and a medical device — and not making diagnostic claims

### Working with a partner

- Splitting work by ownership, with a written interface between the halves
- Git conflicts and weekly syncs
- Being able to explain your partner's half, not just your own

---

## 2. Stories for behavioural questions

Use the STAR shape: **S**ituation, **T**ask, **A**ction, **R**esult. Keep each under two minutes.

### "Tell me about a mistake you caught."
**The load cell that didn't exist.** The whole design was built around a slim 80 mm load cell. Before ordering, checking availability showed that shape only goes to about 50 kg — the 100 kg version isn't sold in Canada, and the obvious substitutes were three-wire half-bridges that wouldn't work. We re-specified the part and redesigned around it *before* spending anything. **Lesson:** confirm your critical component is buyable before designing around it.

### "Tell me about a time you didn't trust a result."
**The check that lied.** The CAD ran an automatic check that the load cell didn't collide with any printed part. On one version it reported the cell completely buried in plastic. Instead of redesigning, we checked the geometry itself and found the bolt slots had been modelled in a way that produced an invalid solid — so the check was running on corrupt data. Rebuilding the slots fixed it, and now every part is validated before any check runs. **Lesson:** a verification is only as good as what it's measuring.

### "Tell me about iterating on a design."
**Six versions, one rule.** The mechanical principle never changed — palm side to one end of the load cell, finger side to the other, nothing else touching. But the first versions were a bracket on a table, then two flat plates, then a lopsided clinical-style head. Each was rejected for a specific reason (not handheld, not symmetric, not intuitive) until a split, barrel-shaped grip made the principle obvious at a glance: two colours, two halves, one seam. **Lesson:** a design can be correct and still wrong for the user.

### "Tell me about debugging."
**First signal.** *(Fill in from your build log.)* What didn't work, how you isolated it — Blink, then the library example, then a multimeter on the HX711 supply — and what the cause was. If it worked first time, use the pin-assignment trap: the library example assigns the data and clock pins the opposite way to the wiring, so nothing appears and nothing reports an error.

### "Tell me about a trade-off."
**Removing the overload stop.** Earlier designs had an adjustable stop bolt to protect the load cell. The final design drops it: no hand reaches the 120 kg safe overload, drops load the cell along its strong axis, and a printed stop can't be made accurate to the half-millimetre it needs. Fewer parts, fewer adjustments, no loss of protection that mattered. **Lesson:** removing a feature can be the better engineering decision — if you can justify it.

---

## 3. Technical questions you should be able to answer

| Question | Short answer |
|---|---|
| How does a load cell work? | Strain gauges on a metal body change resistance as it bends; a Wheatstone bridge turns that into a small voltage proportional to force. |
| Why do you need the HX711? | The signal is ~10 mV full scale. The HX711 amplifies it 128× and digitizes to 24 bits. |
| What stops force bypassing the sensor? | The two halves are bolted to opposite ends of the load cell with a 3 mm seam everywhere else. Nothing else connects them. |
| Why slots instead of holes? | Hole positions vary between load cells. The force pulls along the bolts, not across them, so slots clamp just as well. |
| Why a 100 kg cell for a ~50 kg grip? | Safe overload margin. A 50 kg cell's safe limit is 60 kg, which a strong grip can reach. Resolution isn't the limit anyway. |
| What limits your accuracy? | Not the sensor — it resolves about a gram. Human grip varies 2–4 kg squeeze to squeeze. Instrument error comes from the printed parts, the mounting and the reference masses. |
| Nonlinearity vs. hysteresis? | Nonlinearity: departure from a straight line. Hysteresis: different reading at the same load depending on whether you're loading or unloading. |
| Why is R² not enough? | R² above 0.999 is easy and hides real nonlinearity. Max residual as % of full scale is the honest figure. |
| How did you calibrate? | Known masses hung through the same load path as a squeeze, ascending and descending, three runs; then verified against a mass not used in the fit. |
| How did you check direction? | Pressed by hand and hung a mass — both must move the reading the same way. |
| Why print upright? | Smoothest outer surface, minimal supports; stresses in the half-shell are low enough that the across-layer direction is safe. |
| What would you change? | *(From your report §7 — must be tied to something you measured.)* |

---

## 4. Resume bullets

Fill in real numbers. Never leave an `X` on a resume.

> **Hand Dynamometer — Personal Project** · Sept–Nov 2026
> - Built a handheld grip-strength instrument around a 100 kg single-point load cell, HX711 24-bit ADC and Arduino Nano; wrote C++ firmware and a Python logging and analysis pipeline.
> - Designed a split-grip enclosure in which the load cell is the only load path between palm and finger halves; verified zero interference between parts in CAD and printed on Bambu P1S printers.
> - Calibrated against verified masses through the operational load path (3 runs, ascending/descending); achieved X % verification error on an unseen mass and characterized nonlinearity, hysteresis, repeatability, noise and creep against the sensor datasheet.
> - Documented requirements, design iterations, verification checklist and calibration report in a public GitHub repository.

**One-line version** for the top of the entry:
> Handheld grip dynamometer, calibrated to ±X % — load cell, embedded C++, Python, 3D-printed enclosure.

---

## 5. How to talk about it in 60 seconds

> "I built a grip-strength dynamometer — the kind used clinically to screen for age-related muscle loss. It's a handle split into two halves around a load cell, and the key design rule was that nothing except the sensor could connect the palm side to the finger side, so all the force goes through it. I did the electronics and firmware — the sensor puts out about 10 millivolts at full load, so most of the work was getting that signal clean. Then I calibrated it with known weights, and the interesting part was separating the errors: nonlinearity, hysteresis, drift, creep. Comparing each against the sensor's datasheet told me the extra error was coming from [X], not the sensor. Final verification error was [X] percent."

Practise it out loud until it fits in a minute without notes.

---

## 6. Before any interview

- [ ] Every number in your bullets is real and you can explain where it came from
- [ ] You can explain your partner's half as well as your own
- [ ] You have one photo of the device on your phone
- [ ] You know your biggest source of error and how you know
- [ ] You can say what you'd change, tied to a measurement
- [ ] You can describe honestly which parts you built yourself

# 13 — Jamar-style two-handle concept (v4 prototype — concept only, not print-ready)

A possible **v4**: a clinical-style two-handle dynamometer in the spirit of the Jamar, built around the same CZL601 load cell, bolts and electronics as v3. Drafted as a concept on Oct 16. **This is a side project / prototype. v3 remains the design being built and calibrated; nothing here is ready to print.**

## Why this style

The Jamar is the clinical standard, and its adjustable grip span is how published grip-strength norms are measured. A two-handle version is a closer match when comparing results against those norms.

## How it works

The load cell can't go inside a handle in this style — the cell plus its walls is about 45 mm thick, so the grip would be far too fat. Instead the cell stands **upright in a body beside the grip**, roughly where the display sits on the commercial device.

- **Frame (grey, fixed):** the body holds the cell. The cell's cable end bolts to the back of the body, using the same 3-hole pattern that passed G0. Arms above and below reach out to the palm bar.
- **Palm bar (grey, separate):** bolts between the arms at one of **5 positions**, so the grip span adjusts like a Jamar's handle positions.
- **Finger part (black):** a bracket bolted to the cell's top end, with the finger bar hanging from it. There's a 20 mm gap behind it for the fingertips.

The squeeze still has only one path — through the load cell — the same principle as v3.

Concept checks that passed in CAD:

- The finger part stays at least 3 mm from the frame everywhere.
- The cell's bending zone is clear, the cable stays on the fixed side, and all 5 palm-bar positions fit.
- At 100 kg the finger bar sees about 9 MPa — fine if it's printed lying on its side.

## What's not designed yet

- Board mounts inside the body.
- How to print the frame — it's 181 mm long, so it may need splitting.
- The calibration fixture.
- **The 5 handle spacings are placeholders.** A Jamar has 5 lock positions and research commonly uses the 2nd, but the exact distances weren't confirmed. Measure a real Jamar (BME labs or a physio clinic) before matching them.

## Plan

Build v3 first, then this as v4 (option A from the design chat): the cell, electronics, firmware and calibration all carry over. Switching to this immediately would cost about another week of design and test prints before G2.

Sources:

- [Springer BMC Musculoskeletal Disorders (2018), Jamar 5 lock positions](https://link.springer.com/article/10.1186/s12891-018-1971-4)
- [PMC10584072, second handle position used for the Jamar](https://pmc.ncbi.nlm.nih.gov/articles/PMC10584072)

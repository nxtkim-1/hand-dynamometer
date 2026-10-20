# 09 — Day by day

**Start** Friday 25 September 2026 · **Finish** Sunday 8 November 2026 · **Buffer** 9–22 November

Starting a week later than first planned, but the finish date hasn't moved: the two-part design prints in ~9 hours instead of ~22, which absorbs the lost week.

**A** = printing, assembly, calibration · **B** = firmware, software, analysis

Every session: goal, steps, **Done when**, what to do if it goes wrong. One rule for the whole project: **nothing is done until it's committed and logged** in `docs/06_build_log.md`.

---

## Calendar

| Week | Dates | What happens | Gate |
|---|---|---|---|
| 1 | **Fri 25** – Sun 27 Sep | Order, repo, software, slice the coupon | — |
| 2 | Mon 28 Sep – Sun 4 Oct | Print coupon, parts arrive, solder, **first signal**, fit test, print the real parts | **G1** Wed 30 · **G0** Wed 30 |
| 3 | Mon 5 – Sun 11 Oct | Assemble, first squeeze, prepare calibration *(Thanksgiving weekend)* | **G2** Tue 6 |
| 4 | Mon 12 – Sun 18 Oct | Calibration and characterization *(reading week)* | **G3** Fri 16 |
| 5 | Mon 19 – Sun 25 Oct | Diagnose results, 30-second holds, photos, video | — |
| 6 | Mon 26 Oct – Sun 1 Nov | Write the calibration report | — |
| 7 | Mon 2 – Sun 8 Nov | Checklist, publish, swap halves, resume | **G4** Fri 6 |

---

# WEEK 1 · Fri 25 – Sun 27 Sep

---

### TODAY, FRI 25 · A · 20 min · Order the parts

It's evening, so this is the only thing that has to happen tonight. Shipping is the critical path — every day you wait, the whole project shifts a day.

1. Log into `den.uwaterloo.ca` with Duo. Check **Parts → Sensors (Force)** and **Arduinos**. If DEN has a 100 kg parallel-beam cell or a Nano, borrow instead of buying.
2. On Amazon.ca, order:
   - **Load cell** — the 100 kg parallel-beam cell (the Yosoo one you found, or the Yanmis listing). It's the cell only, no amplifier.
   - **HX711** — WWZMDiB 4-pack.
   - **Nano** — search *ELEGOO Nano V3 Boards with Mini-B USB Cables, 3-Pack*. Get the one **with cables**.
3. Check each delivery date. **If the load cell arrives later than Wed 30 Sep, look for a faster listing.** The Nano and HX711 usually ship from Amazon and arrive in 1–2 days; third-party sellers are slower.

**Done when:** three order confirmations with delivery dates.
**Log:** what DEN had, order numbers, delivery dates.

### TODAY, FRI 25 · both · 30 min · Read and look

1. Unzip the project. Open `images/assembly_exploded.png`.
2. Four pieces: grey palm half, load cell, black finger half, cover. The palm half bolts to the load cell's **bottom**, the finger half to its **top**. A 3 mm seam keeps them apart. That's the whole idea — make sure you both can say it in one sentence. Then read `docs/12_design.md`.
3. Read `README.md`.

That's it for tonight.

---

### SAT 26 · A · 20 min · Fasteners

Home Depot or any hardware store with a metric drawer:

| Qty | Item |
|---|---|
| **5** | M6 × 25 **button head** screw *(4 needed, 1 spare)* |
| 4 | M6 washer |
| 2 | M3 × 8 pan head screw |

Plus a **4 mm hex key** if you don't have one. Washers are not optional — the bolts go through slots.

### SAT 26 · A · 60 min · Bambu Studio and the coupon file

1. Install **Bambu Studio** (free, bambulab.com). Printer: **Bambu Lab P1S**, nozzle 0.4 mm.
2. Filament: **Bambu PETG Basic**. Process: **0.20 mm Standard**.
3. Drag in `cad/output/print_ready/fit_coupon_print.stl`. **Don't rotate it.**
4. Change: wall loops **3**, sparse infill **20 % gyroid**, support **off**.
5. Click **Slice plate**. Expect about **27 g, ~1 hour, ~$2**.
6. **File → Save project** as `fit_coupon.3mf`. This is what you bring to the RPC.
7. While you're in there, load `palm_half_print.stl` and `finger_half_print.stl` too — wall loops **4**, infill **40 % gyroid**, and for the finger half a 5 mm brim and **tree supports on**. Note grams and time. Save as `palm_half.3mf` and `finger_half.3mf`.

**Done when:** three `.3mf` files saved.

### SAT 26 · B · 60 min · Software setup

1. Install **Python 3**. On Windows, **tick "Add Python to PATH"**.
2. `pip install -r software/requirements.txt`
3. `cd software` then `python logger.py fake --label first_test`
4. Watch the numbers climb to ~40 kg and decay. Ctrl+C after 15 s. Open the CSV it made. Delete it.
5. Install the **Arduino IDE**. Tools → Manage Libraries → search **HX711** → install **Bogdan Necula**'s.

**Done when:** fake logging works and the HX711 library is installed. You understand `--fake` pretended to be the Arduino — this is why software never waits for hardware.

---

### SUN 27 · both · 60 min · GitHub and the contract

1. Both make GitHub accounts (professional usernames). Both install **GitHub Desktop**.
2. One person: File → Add local repository → the project folder → "create a repository here" → commit `Initial commit` → **Publish**, unticking "Keep this code private".
3. github.com → Settings → Collaborators → add your partner. They accept, then File → Clone.
4. Partner adds their name to the README Team section, commits, pushes. Other person clicks Fetch → Pull.
5. Add this to `docs/06_build_log.md`:

   > **Interface contract.** The Arduino sends one line per sample over USB at 115200 baud, ~10 Hz, as `t_ms,raw,net,force_kg`. This doesn't change without both of us agreeing.

6. Decide who is A and who is B.

**Done when:** both of you see each other's commits.
**If stuck:** the collaborator invite email is usually in spam.

### SUN 27 · B · 45 min · Read the firmware

Open `firmware/grip_firmware/grip_firmware.ino` in the Arduino IDE. Write your own one-line comment above each block. You should be able to answer:

- Why does `doTare()` average 20 readings instead of taking one?
- What does `SIGN` do?
- Why is `COUNTS_PER_KG` 1.0 right now?
- Why does the loop wait for `scale.is_ready()` instead of using `delay(100)`?

---

# WEEK 2 · Mon 28 Sep – Sun 4 Oct

The decisive week.

---

### MON 28 · A · 30 min + 1 h print · Print the fit coupon

1. Take `fit_coupon.3mf` to the **Rapid Prototyping Centre**. Ask how they want files (USB or upload) and whether it's walk-up or queued.
2. Choose **standard PETG — grey**. It's $0.07/g, so about $2.
3. Print it. You don't need the load cell yet — you'll test the fit the day it arrives.

**Done when:** coupon in your hand.

### MON 28 · B · 45 min · Understand the calibration maths

1. `cd data` then `python ../software/calibrate.py example_calibration_points.csv`
2. Open the two PNGs it made. Write answers in the build log:
   - What is `COUNTS_PER_KG` physically?
   - Why is R² a weak measure of linearity, and what's reported instead?
   - What is hysteresis, and why does the data have `up` and `down` rows?
   - Why three runs?

---

### TUE 29 · A · 30 min · Measure the cell (when it arrives)

1. Unpack carefully. **Don't pull on the wires.**
2. Count the wires. **Must be four.** Three means the wrong part — return it.
3. Calipers: length, width, thickness. Expect about 130 × 30 × 22 mm.
4. Test that an M6 screw threads into both ends.
5. Measure from each **end face** to each hole centre — four numbers.
6. Photo of the cell beside the calipers.

### TUE 29 · B · 50 min · Solder

1. Slide heat-shrink onto the wires **before** soldering.
2. Strip 3 mm off each cell wire.
3. Solder to the HX711: **red → E+, black → E−, green → A+, white → A−.** Check the label on your cell first.
4. Shrink the tubing.
5. **Zip-tie the four wires together 30 mm from the cell.** Without this they break at the joint — the most common failure in this build.
6. HX711 → Nano with jumper wires: **VCC → 5V, GND → GND, DT → D3, SCK → D2.**

---

### WED 30 · B · 45 min · **GATE G1 — first signal**

1. Plug in the Nano. Tools → Board → Arduino Nano. Tools → Port → the new one.
2. Upload **File → Examples → Basics → Blink**. The LED blinks → board and cable work.
3. Upload **File → Examples → HX711 → the basic example**. Open Serial Monitor.
4. Press the end of the cell with your thumb.

**Done when:** the number changes when you press, and returns when you let go.

| Problem | Fix |
|---|---|
| No port shows up | Install the CH340 driver; or the cable is charge-only |
| Upload fails | Tools → Processor → "ATmega328P (Old Bootloader)" |
| Nothing prints | DT and SCK swapped, or HX711 not powered |
| Numbers never change | A+/A− not connected, or a wire broke |
| Numbers jump wildly | Loose wire — wiggle each one |

**If this isn't working by Sunday 4 October, stop and get help in person** — DEN staff, a TA, or the robotics club.

### WED 30 · A · 40 min · **GATE G0 — fit test**

1. Stand the cell's end on the coupon's ledge.
2. Push an M6 × 25 **with a washer** through each slot into the cell. Start both by hand.
3. Tighten until snug, then a quarter turn more. No harder.
4. Check: the cell sits flat on the ledge, and a strip of paper slides freely in the 2 mm gap between cell and coupon.

**Done when:** both bolts are in and the paper slides.

| Problem | Fix |
|---|---|
| Holes don't line up with the slots | In `cad/dynamometer_cad.py`, widen `SLOT_NEAR` / `SLOT_FAR`, run it, reprint the coupon |
| Bolts are tight in the slots | Raise `SLOT_W` by 0.2, reprint |
| Cell rocks on the ledge | Scrape the ledge flat with a blade |

If you changed anything, run `python cad/dynamometer_cad.py` and re-slice the palm and finger files before printing them.

---

### THU 1 OCT · A · 20 min + ~9 h printing · Print the real parts

1. Take `palm_half.3mf` and `finger_half.3mf` to the RPC. Also print `cover_print.stl` (3 walls, 20 %).
2. Suggested colours: **palm grey, finger black** — makes the two-part idea obvious in photos.
3. Total about 150 g → about $10–12.

### THU 1 OCT · B · 75 min · Write the firmware yourself

Build it in four steps, testing each before the next:

1. Blink (done).
2. Print `millis()` over serial at 115200.
3. Print a raw HX711 reading using the library.
4. **Your own version:** tare at start by averaging 20 reads, subtract the offset, divide by `COUNTS_PER_KG`, print `t_ms,raw,net,force_kg`.

Then compare yours with `grip_firmware.ino`. Upload whichever you trust.

---

### FRI 2 · B · 50 min · Logger on real hardware

1. Close the Arduino Serial Monitor (only one program can use the port).
2. `python software/logger.py COM3 --plot` (your port name will differ).
3. Press the cell. The live plot should follow your hand.
4. Open the CSV. Time should step by about 0.1 s — that's 10 samples a second.

### SAT 3 · A · 45 min · Clean up the prints

1. Peel off the brims.
2. Turn a 6.5 mm drill bit **by hand** through each slot to clear stringing. Don't enlarge them.
3. Check both ledges are flat. Scrape off any bulge — a bulged ledge tilts the cell.
4. Lightly sand the outside of both halves where your hand goes.

### SUN 4 · — · Buffer

Catch up on anything that slipped. **Hard deadline for G1 (first signal).**

---

# WEEK 3 · Mon 5 – Sun 11 Oct

---

### MON 5 · both · 45 min · Assemble

Follow `docs/03_assembly.md` steps 3–6:

1. Feed the load cell cable down into the base pod. Stand the cell on the **palm half**'s ledge; two M6 × 25 with washers through the slots.
2. **Finger half** over the top end — its ledge caps the cell; two M6 × 25 with washers.
3. Nano and HX711 into the base pod. Cover on with two M3 × 8.

**Log:** photo at each step.

### TUE 6 · both · 45 min · **GATE G2 — clearances and first squeeze**

1. Paper slides freely down both side seams between grey and black.
3. Paper slides freely through the top seam (dome) and bottom seam (base).
5. Upload the firmware, run the logger, squeeze hard, release.

**Done when:** all three gaps are clear and the reading goes back to zero after you let go.

**If it doesn't return to zero:** something is touching across a seam. Fix it before calibrating — otherwise every number afterwards is wrong.

### WED 7 · A · 60 min · Gather and weigh the masses

1. Collect things totalling about 35 kg in roughly 5 kg steps: water jugs (1 L = 1 kg), gym plates, or DEN calibration weights.
2. **Weigh every one** on a scale and write down the real number. A "10 kg" plate is often 9.7 or 10.3.
3. Label each with tape.

### THU 8 · A · 45 min · Build the rig

1. Clamp the **calibration cradle** in a bench vise. Lay the device in it **grey palm half down**, base at the slotted end. Zip-tie over the **base pod only** — never around the black half.
2. Tie a strong cord through the hole in the **dome**. Hang an empty bucket or bag.
3. **Direction check:** press the black half toward the grey half by hand → `net` goes up. Put a weight in the bucket → `net` must go up **too**. If one goes down, the device is clamped the wrong way round.

### THU 8 · B · 30 min · Data sheet

1. Create `data/calibration_points.csv` containing only this line: `mass_kg,net_counts,direction,run`
2. Print a paper table with those four columns and 48 rows.

### FRI 9 – SUN 11 · — · Thanksgiving weekend, off

---

# WEEK 4 · Mon 12 – Sun 18 Oct — Calibration *(reading week)*

The most important week. This is where it becomes a measuring instrument.

---

### MON 12 · Thanksgiving, off

### TUE 13 · both · 2 h · Calibration run 1

1. Power it up with the empty bucket hanging. **Wait 5 minutes** — electronics drift while warming up.
2. Start `python software/logger.py COM3 --label cal_run1` with the empty bucket hanging. That reboots the Nano, which zeroes itself. Wait 5 s. **Never restart the logger mid-run — it re-zeroes with the mass on.**
3. **Going up:** add weight 1, wait 10 s, write down `net`. Add weight 2, wait, write. Continue to the top.
4. **Coming down:** remove one at a time, writing down `net` each time, back to empty.
5. Type all 16 readings into the CSV.

**Tip:** one person handles weights and reads numbers out, the other writes.

### WED 14 · both · 2 h · Runs 2 and 3

Same again, twice. Zero it before each run. If one run looks different, keep it and note why — the spread between runs is your repeatability result.

### THU 15 · B · 45 min · Fit and sanity check

1. `cd data` then `python ../software/calibrate.py calibration_points.csv`
2. Check `COUNTS_PER_KG` is roughly **43,000**:

   | You got | Meaning |
   |---|---|
   | 30,000 – 56,000 | Correct |
   | About 21,000 | Wrong HX711 channel, or a 1.0 mV/V cell |
   | About 86,000 | Possibly a 50 kg cell |
   | Negative | Two signal wires swapped — set `SIGN = -1` |

3. Paste the number into `grip_firmware.ino` as `COUNTS_PER_KG`. Upload.

### FRI 16 · both · 40 min · **GATE G3 — verification**

1. Hang a weight you **didn't** use in calibration, e.g. 12.4 kg.
2. Read `force_kg`. Error = (reading − true) ÷ true × 100 %.
3. Repeat with a second one.

**Target: within 2 %.** If not, don't tweak until it passes — find out why (usually a weight not weighed properly, or something rubbing).

### SAT 17 · A · 30 min active · Noise and drift

1. Nothing hanging. Log 60 seconds → standard deviation of the readings = your **noise**.
2. Nothing hanging. Log 30 minutes (go do something else) → how far it wandered = your **drift**.

### SUN 18 · A · 20 min active · Creep

Hang about 20 kg. Log 30 minutes. How much did the reading change? If it's much more than the cell's spec (±0.023 % of 100 kg), that's the plastic parts slowly bending — a real result to report.

---

# WEEK 5 · Mon 19 – Sun 25 Oct

---

### MON 19 · B · 90 min · Fill the results table

Fill every row of the table in `docs/05_calibration_report.md`. No blanks.

### TUE 20 · both · 60 min · Why is it wrong where it's wrong?

Compare each of your numbers with the load cell's spec. Wherever yours is worse, ask which caused it:

- **Plastic parts** bending or creeping?
- **Something rubbing** — redo the paper checks.
- **The weights** — how accurate was your scale?
- **Temperature** — did the room change between runs?

Write the answers into section 4.4 of the report. **This is exactly what interviewers ask about.**

### WED 21 & THU 22 · both · 45 min each · 30-second holds

Wednesday person A, Thursday person B.

1. Sit, feet flat, **elbow bent at 90°**, thumb pointing up.
2. Hold the device relaxed, not squeezing.
3. Start `python software/logger.py COM3 --label hold_A_left`. It re-zeroes as it starts, so keep your hand relaxed and **wait 5 seconds** before squeezing.
4. On "go": squeeze as hard as possible and **keep squeezing for 30 seconds**. Don't pace yourself.
5. Stop logging. Rest 2 minutes. Other hand.

Say the same encouragement each time — it measurably changes results.

### FRI 23 · B · 45 min · Analyse the holds

`python software/analyze_hold.py <file>` for each of the four. Record peak, time to peak, force at 30 s, and percent drop.

### SAT 24 · A · 60 min · Photos

Plain background, good light:

1. A hand squeezing it, elbow at 90°
2. Side view
3. Three-quarter view
4. Close-up of the seam between the grey and black halves
5. The four parts laid out
6. The calibration rig with a weight hanging
7. The base pod open, electronics inside

### SUN 25 · both · 45 min · Demo video

30 seconds: hands squeezing, live plot visible. One take is fine.

---

# WEEK 6 · Mon 26 Oct – Sun 1 Nov — Write the report

| Day | Who | Write |
|---|---|---|
| **Mon 26** | A, 90 min | §1 what it is · §2 how force gets through the cell · §3 how you calibrated |
| **Tue 27** | B, 90 min | §4 results table + plots + why · §5 the holds |
| **Wed 28** | both, 60 min | §6 limitations |
| **Thu 29** | both, 45 min | §7 what you'd change |
| **Fri 30** | B, 60 min | README: results table, photos, video link |
| Sat–Sun | — | Buffer |

**§2 matters most.** Explain why force can't bypass the cell: two parts, opposite faces, 2 mm of air, nothing else joining them.

**§6 is where you earn respect.** Be specific: "calibrated to 35 kg, not the full 100", "weights checked on a scale with 50 g resolution", "plastic parts crept 0.4 % over 30 minutes", "tested on two people only", "educational, not for diagnosis".

**§7 must be concrete:** not "make it better", but "thicken the palm half's wall from 5 to 7 mm, where we measured 0.4 mm of flex at 30 kg."

---

# WEEK 7 · Mon 2 – Sun 8 Nov — Finish

| Day | Who | Task |
|---|---|---|
| **Mon 2** | both, 90 min | Go through every line of `docs/08_verification_checklist.md` |
| **Tue 3** | both, 60 min | Fix or explain anything that failed |
| **Wed 4** | A, 45 min | Tidy the repo. Download it fresh and check a stranger could follow it |
| **Thu 5** | B, 45 min | Final README. Add GitHub topics. Pin it to your profile |
| **Fri 6** | both, 60 min | **G4 — swap halves** (below) |
| **Sat 7** | both, 45 min | Resume bullets with real numbers. Add to LinkedIn |
| **Sun 8** | — | **Done** |

### Fri 6 — swap halves

A explains the software to B; B explains the hardware to A. Then quiz each other until neither hesitates:

- Why two printed parts instead of one frame?
- What stops force going around the load cell?
- Why slots instead of round holes, and why is that safe?
- Nonlinearity vs hysteresis — what's the difference?
- Why calibrate by hanging weights instead of pressing by hand?
- Why a 100 kg cell to measure a 50 kg grip?
- What limits your accuracy — the sensor, or something else?
- What's your biggest source of error, and how do you know?

---

# Buffer · 9 – 22 Nov

Only if something slipped. Otherwise, study for exams.

# If you fall behind

Cut in this order: creep test → one person's holds → video → extra characterization.
**Never cut:** calibration, the verification weight, or the limitations section.

# If you only have 30 minutes

Add a build-log entry with photos and commit. Steady small commits over seven weeks look far better than a burst at the end.

# Total effort

About **35 hours each**, roughly 5 hours a week.

# 03 — Assembly

> **Current design: v3 compact box (released 2026-10-16).** The steps directly below are the ones to follow. The older text further down is for the round-base version and is kept for history.

## v3 compact box — hardware

| Qty | Item | Where |
|---|---|---|
| 3 | M6 × 25 button head + M6 washer | Palm half → load cell's bottom end (cable end) |
| 3 | M6 × 25 button head + M6 washer | Finger half → load cell's top end |
| 4 | M3 × 10 pan head | Cover → box (self-tap into the printed pilots) |
| - | double-sided foam tape | Nano on its rail, HX711 on the end wall above its shelf |

Tools: 4 mm hex key, small Phillips screwdriver.

## v3 compact box — steps

1. **Electronics first, on the bench.** Solder, then pass G1 (a number on screen that changes when the cell is pressed) before anything goes into the box. The 4 link wires between HX711 and Nano should be long enough to reach from the end wall down to the Nano (about 8 cm).
2. **Clean the prints.** Pull the supports out of the box through its open bottom. Run a 7 mm drill bit by hand through the six bolt holes to clear stringing.
3. **Feed the cable end in.** Cover off, palm half standing upright. Lower the HX711 end of the cable down through the opening in the top of the box until it hangs out of the open bottom.
4. **Lower the cell in.** Bring the cell to the open side of the palm half, cable end down. Slide it down until it sits on the ledge. The cable goes down the slot in the box top as the cell drops. Thread the 3 bolts + washers from the palm side, snug, then 1/8 turn. Paper must slide freely in the 3 mm gap on both sides.
5. **Coil the spare cable** on the floor of the box, round loops against the walls, no tighter than a 2 cm loop. Two loops side by side, up to four layers. Do not crush or kink it.
6. **Mount the boards.** HX711 on its shelf on the end wall, foam tape behind it. Nano on the rail of the cover with foam tape, USB end towards the window. Check the USB plug reaches the Nano through the window before closing.
7. **Close the box.** Cover on with 4 × M3 × 10. Nothing should be pinched.
8. **Finger half on.** Bolt it to the top end of the cell with 3 bolts + washers. Check the 3 mm seam all round the halves and above the box (paper slides everywhere). If anything rubs, stop and find out why: a rub is a force leak.
9. **G2:** with the logger running, squeeze and release. The reading returns to zero.

---

## (older round-base version, kept for history)

About 30 minutes. Two printed halves, four M6 bolts, one hex key.

**Tools:** 4 mm hex key, small Phillips screwdriver, and the soldering kit for step 1.

![Exploded](../images/final_exploded.png)

## The idea

The **grey palm half** bolts to the load cell's **bottom** end. The **black finger half** bolts to its **top** end. The two halves never touch — a 3 mm seam runs between them all the way round. Squeeze, and the only thing joining them is the load cell. See `12_design.md` for the full explanation.

## Hardware

| Qty | Item | Where |
|---|---|---|
| 2 | M6 × 25 button head + M6 washer | Palm half → load cell's bottom end |
| 2 | M6 × 25 button head + M6 washer | Finger half → load cell's top end |
| 2 | M3 × 8 pan head | Cover → base |

The load cell's holes are threaded — it is its own nut.

## Step 1 — Electronics first

Do the whole of `11_firmware_tutorial.md` up to "first signal" **before** anything goes into the housing. Solder, strain-relieve, and prove the load cell reads. Never mount a cell you haven't seen working.

## Step 2 — Clean the prints

1. Peel off the brims.
2. Turn a 6.5 mm drill bit **by hand** through the four slots to clear stringing. Don't enlarge them.
3. Check both ledges are flat — scrape off any bulge with a blade. A bulged ledge tilts the load cell.

## Step 3 — Load cell into the palm half

1. Feed the load cell's cable down through the bore into the base pod.
2. Stand the load cell's **bottom** end on the ledge inside the palm half, its flat face against the boss.
3. From outside the palm half, push an M6 × 25 **with a washer** through each slot into the load cell. Start both by hand before tightening either.
4. Tighten **snug plus a quarter turn.** Over-tightening distorts the load cell and shifts its zero.

**Check:** the washers and heads sit down inside the counterbores, flush with the surface.

## Step 4 — Finger half onto the top end

1. Lower the finger half over the load cell so its top ledge sits on the cell's top end face, and the dome clears the palm half by the 3 mm seam.
2. From the black side, push an M6 × 25 **with a washer** through each slot into the top of the load cell.
3. Snug plus a quarter turn.

## Step 5 — Electronics into the pod

1. HX711 and Nano into the pod. A dab of hot glue under each keeps them from rattling.
2. Nano's USB socket lined up with the port in the side of the base.
3. Cover on with two M3 × 8 screws.

## Step 6 — The seam check (every time you reassemble)

1. ☐ **Side seams:** slide a sheet of paper down both vertical seams between grey and black. It must pass freely the whole length.
2. ☐ **Top seam:** paper slides freely between the dome and the top of the palm half.
3. ☐ **Bottom seam:** paper slides freely between the bottom of the black half and the top of the base.
4. ☐ **No wires across a seam.** The load cell cable runs down inside the grey half only.

Then hold it and squeeze hard. It should feel completely solid — the halves move far less than a millimetre. No clicking, no scraping.

## Step 7 — First real reading

Upload `firmware/grip_firmware/grip_firmware.ino`, close the Serial Monitor, then:

```
python software/logger.py COM3 --plot
```

Squeeze. The trace should rise and fall with your hand and **return to zero when you let go.** If it goes negative, set `SIGN = -1` in the firmware and upload again.

## If something's wrong

| Symptom | Likely cause |
|---|---|
| Doesn't return to zero | Something is touching across a seam — redo step 6 |
| Reading lower than expected | Same — force is going around the load cell |
| Clicking when you squeeze | A bolt head proud of its counterbore, or a seam touching |
| Nothing at all | Go back to the tutorial's "first signal" troubleshooting |

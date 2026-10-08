# 03 — Assembly

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

# Firmware, step by step

Four small programs. Each one adds one idea to the one before, and step 4 is the full
firmware (`../grip_firmware/grip_firmware.ino`, v1.0) plus a "waiting for HX711" message.
Written as teaching material on 2026-10-16.

| Step | Folder | Adds | You know it works when |
|---|---|---|---|
| 1 | `step1_hello_serial` | setup/loop, Serial, millis() | a climbing number every 100 ms |
| 2 | `step2_read_raw` | the HX711 library, polling | the number jumps when you press the cell (G1) |
| 3 | `step3_tare` | functions, averaging, a zero offset | about 0 at rest, back to 0 after a squeeze |
| 4 | `step4_csv_and_commands` | CSV output, kg, the `t` command | logger.py saves clean lines |

## How to use them (so the work is yours)

1. Read the step's comments, then **type it yourself** into `firmware/my_firmware/my_firmware.ino`. Don't paste.
2. Upload, check, do the "Try" line at the top.
3. When it works, commit it that day: `my firmware step N: ...` (table in `docs/07_github_guide.md`).
4. If it breaks and you fix it, commit the fix too, with what was wrong.

One step a day is a good pace. Four days of real commits is the version history worth showing.

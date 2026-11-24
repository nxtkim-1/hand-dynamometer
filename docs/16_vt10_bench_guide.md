# 16 - Bench sheet: proof load and calibration (VT-09 + VT-10), about 20 minutes

**VT-09:** the printed frame holds about 30 kg. **VT-10:** find counts per kg and check it on a weight the fit never sees.
One session, one logger recording. Print this and fill it in.

## Before

1. Weigh the hanger (with strap and carabiner) and the 10, 25, 45, 35, 50, 5 lb plates. Write the kg below.
2. Upload the firmware (`SIGN = 1`), close the Arduino IDE.
3. Device upside down (palm bar down) on two blocks; strap over the finger bar only.
4. Start the logger and leave it running:
   ```
   cd C:\Users\nxtho\.t3\projects\gripdynamometer\data
   python ..\software\logger.py COM7 --label g3_v42
   ```

Hanger: ____ kg  10: ____  25: ____  35: ____  45: ____  50: ____  5: ____

## Steps (about 20 s each, hands off)

Expected `net` assumes a 1.0 kg hanger; add about 43,000 per extra kg. Range is ±10 %.

| # | Hang | Expected `net` | Seen | Logger s |
|---|---|---|---|---|
| 1 | nothing, 30 s | 0 ± 100 | | |
| 2 | hanger | 43,000 (positive!) | | |
| 3 | +10 lb | 238,000 | | |
| 4 | +25 lb | 530,000 | | |
| 5 | +45 lb | 920,000 | | |
| 6 | +65 lb (50+10+5), **hold 2 min** | 1,309,000 | start: / end: | |
| 7 | +45 lb | slightly above step 5 | | |
| 8 | +25 lb | slightly above step 4 | | |
| 9 | +10 lb | slightly above step 3 | | |
| 10 | hanger | about step 2 | | |
| 11 | nothing, 30 s | 0 ± 200 | | |
| 12 | 35 lb plate alone (check) | 725,000 | | |

Ctrl+C, then send the file name from `data\`.

Quick check while you go: `net ÷ kg` should be about the same at every step.
If step 2 reads negative, stop: the sign or the rig is upside down.

## Pass

| | Pass |
|---|---|
| Counts per kg | within ±30 % of 42,952 |
| Range | at least 30 kg |
| Check weight (step 12) | within 2 % |
| Zero (step 11) | within ±200 counts |
| Frame at step 6 | no crack, creak or bending |

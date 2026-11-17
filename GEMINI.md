# Project Guidelines & Coding Rules: Focus Applied Technologies / DBW

## Firmware & Microcontroller (PicBasic Pro / PBP) Standards
Whenever writing, reading, or editing PicBasic Pro (`.pbp` / `.bas`) or assembly firmware for PIC microcontrollers (e.g. PIC18F46K22, PIC18F26K22):

1. **Coding Style & Structure:**
   - Follow the **Horizon / Focus Applied Technologies** style found in `D:\PBP` (e.g., `ThrottleRobot.bas`, `ClutchRobot.bas`, `DBW.pbp`).
   - Group concise assignments on one line with colons where appropriate (e.g., `t=0:led1=1`, `num=0`).
   - Keep variable names short and conventional (`tps`, `tpsav`, `th`, `Plo`, `Phi`, `num`, `j`, `i`, `s`, `cyc`).
   - Keep register declarations clear and explicit (`OSCCON`, `ANSELx`, `TRISx`, `TXSTA1`, `RCSTA1`, `BAUDCON1`, `SPBRG1`).

2. **Language in Comments and Strings:**
   - **STRICT RULE:** Never use Malay or informal language in code comments or serial strings. All comments, banners, and CLI messages MUST be in technical, concise English.

3. **Loop Efficiency & Timing:**
   - Keep the main loop fast and non-blocking.
   - For analog throttle inputs, always apply the running average filter: `tpsav = (3 * tpsav + tps) / 4`.
   - For servo control, use 50Hz RC timing (~20ms frame: `pulsout ServoPin, th` with `pause 18`).
   - Use non-blocking serial checking (`if j=0 then Hserin 10, BAU, [s]`) with label `BAU:` (*Business As Usual*).

4. **EEPROM & Calibration:**
   - Store calibration values (e.g., Idle pulse `Plo`, WOT pulse `Phi`, power cycles `cyc`) in on-chip EEPROM.
   - Provide the interactive serial CLI menu (`###L`, `###H`, `Z` to burn, `Q` to quit) for on-the-fly dyno calibration without reflashing.

---
name: horizon-pbp-style
description: >-
  Coding standards and architectural style guide for PicBasic Pro (PBP) firmware
  developed at Focus Applied Technologies / Horizon (D:\PBP). Use whenever
  writing, modifying, or refactoring PIC microcontroller code for dyno controllers,
  throttle actuators, DBW modules, and engine test cell equipment.
---

# Focus Applied Technologies (Horizon) PicBasic Pro (PBP) Coding Standard

This skill encapsulates the efficient, low-overhead PicBasic Pro firmware design patterns used across Focus Applied Technologies projects (e.g., `ThrottleRobot.bas`, `ClutchRobot.bas`, `DBW.pbp` in `D:\PBP`).

## Core Principles

1. **Comments & Strings in English Only:**
   - Never use Malay or informal language in code comments, terminal banners, or CLI prompt strings. All documentation in source code must be in clean, technical English.
2. **Extreme Runtime Efficiency:**
   - Avoid slow floating-point operations. Use scaled integer math and fast linear interpolation.
   - Keep the main loop tight and predictable (~20ms for 50Hz servo timing or ~35ms for standard control).
3. **Non-Blocking Serial Communications:**
   - Never let `HSERIN` block the control loop. Use a short timeout jumping to `BAU:` (*Business As Usual*).
4. **Permanent In-Circuit Calibration:**
   - Store limits and calibration offsets in EEPROM.
   - Provide interactive serial CLI commands (`###L`, `###H`, `Z` to burn, `Q` to quit) so calibration can be performed on the fly via PuTTY/terminal without recompiling.

---

## Code Structure Template

```pbp
'****************************************************************
'*  Name    : <MODULE_NAME>.BAS                                 *
'*  Author  : Horizon / Focus Applied Technologies (c) <YEAR>   *
'*  Target  : <BOARD_NAME> (MCU PIC <MODEL> @ <FREQ>MHz)        *
'*  Purpose : <CLEAR_1_TO_2_LINE_DESCRIPTION>                   *
'****************************************************************
'DECLARATION *******************************************************************
'OSCILLATOR=====================================================================
OSCCON = %01110111                      'HFINTOSC configuration
DEFINE OSC 16
DEFINE ADC_BITS 8                       '8-bit: 0-255 (or 10-bit: 0-1023)

'I/O CONFIG=====================================================================
ANSELA = %00000000                      'Explicitly define analog vs digital
TRISA  = %11111111                      '1=Input, 0=Output
ANSELB = %00000000
TRISB  = %11111111
ANSELC = %00000000
TRISC  = %10111011
ANSELD = %00010000                      'e.g. ANSD4 for AN24 TPS input
TRISD  = %11111011

'HSERCOM Setup =================================================================
TXSTA1   = %00100100                    'TX enabled, BRGH=1
RCSTA1   = %10010000                    'SPEN=1, CREN=1
BAUDCON1 = %01001000                    'BRG16=1
SPBRG1   = 160                          '9600 baud @ 16MHz
SPBRGH1  = 1

'PORT MAPPING & VARIABLES=======================================================
ServoPin        var PORTC.2             'Output pin
LED1            var PORTD.2             'Status LED
i               var byte                'General counter
j               var byte                'Telemetry/loop cadence counter
s               var byte                'Serial character buffer
t               var word                'Blink timer
tps             var word                'Raw ADC input
tpsav           var word                'Running average filtered input
th              var word                'Pulse width / output value
Plo             var word                'Low limit (Idle)
Phi             var word                'High limit (WOT)
num             var word                'Numeric accumulator for serial parser
cyc             var word                'Power cycle counter

'EEPROM=========================================================================
' Store default values as MSB, LSB byte pairs
data 1,164, 2,168, 0,0

'INITIALIZATION*****************************************************************
clear
read 0, Plo.byte1 : read 1, Plo.byte0
read 2, Phi.byte1 : read 3, Phi.byte0
read 4, cyc.byte1 : read 5, cyc.byte0
cyc = cyc + 1
write 4, cyc.byte1 : write 5, cyc.byte0

'Sanity boundary check
if (Plo < 300) or (Plo > 600) then Plo = 420
if (Phi < 500) or (Phi > 900) then Phi = 680
if Plo >= Phi then Plo = 420 : Phi = 680

Hserout ["Focus Applied Technologies - Controller Initialized", 13]

Main:'**************************************************************************
    'Dynamic heartbeat LED
    t = t + 1
    if t > tps then led1 = 0
    if t = 200 then t = 0 : led1 = 1

    'Read ADC and apply running average filter
    adcin 24, tps
    tpsav = (3 * tpsav + tps) / 4

    'Linear interpolation & failsafe
    if tpsav < 4 then
        th = Plo
    else
        th = Plo + (Phi - Plo) * tpsav / 255
    endif

    'Clamp limits
    if th < Plo then th = Plo
    if th > Phi then th = Phi

    'Output actuator pulse
    pulsout ServoPin, th
    pause 18                            'Complete 20ms frame for 50Hz RC servo

    'Telemetry streaming cadence
    j = j + 1
    if j = 25 then
        j = 0
        Hserout [#tpsav, ",", #th, ",", #((tpsav * 100) / 255), "%", 13]
    endif

    'Non-blocking serial CLI check
    if j = 0 then
        Hserin 10, BAU, [s]
        num = 0
        Hserout ["Commands: ###L=Idle, ###H=WOT, Z=Burn, Q=Quit", 13]
        GetChar:
        Hserin 10000, BAU, [s]
        Hserout [s]
        if s = "Q" then goto BAU
        if (s >= 48) and (s <= 57) then
            num = num * 10 + s - 48
            goto GetChar
        endif
        select case s
            case "L"
                Plo = num : Hserout [" -> Set Low: ", #Plo, 13] : num = 0
            case "H"
                Phi = num : Hserout [" -> Set High: ", #Phi, 13] : num = 0
            case "Z"
                write 0, Plo.byte1 : write 1, Plo.byte0
                write 2, Phi.byte1 : write 3, Phi.byte0
                Hserout [" -> Burned.", 13]
                goto BAU
            case "Q"
                goto BAU
        end select
        goto GetChar
        BAU: 'Business As Usual
    endif
goto Main
```

## Key Idioms & Conventions to Always Follow

* **Variable Names:** Keep them short and standard (`tps`, `tpsav`, `th`, `Plo`, `Phi`, `num`, `j`, `i`, `s`).
* **Multi-statement lines:** Use `:` for related fast statements (`t=0 : led1=1`, `num=0`).
* **Noise Filter:** Always use `tpsav = (3*tpsav + tps)/4` for analog pedal/dyno signals to eliminate servo flutter.
* **Non-blocking Serial:** Always implement the `if j=0 then Hserin 10,BAU,[s]` pattern with `BAU:`.
* **Zero Malay in Comments:** Code comments and serial strings must remain strictly English.

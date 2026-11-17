# 🚗 Focus Applied Technologies - Drive-By-Wire (DBW) Controller & Test Bench System

> **Document Version:** 2.0  
> **Target Platform:** Toyota Hilux / Kijang Innova (1KD-FTV & 2KD-FTV D-4D Common Rail Diesel)  
> **Microcontroller:** Microchip PIC18F26K22 / PIC18F46K22 (16 MHz)  
> **Hardware-In-The-Loop (HIL) DAQ:** Advantech USB-4716 Multifunction USB Module  
> **Author / Maintainer:** Horizon / Focus Applied Technologies Sdn. Bhd. (Mukmin & Team)  
> **Repository Path:** `d:\Users\ANG\Desktop\Mukmin\DBW`

---

## 📑 Table of Contents
1. [Executive Summary & Purpose](#1-executive-summary--purpose)
2. [System Architecture & Working Principle](#2-system-architecture--working-principle)
3. [Microcontroller Hardware & Pinout](#3-microcontroller-hardware--pinout)
4. [Firmware Analysis (`DBW.pbp`)](#4-firmware-analysis-dbwpbp)
   - [Analog Conversion & Dual TPS Generation](#analog-conversion--dual-tps-generation)
   - [Switch Logic: Idle & WOT](#switch-logic-idle--wot)
   - [EEPROM Calibration Memory Map](#eeprom-calibration-memory-map)
   - [Serial Telemetry & Interactive CLI Command Protocol](#serial-telemetry--interactive-cli-command-protocol)
5. [Automotive ECU Correlation: Toyota Hilux / Innova (2KD-FTV)](#5-automotive-ecu-correlation-toyota-hilux--innova-2kd-ftv)
   - [Factory Sensor Specifications (VPA1 & VPA2)](#factory-sensor-specifications-vpa1--vpa2)
   - [Fail-Safe & Correlation DTCs (P2138 Avoidance)](#fail-safe--correlation-dtcs-p2138-avoidance)
6. [Hardware-In-The-Loop (HIL) Test Bench Web Application](#6-hardware-in-the-loop-hil-test-bench-web-application)
   - [Architecture & Tech Stack](#architecture--tech-stack)
   - [Advantech DAQ Interface (USB-4716)](#advantech-daq-interface-usb-4716)
   - [Web Dashboard Features](#web-dashboard-features)
   - [Quick Start: Running the Test Bench](#quick-start-running-the-test-bench)
7. [Integration with Fuel Stretcher V2.0 & Dyno Systems](#7-integration-with-fuel-stretcher-v20--dyno-systems)
8. [Cross-Project Knowledge & Historical Context](#8-cross-project-knowledge--historical-context)
9. [Calibration & Bench Testing Workflow](#9-calibration--bench-testing-workflow)
10. [Troubleshooting & Diagnostics Guide](#10-troubleshooting--diagnostics-guide)

---

## 1. Executive Summary & Purpose

Modern common rail diesel vehicles—specifically the **Toyota Hilux, Fortuner, and Kijang Innova (1KD-FTV 3.0L & 2KD-FTV 2.5L)**—employ an electronic throttle pedal system (**Drive-By-Wire / DBW**). The accelerator pedal does not use a traditional mechanical cable; instead, it houses dual potentiometers / Hall-effect sensors (**VPA1** and **VPA2**) that output two precisely correlated DC analog voltages to the Denso Engine Control Unit (ECU).

When retrofitting an engine onto an **engine dynamometer**, or when interfacing with external dynamometer throttle actuators and automated throttle control systems (such as the **Focus Applied Technologies Dyno Controller** and **Fuel Stretcher V2.0**), an analog bridging controller is required to:
1. Receive a single-ended $0.0\text{V} - 5.0\text{V}$ throttle request signal from the dyno system or manual pot.
2. Generate **dual, safety-critical, independently calibrated throttle signals** (TPS1/VPA1 and TPS2/VPA2) that strictly satisfy the Toyota ECU's correlation curves.
3. Provide discrete digital switching signals for **Idle status** and **Wide-Open Throttle (WOT)** status (including their inverted logic counterparts) for auxiliary controllers, dyno safeties, and fuel modification modules.
4. Provide non-volatile EEPROM storage and an in-circuit serial calibration interface so technicians can calibrate voltage floors and ceilings on the fly without recompiling firmware.

The project in this repository comprises the **PIC microcontroller firmware (`DBW.pbp`)**, vehicle service manual correlation data (`MANUALS/`), and a **Hardware-In-The-Loop (HIL) automated test bench Web Application (`WebApp/`)** driven by an **Advantech USB-4716 DAQ**.

---

## 2. System Architecture & Working Principle

```
+-----------------------------------------------------------------------------------------+
|                                    DYNO TEST CELL                                       |
|                                                                                         |
|  +------------------------+      0-5V DC Analog       +------------------------------+  |
|  | Dyno Throttle Actuator | ------------------------> | Focus Applied Technologies   |  |
|  | / Advantech AO Ch0     |      (Pin AN24)           | DBW Controller (PIC18F26K22) |  |
|  +------------------------+                           +------------------------------+  |
|                                                                 |         |             |
|                                    PWM1 (RC2) + RC Lowpass      |         |             |
|                                 +-------------------------------+         |             |
|                                 |                                         |             |
|                                 |  PWM2 (RC1/RD1) + RC Lowpass            |             |
|                                 |  +--------------------------------------+             |
|                                 |  |                                                    |
|                                 v  v                                                    |
|                  +-------------------------------+                                      |
|                  |     Toyota Denso Diesel ECU   | <--- Discrete Digital Switches       |
|                  |      (Hilux 2KD-FTV D-4D)     |      (Idle, WOT, Inverted)           |
|                  |                               |                                      |
|                  | - Pin E5-22: VPA1 (0.8 - 3.4V)|                                      |
|                  | - Pin E5-23: VPA2 (1.6 - 4.6V)|                                      |
|                  +-------------------------------+                                      |
+-----------------------------------------------------------------------------------------+
                                 ^
                                 |  Simulate & Validate (HIL Bench)
+-----------------------------------------------------------------------------------------+
|                               HIL VALIDATION WEB BENCH                                  |
|                                                                                         |
|  +----------------------------+   USB   +----------------------+   HTTP/JSON   +-----+  |
|  | Advantech USB-4716 DAQ     | <=====> | Python Flask Server  | <===========> | Web |  |
|  | - AO0: Throttle Command    |         | (Automation.BDaqApi) |  Port 5000    | GUI |  |
|  | - AI0: TPS1 Readback       |         +----------------------+               +-----+  |
|  | - AI1: TPS2 Readback       |                                                         |
|  +----------------------------+                                                         |
+-----------------------------------------------------------------------------------------+
```

---

## 3. Microcontroller Hardware & Pinout

The controller is based on the **Microchip PIC18F26K22** (and compatible with 40/44-pin **PIC18F46K22**), running at **16 MHz** internal HF oscillator.

### Hardware Pin Mapping Table

| Pin Name | Port / Bit | Function | Circuit / Description |
| :--- | :--- | :--- | :--- |
| **AN24** | Analog Input (CHS 24) | **Throttle In (0–5V)** | Single-ended throttle command from dyno or pedal potentiometer. |
| **CCP1** | `PORTC.2` | **PWM Out 1 (TPS1 / VPA1)** | Hardware PWM (1 kHz or 20 kHz), filtered via external RC low-pass filter to generate smooth DC voltage $0.80\text{V} - 3.39\text{V}$. |
| **CCP2 / CCP4** | `PORTC.1` or `PORTD.1` | **PWM Out 2 (TPS2 / VPA2)** | Hardware PWM, filtered via external RC low-pass filter to generate smooth DC voltage $1.61\text{V} - 4.61\text{V}$. |
| **Si** | `PORTB.0` | **Idle Switch Output** | High (+5V) when throttle is above idle threshold ($Vi$), Low (0V) at idle. (Labeled `Inj sens 1`). |
| **Sw** | `PORTB.1` | **WOT Switch Output** | High (+5V) when throttle is at/above Wide Open Throttle ($Vw$), Low (0V) below WOT. (Labeled `Inj sens 2`). |
| **Sii** | `PORTB.2` | **Inverted Idle Switch** | Logical inverse of `Si` (`1 - SIO`). (Labeled `Inj sens 3`). |
| **Swi** | `PORTB.5` | **Inverted WOT Switch** | Logical inverse of `Sw` (`1 - SWO`). (Labeled `Inj sens 4`). |
| **LED1** | `PORTD.2` | **Heartbeat / TPS Status LED** | Flashing LED with period dynamically proportional to throttle position ($t > TPS$). |
| **TX1** | `PORTC.6` | **Serial TX (UART)** | Hardware UART transmitting telemetry and menu prompts at 9600 baud, 8-N-1. |
| **RX1** | `PORTC.7` | **Serial RX (UART)** | Hardware UART receiving serial calibration commands (`###L`, `###H`, `###K`, `###G`, `###I`, `###W`, `Z`, `Q`). |

---

## 4. Firmware Analysis (`DBW.pbp`)

The firmware is written in **PicBasic Pro (PBP 2.60C / 3.x)** and compiled with **MPASM**.

### Analog Conversion & Dual TPS Generation
The analog-to-digital converter reads the throttle input signal with 8-bit resolution ($0 - 255$ counts, corresponding to $0.00\text{V} - 5.00\text{V}$). A digital 4-point weighted moving average filter is applied to eliminate high-frequency noise and jitter from dyno cabling:

$$TPS_{av} = \frac{3 \times TPS_{av} + TPS_{in}}{4}$$

The firmware then executes linear interpolation to map the 8-bit input to two independently calibrated channels:

$$\text{TPS1 Output (TPSO)} = V_1 + \frac{(V_2 - V_1) \times tps}{255}$$

$$\text{TPS2 Output (TPSN)} = V_3 + \frac{(V_4 - V_3) \times tps}{255}$$

*Note:* In the manual variation (`MANUALS/DBW.pbp`), the outputs can be complemented ($255 - \dots$) when driving inverted optocoupler driver circuits.

The computed bytes are written directly to hardware PWM channels:
- `hpwm 1, TPSO.byte0, 1000` (Timer2 PWM on CCP1)
- `hpwm 2, TPSn.byte0, 1000` (Timer2 PWM on CCP2)

### Switch Logic: Idle & WOT
The firmware monitors the throttle position against two programmable threshold voltages:
- $V_i$ (Idle Threshold, default `10` = $0.20\text{V}$)
- $V_w$ (Wide Open Throttle Threshold, default `230` = $4.51\text{V}$)

```pbp
select case tps
    case is < Vi
        SIO = 0: SWO = 0
    case is < Vw
        SIO = 1: SWO = 0
    case else
        SIO = 1: SWO = 1
end select
si  = SIO:  sii = 1 - SIO
sw  = SWO:  swi = 1 - SWO
```

### EEPROM Calibration Memory Map
Calibration values are permanently stored in the PIC18F26K22's on-chip 1024-byte data EEPROM:

| Address Offset | Parameter | PBP Variable | Default Byte Value | Equivalent Voltage | Function |
| :---: | :---: | :---: | :---: | :---: | :--- |
| `0x00 - 0x01` | **V1** (MSB, LSB) | `V1` | `0, 41` (`$0029`) | **~0.80 V** | Minimum TPS1 (VPA1) output voltage at 0% throttle (Idle) |
| `0x02 - 0x03` | **V2** (MSB, LSB) | `V2` | `0, 173` (`$00AD`) | **~3.39 V** | Maximum TPS1 (VPA1) output voltage at 100% throttle (WOT) |
| `0x04 - 0x05` | **Vi** (MSB, LSB) | `Vi` | `0, 10` (`$000A`) | **~0.20 V** | Throttle input threshold for Idle Switch toggle |
| `0x06 - 0x07` | **Vw** (MSB, LSB) | `Vw` | `0, 230` (`$00E6`) | **~4.51 V** | Throttle input threshold for WOT Switch toggle |
| `0x08 - 0x09` | **cyc** (MSB, LSB) | `cyc` | `0, 0` | Counter | Power cycle counter (increments on every boot) |
| `0x0A - 0x0B` | **V3** (MSB, LSB) | `V3` | `0, 82` (`$0052`) | **~1.61 V** | Minimum TPS2 (VPA2) output voltage at 0% throttle (Idle) |
| `0x0C - 0x0D` | **V4** (MSB, LSB) | `V4` | `0, 235` (`$00EB`) | **~4.61 V** | Maximum TPS2 (VPA2) output voltage at 100% throttle (WOT) |

### Serial Telemetry & Interactive CLI Command Protocol
Serial port configuration: **9600 Baud, 8 Data Bits, No Parity, 1 Stop Bit (8-N-1)**.

1. **Continuous Telemetry Streaming:**
   Every 100 loops (~50–100ms), the controller outputs a comma-separated stream:
   ```
   <TPS_IN>,<TPS1_OUT>,<TPS2_OUT>,<IDLE_SW>,<WOT_SW>\r
   Example: 128, 107, 158, 1, 0
   ```
2. **Interactive Calibration Menu:**
   Sending any serial character during normal execution triggers the calibration interpreter:
   - Enter a **3-digit decimal number (000–255)** followed by the command letter:
     - `###L`: Set Low TPS1 output voltage ($V_1$)
     - `###H`: Set High TPS1 output voltage ($V_2$)
     - `###K`: Set Low TPS2 output voltage ($V_3$)
     - `###G`: Set High TPS2 output voltage ($V_4$)
     - `###I`: Set Idle Switch voltage threshold ($V_i$)
     - `###W`: Set WOT Switch voltage threshold ($V_w$)
   - Command `Z`: **Burn** current in-RAM calibration to internal EEPROM.
   - Command `Q`: **Quit** calibration menu and resume normal execution (BAU - Business As Usual).

---

## 5. Automotive ECU Correlation: Toyota Hilux / Innova (2KD-FTV)

### Factory Sensor Specifications (VPA1 & VPA2)
According to the official **Toyota 1KD-FTV / 2KD-FTV Engine Repair Manual (DR174E)**:

| Sensor Channel | ECU Connector Pin | Accelerator Released (Idle) | Accelerator Depressed (WOT) | Sensor Purpose |
| :--- | :--- | :---: | :---: | :--- |
| **VPA1** (Sensor 1) | **Pin E5-22** (`W-L`) | **0.5 V – 1.1 V** *(Nominal: 0.8 V)* | **2.6 V – 4.5 V** *(Nominal: 3.4 V)* | Primary engine throttle control signal |
| **VPA2** (Sensor 2) | **Pin E5-23** (`GR-G`) | **1.2 V – 2.0 V** *(Nominal: 1.6 V)* | **3.4 V – 5.0 V** *(Nominal: 4.6 V)* | Sensor malfunction detection & plausibility check |
| **VCPA** (Sensor 1 Vcc) | Pin E5-26 (`LG-R`) | 4.5 V – 5.5 V | 4.5 V – 5.5 V | Regulated +5V sensor supply from ECU |
| **VCPA2** (Sensor 2 Vcc)| Pin E5-27 (`BR-R`) | 4.5 V – 5.5 V | 4.5 V – 5.5 V | Regulated +5V sensor supply from ECU |
| **EPA** (Sensor 1 GND) | Pin E5-28 (`BR-W`) | 0.0 V (Sensor GND) | 0.0 V (Sensor GND) | Analog Ground for VPA1 |
| **EPA2** (Sensor 2 GND)| Pin E5-29 (`BR-Y`) | 0.0 V (Sensor GND) | 0.0 V (Sensor GND) | Analog Ground for VPA2 |

```
Voltage (V)
  5.0 |                                             .--- VPA2 (WOT: 4.6V)
  4.5 |                                        .---'
  4.0 |                                   .---'     .--- VPA1 (WOT: 3.4V)
  3.5 |                              .---'     .---'
  3.0 |                         .---'     .---'
  2.5 |                    .---'     .---'
  2.0 |               .---'     .---'
  1.5 |     .--------'     .---'  (VPA2 Idle: 1.6V)
  1.0 |               .---'
  0.5 |     .--------'            (VPA1 Idle: 0.8V)
  0.0 +--------------------------------------------------> Throttle Input (%)
      0% (Idle)                                  100% (WOT)
```

### Fail-Safe & Correlation DTCs (P2138 Avoidance)
The Denso ECU performs continuous cross-channel plausibility diagnostics. If the DBW controller's output voltages diverge from the expected slope or tolerance window:

| DTC Code | Detection Item | Cause | Consequence |
| :--- | :--- | :--- | :--- |
| **P0120 / P2120** | Pedal Position Sensor 1 Circuit Malfunction | Open or short in VPA1 line | Check Engine Light (MIL) ON, limited power |
| **P2122** | Sensor 1 Circuit Low Input | VPA1 voltage dropped $< 0.4\text{V}$ | ECU enters Limp-Home mode |
| **P2123** | Sensor 1 Circuit High Input | VPA1 voltage exceeded $> 4.8\text{V}$ | ECU enters Limp-Home mode |
| **P2125** | Pedal Position Sensor 2 Circuit Malfunction | Open or short in VPA2 line | Check Engine Light (MIL) ON |
| **P2127** | Sensor 2 Circuit Low Input | VPA2 voltage dropped $< 1.0\text{V}$ | ECU enters Limp-Home mode |
| **P2128** | Sensor 2 Circuit High Input | VPA2 voltage exceeded $> 4.9\text{V}$ | ECU enters Limp-Home mode |
| **P2138** | **Voltage Correlation Error (D / E)** | **VPA1 and VPA2 slopes or offset mismatch** | **Engine enters fail-safe limp mode: throttle pinned at idle (~1100 RPM limit), pedal response disabled** |

> [!IMPORTANT]
> The default EEPROM values ($V_1=41 \rightarrow 0.80\text{V}$, $V_2=173 \rightarrow 3.39\text{V}$, $V_3=82 \rightarrow 1.61\text{V}$, $V_4=235 \rightarrow 4.61\text{V}$) were calculated specifically to prevent DTC **P2138** on 1KD and 2KD engines. Any recalibration must maintain this precise proportional ratio across the full pedal sweep.

---

## 6. Hardware-In-The-Loop (HIL) Test Bench Web Application

The `WebApp/` folder contains a full-stack automated test bench system designed to simulate throttle pedal actuation, stimulate the DBW controller, and capture the real-time feedback curves using an industrial **Advantech USB-4716 DAQ**.

### Architecture & Tech Stack
- **Backend:** Python 3.10+ with Flask (`WebApp/app.py`).
- **Hardware Driver:** Advantech BDaq C-API Python Wrapper (`WebApp/Automation/BDaq/`).
- **Frontend:** Vanilla HTML5, CSS3 with modern dark UI (neon cyan/purple glassmorphism), Google Fonts (`Outfit`), and Chart.js.
- **Communication:** Non-blocking JSON REST API endpoints (`/api/set_throttle` and `/api/get_tps`).

### Advantech DAQ Interface (USB-4716)

```
+-----------------------------------------------------------------------------------------+
|                                ADVANTECH USB-4716 WIRING                                |
|                                                                                         |
|   Terminal Name       Function                    Connection to Test Bench / DBW        |
|   -------------       --------                    ------------------------------        |
|   AO 0                Analog Output Ch 0          --> DBW Controller Analog Input (AN24)|
|   AGND                Analog Ground Common        --> DBW Board GND (Shared Ground)     |
|   AI 0                Analog Input Ch 0           <-- DBW TPS1 / VPA1 Output Filter     |
|   AI 1                Analog Input Ch 1           <-- DBW TPS2 / VPA2 Output Filter     |
+-----------------------------------------------------------------------------------------+
```

#### Dynamic Hardware Detection & Reconnection
The backend implements dynamic DAQ error recovery (`init_daq()`). If the USB cable is unplugged or the module loses power, the server does not crash; it automatically attempts a non-blocking re-initialization and reflects the live status to the web interface.

### Web Dashboard Features
1. **Interactive Throttle Slider:** Allows technicians to smoothly sweep simulated throttle input from $0.00\text{V}$ to $5.00\text{V}$ (step $0.01\text{V}$) with a 20ms debounce filter.
2. **Dual TPS Digital Gauges:** Large, high-visibility digital readouts for TPS 1 and TPS 2 voltages.
3. **Real-Time Rolling Oscilloscope (Chart.js):** 30-sample rolling strip-chart with 100ms update rate, plotting TPS 1 (cyan) and TPS 2 (purple) trajectories simultaneously to visually verify tracking and linearity.
4. **DAQ Connectivity Badge:** Real-time badge indicating `DAQ Connected` (green/cyan) or `DAQ Disconnected` (red).

### Quick Start: Running the Test Bench
A Windows batch script is included for single-click operation:

```cmd
d:\Users\ANG\Desktop\Mukmin\DBW\RUN_WEBAPP.bat
```

This script:
1. Navigates to `d:\Users\ANG\Desktop\Mukmin\DBW\WebApp`.
2. Automatically launches Microsoft Edge at `http://127.0.0.1:5000`.
3. Starts the Flask server (`python app.py`) on port 5000.

---

## 7. Integration with Fuel Stretcher V2.0 & Dyno Systems

In engine test cell dynamometers operated by Focus Applied Technologies:
1. **The Fuel Stretcher V2.0** (`FUEL STRETCHER V2.0/`):
   - An interceptor board designed for common rail diesel engines.
   - Intercepts injector pulse signals from the ECU (`#1`, `#2`, `#3`, `#4`) to dynamically extend injection duration and fuel delivery during high-load dyno testing.
   - Requires real-time knowledge of throttle state (Idle, Part-Throttle, and WOT) to govern enrichment algorithms.
2. **DBW to Fuel Stretcher Handshake:**
   - The DBW controller's discrete switch outputs (`Si`, `Sw`, `Sii`, `Swi` on PORTB) interface directly with the Fuel Stretcher's injection sensor input pins (`Inj sens 1` through `Inj sens 4`).
   - This prevents over-fueling during engine deceleration or idle while enabling instant fuel extension upon detecting WOT.

---

## 8. Cross-Project Knowledge & Historical Context

Throughout the Focus Applied Technologies engineering portfolio (documented across company repositories and previous development cycles):

1. **FanCon (Variable Speed Dyno Fan Controller):**
   - Developed in `d:\Users\ANG\Desktop\VSFC` and `LOCAL COMPANY REPO`.
   - Built on the same **PIC18F26K22 (16MHz)** MCU and PicBasic Pro toolchain.
   - Employs identical EEPROM calibration architectures (`data`, `read`, `write`) and serial diagnostic routines.
2. **Balancing 2.0 (2-Plane Dynamic Balancing System):**
   - Utilizes Advantech DAQ cards (USB-4704 / USB-4716) for high-speed vibration and tachometer signal processing.
   - Shared design system: modern dark liquid-glass UI with neon accents, Outfit typography, and real-time Chart.js / canvas visualization.
3. **Repository Document Hub (`LOCAL COMPANY REPO`):**
   - Serves as the central intranet library for calibration procedures, schematics, and service manuals across test cells.

---

## 9. Calibration & Bench Testing Workflow

### Step-by-Step Calibration via Serial Terminal

1. **Hardware Connection:**
   - Connect a USB-to-TTL UART cable (3.3V/5V compatible) to the DBW controller board:
     - USB-TTL **GND** $\rightarrow$ Board **GND**
     - USB-TTL **RX** $\rightarrow$ Board **TX (RC6)**
     - USB-TTL **TX** $\rightarrow$ Board **RX (RC7)**
2. **Open Terminal:**
   - Set baud rate to **9600**, 8 data bits, no parity, 1 stop bit, no flow control.
3. **Read Current Stream:**
   - Verify that telemetry strings are streaming: `<tps>, <tpso>, <tpsn>, <sio>, <swo>`.
4. **Enter Calibration Mode:**
   - Press any key (e.g. `M` or Enter). The calibration menu will appear:
     ```text
     Commands: Enter 3 digit #(0-255) followed by letter (eg. 023L) 
     ###L Set Low  TPS1 output voltage
     ###H Set High TPS1 output voltage
     ###K Set Low  TPS2 output voltage
     ###G Set High TPS2 output voltage
     ###I Set Idle Switch voltage
     ###W Set WOT  Switch voltage
     Q=Quit      Z=Burn to EEPROM
     ```
5. **Adjust Parameters:**
   - To set TPS1 Low to 0.80V ($41$ counts): type `041L`.
   - To set TPS1 High to 3.39V ($173$ counts): type `173H`.
   - To set TPS2 Low to 1.61V ($82$ counts): type `082K`.
   - To set TPS2 High to 4.61V ($235$ counts): type `235G`.
6. **Save & Exit:**
   - Type `Z` to burn settings to EEPROM.
   - Type `Q` to resume normal operation.

---

## 10. Troubleshooting & Diagnostics Guide

| Symptom | Probable Cause | Diagnostic & Corrective Action |
| :--- | :--- | :--- |
| **Toyota ECU logs DTC P2138** | Voltage correlation between VPA1 and VPA2 out of bounds. | Check TPS1 and TPS2 curves on the WebApp test bench. Ensure VPA2 starts at ~1.6V when VPA1 is at ~0.8V, and both increase strictly monotonically. Re-calibrate using serial menu. |
| **ECU logs DTC P2122 / P2127** | TPS output voltage dropped below 0.4V (P2122) or 1.0V (P2127). | Verify $V_1 \ge 41$ (0.80V) and $V_3 \ge 82$ (1.61V). Ensure RC filter capacitors are not shorted to ground. |
| **WebApp shows "DAQ Disconnected"** | Advantech USB-4716 not detected or device descriptor mismatch. | 1. Check USB cable and ensure green power LED on DAQ is ON.<br>2. Verify device name in Advantech Device Manager is `USB-4716,BID#0`.<br>3. Run `python WebApp/test.py` to inspect raw error codes. |
| **Heartbeat LED (LED1) not blinking** | Controller halted or power supply missing. | Verify +5V regulated VDD supply to PIC18F26K22. Check MCLR pull-up resistor. Ensure oscillator is running at 16 MHz. |
| **Serial terminal shows gibberish** | Baud rate mismatch. | Ensure terminal is set strictly to **9600 baud, 8-N-1**. Verify `OSCCON` is set to 16 MHz (`%01110111`) in firmware. |
| **Output voltages jitter under dyno load** | High electrical noise from dyno ignition/inverters. | Ensure analog ground (AGND) and vehicle chassis ground are securely bonded at a single star point. Check ADC moving average filter coefficient (`tpsav`). |

---

*Focus Applied Technologies Sdn. Bhd. — Engineering Quality Control & Documentation System.*

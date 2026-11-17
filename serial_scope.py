"""
===================================================================
 Focus Applied Technologies - DBW Real-Time PWM Oscilloscope
 Target: COM4 @ 115200 Baud (PIC18F46K22 Fuel Stretcher V2.0)
 Author: Focus Applied Tech / Mukmin & Team (c) 2026
 Displays Real-Time 50Hz PWM Square Waveform + Analog Command
===================================================================
"""

import sys
import time
import threading
import numpy as np
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
import matplotlib.animation as animation

DEFAULT_PORT = "COM4"
BAUD_RATE = 115200

# Thread-safe variables
data_lock = threading.Lock()
current_tps_raw = 0.0
current_volts = 0.0
current_pulse_us = 1000.0
current_thr_pct = 0.0
connection_status = "CONNECTING..."
is_connected = False
is_running = True

def serial_worker(port_name, baud):
    global current_tps_raw, current_volts, current_pulse_us, current_thr_pct
    global connection_status, is_connected, is_running
    
    while is_running:
        try:
            ser = serial.Serial(port_name, baud, timeout=0.5)
            is_connected = True
            connection_status = f"CONNECTED: {port_name} @ {baud} bps"
            ser.reset_input_buffer()
            
            while is_running:
                raw_line = ser.readline()
                if not raw_line:
                    continue
                line = raw_line.decode('latin-1', errors='ignore').strip()
                if not line or line.startswith('#'):
                    continue
                
                parts = line.split(',')
                if len(parts) >= 2:
                    try:
                        raw_tps = float(parts[0])
                        raw_pulse = float(parts[1])
                        
                        volts = (raw_tps * 5.0) / 255.0
                        thr = (raw_tps * 100.0) / 255.0
                        
                        with data_lock:
                            current_tps_raw = raw_tps
                            current_volts = volts
                            current_pulse_us = raw_pulse
                            current_thr_pct = thr
                    except ValueError:
                        pass
            ser.close()
        except serial.SerialException as e:
            is_connected = False
            err_str = str(e).lower()
            if "access is denied" in err_str or "permission" in err_str:
                connection_status = "PORT BUSY (CLOSE PUTTY!)"
            else:
                connection_status = f"CONNECTING TO {port_name}..."
            time.sleep(0.8)
        except Exception:
            is_connected = False
            time.sleep(0.8)

def generate_pwm_waveform(pulse_width_ms, period_ms=20.0, num_cycles=3):
    """
    Generates time-domain step waveform points for oscilloscope display.
    """
    t_points = []
    v_points = []
    
    for cycle in range(num_cycles):
        t_start = cycle * period_ms
        t_fall = t_start + pulse_width_ms
        t_end = (cycle + 1) * period_ms
        
        # Rising edge to 5.0V
        t_points.extend([t_start, t_start])
        v_points.extend([0.0, 5.0])
        
        # High plateau
        t_points.append(t_fall)
        v_points.append(5.0)
        
        # Falling edge to 0.0V
        t_points.extend([t_fall, t_fall])
        v_points.extend([5.0, 0.0])
        
        # Low plateau
        t_points.append(t_end)
        v_points.append(0.0)
        
    return np.array(t_points), np.array(v_points)

def main():
    port = DEFAULT_PORT
    if len(sys.argv) > 1:
        port = sys.argv[1]

    th = threading.Thread(target=serial_worker, args=(port, BAUD_RATE), daemon=True)
    th.start()

    plt.style.use('dark_background')
    fig, (ax_pwm, ax_tps) = plt.subplots(2, 1, figsize=(11, 7), gridspec_kw={'height_ratios': [2, 1]})
    fig.canvas.manager.set_window_title('Focus Applied Tech - Real-Time 50Hz PWM Oscilloscope')

    # Top Oscilloscope Screen: Actual 50Hz Square Wave Pulses
    line_pwm, = ax_pwm.plot([], [], color='#00FFAA', lw=2.5, label='PWM Output Signal (Inj01 / PORTD.1)')
    ax_pwm.set_xlim(0, 60.0)  # Show 3 complete 20ms cycles (0ms to 60ms)
    ax_pwm.set_ylim(-0.5, 6.0)
    ax_pwm.set_ylabel('Voltage (V)', color='#00FFAA', fontsize=12, fontweight='bold')
    ax_pwm.grid(True, linestyle=':', alpha=0.45, color='#00FFAA')
    ax_pwm.legend(loc='upper right', framealpha=0.7)
    ax_pwm.set_title('OSCILLOSCOPE VIEW: 50Hz RC PWM Square Waveform (Triggered @ Cycle Start)', 
                     fontsize=11, color='#00FFAA', fontweight='bold', pad=10)

    # Annotations on Scope
    t_meas_text = ax_pwm.text(2.0, 5.3, '', color='#FFFF00', fontsize=11, fontweight='bold',
                              bbox=dict(boxstyle='round,pad=0.3', facecolor='#222222', edgecolor='#FFFF00', alpha=0.8))

    # Bottom Screen: Analog Throttle Input Level Bar
    bar_tps = ax_tps.barh(['Throttle Command'], [0], color='#FF9900', height=0.5)
    ax_tps.set_xlim(0, 5.0)
    ax_tps.set_xlabel('Potentiometer Voltage (0.0V - 5.0V)', fontsize=11, fontweight='bold')
    ax_tps.grid(True, linestyle='--', alpha=0.35, color='#888888')

    # Status Header
    status_header = fig.text(0.50, 0.96, '', fontsize=12, color='#00FFAA', fontweight='bold', ha='center')

    def update_frame(frame):
        with data_lock:
            p_us = current_pulse_us
            v_in = current_volts
            thr = current_thr_pct
            status = connection_status
            conn = is_connected

        # Generate the live square wave for current pulse width
        p_ms = max(0.5, min(2.5, p_us / 1000.0))
        t_wave, v_wave = generate_pwm_waveform(p_ms, period_ms=20.0, num_cycles=3)
        line_pwm.set_data(t_wave, v_wave)

        # Update Throttle Bar
        bar_tps[0].set_width(v_in)

        # Update Scope Measurements
        duty = (p_ms / 20.0) * 100.0
        t_meas_text.set_text(f"Ton (High): {p_ms:.2f}ms ({int(p_us)}us) | Period: 20.0ms (50.0Hz) | Duty: {duty:.1f}%")

        # Update Top Header
        if conn:
            status_header.set_color('#00FFAA')
            status_header.set_text(f"POT: {v_in:.2f}V ({thr:.1f}%)  ==>  SERVO PWM: {int(p_us)}us (50Hz)  |  {status}")
        else:
            status_header.set_color('#FF3333')
            status_header.set_text(f"{status}")

        return line_pwm, bar_tps, t_meas_text, status_header

    ani = animation.FuncAnimation(fig, update_frame, interval=30, blit=False)
    plt.tight_layout()
    plt.subplots_adjust(top=0.91, hspace=0.35)
    plt.show()

if __name__ == '__main__':
    main()

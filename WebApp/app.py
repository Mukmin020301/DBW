import time
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

DAQ_MODULE_LOADED = False
try:
    from Automation.BDaq.InstantAoCtrl import InstantAoCtrl
    from Automation.BDaq.InstantAiCtrl import InstantAiCtrl
    from Automation.BDaq.BDaqApi import ErrorCode
    DAQ_MODULE_LOADED = True
except Exception as e:
    print(f"DAQ library load failed: {e}")

device_desc = "USB-4716,BID#0"
current_throttle_v = 0.0

ao_ctrl = None
ai_ctrl = None

def init_daq():
    global ao_ctrl, ai_ctrl
    if not DAQ_MODULE_LOADED: return False
    try:
        if ao_ctrl is None:
            ao_ctrl = InstantAoCtrl(device_desc)
        if ai_ctrl is None:
            ai_ctrl = InstantAiCtrl(device_desc)
        
        # Test connection by reading channel 0
        err, _ = ai_ctrl.readDataF64(0, 1)
        if err == ErrorCode.Success:
            return True
        else:
            if ao_ctrl:
                try: ao_ctrl.dispose()
                except: pass
            if ai_ctrl:
                try: ai_ctrl.dispose()
                except: pass
            ao_ctrl = None
            ai_ctrl = None
            return False
    except:
        if ao_ctrl:
            try: ao_ctrl.dispose()
            except: pass
        if ai_ctrl:
            try: ai_ctrl.dispose()
            except: pass
        ao_ctrl = None
        ai_ctrl = None
        return False

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/set_throttle', methods=['POST'])
def set_throttle():
    global current_throttle_v
    data = request.json
    voltage = float(data.get('voltage', 0))
    current_throttle_v = voltage
    
    if init_daq():
        try:
            ao_ctrl.writeAny(0, 1, None, [voltage])
        except Exception:
            pass
            
    return jsonify({"status": "success", "voltage": voltage})

@app.route('/api/get_tps', methods=['GET'])
def get_tps():
    global ao_ctrl, ai_ctrl
    tps1_val = 0.0
    tps2_val = 0.0
    hardware_connected = init_daq()
    
    if hardware_connected:
        try:
            err, data = ai_ctrl.readDataF64(0, 2)
            if err == ErrorCode.Success:
                tps1_val = data[0] if data else 0.0
                tps2_val = data[1] if data and len(data) > 1 else 0.0
            else:
                hardware_connected = False
                if ao_ctrl:
                    try: ao_ctrl.dispose()
                    except: pass
                if ai_ctrl:
                    try: ai_ctrl.dispose()
                    except: pass
                ao_ctrl = None
                ai_ctrl = None
        except Exception:
            hardware_connected = False
            if ao_ctrl:
                try: ao_ctrl.dispose()
                except: pass
            if ai_ctrl:
                try: ai_ctrl.dispose()
                except: pass
            ao_ctrl = None
            ai_ctrl = None
            
    return jsonify({
        "tps1": round(tps1_val, 3), 
        "tps2": round(tps2_val, 3),
        "daq_connected": hardware_connected
    })

if __name__ == '__main__':
    print("Starting Hilux DBW Test Server (DYNAMIC HARDWARE CHECK MODE)...")
    app.run(debug=True, port=5000, use_reloader=False)

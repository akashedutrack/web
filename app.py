"""
app.py
Central server for the two ESP32 temperature nodes.

- Boards POST readings to /api/report
- Dashboard (templates/index.html) polls /api/status
- This server decides "bothHigh" once it has fresh data from both boards

Run:
    pip install flask
    python app.py
Then open http://localhost:5000
"""

import time
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

# How long a reading stays "fresh" before we treat that board as offline.
STALE_AFTER_SECONDS = 15

# Kept here for reference / future server-side logic; boards currently decide
# "isHigh" themselves and just report the boolean.
TEMP_THRESHOLD_C = 30.0

# In-memory store keyed by device id. Fine for 2 boards / a hobby project.
devices = {}


def prune_stale():
    now = time.time()
    for dev in devices.values():
        if now - dev["last_seen"] > STALE_AFTER_SECONDS:
            dev["online"] = False


def compute_both_high():
    if len(devices) < 2:
        return False
    return all(d["online"] and d["is_high"] for d in devices.values())


@app.route("/")
def dashboard():
    return render_template("index.html")


@app.route("/api/report", methods=["POST"])
def report():
    data = request.get_json(force=True, silent=True) or {}

    device_id = data.get("deviceId")
    temperature = data.get("temperature")
    humidity = data.get("humidity")
    is_high = bool(data.get("isHigh"))

    if device_id is None or temperature is None or humidity is None:
        return jsonify({"error": "deviceId, temperature, humidity are required"}), 400

    devices[str(device_id)] = {
        "deviceId": device_id,
        "temperature": temperature,
        "humidity": humidity,
        "is_high": is_high,
        "online": True,
        "last_seen": time.time(),
    }

    prune_stale()
    both_high = compute_both_high()

    print(f"[report] device {device_id}: {temperature}C, {humidity}% "
          f"isHigh={is_high} -> bothHigh={both_high}")

    return jsonify({"ok": True, "bothHigh": both_high})


@app.route("/api/status")
def status():
    prune_stale()
    return jsonify({
        "devices": list(devices.values()),
        "bothHigh": compute_both_high(),
        "threshold": TEMP_THRESHOLD_C,
        "serverTime": time.time(),
    })


if __name__ == "__main__":
    # host="0.0.0.0" so ESP32 boards on the same WiFi network can reach it too
    # use_reloader=False avoids a Windows quirk where the debug reloader watches
    # unrelated site-packages files and keeps restarting the server.
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
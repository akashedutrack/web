"""
simulate_boards.py
Sends fake readings from "board 1" and "board 2" to the Flask server every few
seconds, so you can see the dashboard working before the real ESP32 boards
are wired up.

Run this in a second terminal while app.py is running:
    python simulate_boards.py
"""

import time
import random
import requests

SERVER_URL = "http://localhost:5000/api/report"
THRESHOLD_C = 30.0


def fake_reading():
    temp = round(random.uniform(24.0, 34.0), 1)
    hum = round(random.uniform(40.0, 70.0), 1)
    return temp, hum


def send(device_id):
    temp, hum = fake_reading()
    payload = {
        "deviceId": device_id,
        "temperature": temp,
        "humidity": hum,
        "isHigh": temp > THRESHOLD_C,
    }
    try:
        res = requests.post(SERVER_URL, json=payload, timeout=3)
        print(f"Board {device_id}: sent {payload} -> {res.json()}")
    except requests.RequestException as e:
        print(f"Board {device_id}: failed to send ({e})")


if __name__ == "__main__":
    print("Simulating boards 1 and 2. Press Ctrl+C to stop.")
    while True:
        send(1)
        send(2)
        time.sleep(3)
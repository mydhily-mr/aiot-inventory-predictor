"""
simulate_gateway.py

Stands in for your MAX32630FTHR + ESP-01 gateway while hardware is in transit.
Pushes realistic, slowly-depleting bin readings to Firebase on a schedule,
using the exact same data shape your dashboard already expects.

This is not throwaway code: the HTTP calls it makes are effectively what your
ESP-01 firmware will do later (a PATCH/PUT to the same Firebase REST endpoint).
Once your board arrives, you're replacing "generate a fake weight" with
"read the real HX711," not rebuilding the pipeline.

Setup:
    pip install requests --break-system-packages

Fill in FIREBASE_DB_URL below with your project's databaseURL
(Firebase console -> Project Settings -> General -> your web app config),
e.g. "https://smd-store-inventory-default-rtdb.firebaseio.com"
"""

import time
import random
import requests
from datetime import datetime

# ================= CONFIG =================
FIREBASE_DB_URL = "https://aiot-inventory-predictor-default-rtdb.asia-southeast1.firebasedatabase.app/"
UPDATE_INTERVAL_SECONDS = 30       # how often each bin "reports in"
NOISE = 0.15                       # +/- 15% jitter on each reading, like a real sensor
# ============================================

# Same starting point as the dashboard's demo data, so the two line up visually.
BINS = {
    "BIN-R10K-08":   {"name": "10kΩ Resistor · 0805",        "unit": "pcs", "weight_g": 340, "qty": 8400, "rate_per_day": 300},
    "BIN-C100N-06":  {"name": "100nF Ceramic Cap · 0603",     "unit": "pcs", "weight_g": 28,  "qty": 1200, "rate_per_day": 260},
    "BIN-CONUSBC16": {"name": "USB-C Connector · 16-pin",     "unit": "pcs", "weight_g": 612, "qty": 340,  "rate_per_day": 40},
    "BIN-IC-M328P":  {"name": "ATmega328P · TQFP",            "unit": "pcs", "weight_g": 810, "qty": 900,  "rate_per_day": 15},
    "BIN-LED-R06":   {"name": "Red LED · 0603",                "unit": "pcs", "weight_g": 31,  "qty": 5200, "rate_per_day": 500},
}


def push_reading(bin_id: str, data: dict) -> bool:
    """PATCH the bin's current state, and add one entry to its history log."""
    base = f"{FIREBASE_DB_URL}/bins/{bin_id}"
    now = int(time.time())

    try:
        # Update the "current state" fields the dashboard reads on load
        r1 = requests.patch(f"{base}.json", json={
            "name": data["name"],
            "unit": data["unit"],
            "weight_g": round(data["weight_g"], 1),
            "qty": int(data["qty"]),
            "rate_per_day": data["rate_per_day"],
            "updated_at": now,
        }, timeout=10)
        r1.raise_for_status()

        # Append to history (Firebase auto-generates a time-ordered key with POST)
        r2 = requests.post(f"{base}/history.json", json={
            "ts": now,
            "weight_g": round(data["weight_g"], 1),
        }, timeout=10)
        r2.raise_for_status()
        return True

    except requests.exceptions.RequestException as e:
        print(f"  [!] Failed to push {bin_id}: {e}")
        return False


def step_bin(data: dict):
    """Simulate one reporting interval's worth of consumption for a bin."""
    per_unit_weight = data["weight_g"] / data["qty"] if data["qty"] > 0 else 0
    seconds_per_day = 86400
    expected_loss_per_interval = per_unit_weight * data["rate_per_day"] * (UPDATE_INTERVAL_SECONDS / seconds_per_day)

    # add sensor-like jitter so the chart doesn't look like a perfectly straight line
    jitter = 1 + random.uniform(-NOISE, NOISE)
    actual_loss = expected_loss_per_interval * jitter

    data["weight_g"] = max(data["weight_g"] - actual_loss, 0)
    data["qty"] = max(int(data["weight_g"] / per_unit_weight), 0) if per_unit_weight > 0 else data["qty"]


def main():
    if "YOUR-PROJECT" in FIREBASE_DB_URL:
        print("Set FIREBASE_DB_URL at the top of this file before running.")
        return

    print(f"Simulated gateway starting — reporting every {UPDATE_INTERVAL_SECONDS}s. Ctrl+C to stop.\n")
    try:
        while True:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] Pushing readings...")
            for bin_id, data in BINS.items():
                step_bin(data)
                ok = push_reading(bin_id, data)
                status = "ok" if ok else "FAILED"
                print(f"  {bin_id:<16} {data['qty']:>6} {data['unit']:<4} "
                      f"({data['weight_g']:.1f}g)  [{status}]")
            time.sleep(UPDATE_INTERVAL_SECONDS)
    except KeyboardInterrupt:
        print("\nStopped.")


if __name__ == "__main__":
    main()

"""
train_forecast.py

Pulls each bin's logged weight history from Firebase, fits a simple linear
regression to the depletion trend, and writes back a data-driven prediction.

This is intentionally NOT deep learning — see the project README for why a
regression model is the right tool for a single-variable time series like
this. The point isn't model complexity, it's that the prediction is learned
from real observed data instead of a hardcoded assumption.

Run this periodically (once a day is plenty) to refresh predictions as more
history accumulates. It's safe to run early with little data — it'll just
tell you it needs more.

Setup:
    pip install requests pandas scikit-learn --break-system-packages
"""

import time
import os
import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression

# ================= CONFIG =================
FIREBASE_DB_URL = "https://aiot-inventory-predictor-default-rtdb.asia-southeast1.firebasedatabase.app/"
MIN_POINTS_TO_TRAIN = 10   # don't trust a regression fit on fewer points than this
MIN_SPAN_DAYS = 0.5   # history must cover at least 12 hours before the model is trusted

# Per-bin defaults if a bin doesn't specify its own in Firebase.
# lead_time: how many days it actually takes to get a reorder delivered.
# buffer: extra safety margin on top of lead time before you'd want the alert.
DEFAULT_REORDER_LEAD_DAYS = 2
DEFAULT_REORDER_BUFFER_DAYS = 1

# How long to wait before re-sending an alert for the same bin, so it doesn't
# email/message you again every single time this script runs while still critical.
#ALERT_COOLDOWN_HOURS = 1 / 60   # 1 minute for demo purpose
ALERT_COOLDOWN_HOURS = 1.5 / 60   # 1.5 minutes

# Leave EMAIL_ENABLED as False until you've set up an app password — the
# script runs fine without it, it just won't send anything.
EMAIL_ENABLED = True
EMAIL_FROM = "arshikrishna3737@gmail.com"
EMAIL_APP_PASSWORD = os.environ.get("ALERT_EMAIL_APP_PASSWORD", "")   # not your normal password — see note below
EMAIL_TO = "137mydhily@gmail.com"

# WhatsApp via CallMeBot (free, personal-use). Get your API key by messaging
# the bot first — see the setup steps in the project README.
WHATSAPP_ENABLED = False
WHATSAPP_PHONE = "916XXXXXXXXXX"       # your number, country code, no + or spaces
WHATSAPP_APIKEY = "PASTE_CALLMEBOT_APIKEY_HERE"
# ============================================



def fetch_bin_ids() -> list:
    r = requests.get(f"{FIREBASE_DB_URL}/bins.json?shallow=true", timeout=10)
    r.raise_for_status()
    data = r.json()
    return list(data.keys()) if data else []


def fetch_history(bin_id: str) -> pd.DataFrame:
    r = requests.get(f"{FIREBASE_DB_URL}/bins/{bin_id}/history.json", timeout=10)
    r.raise_for_status()
    raw = r.json()
    if not raw:
        return pd.DataFrame(columns=["ts", "weight_g"])
    rows = list(raw.values())  # Firebase auto-keys discarded, order preserved by ts
    df = pd.DataFrame(rows).sort_values("ts").reset_index(drop=True)
    return df


def train_and_predict(df: pd.DataFrame, net_weight_g=None) -> dict | None:
    if len(df) < MIN_POINTS_TO_TRAIN:
        return None

    # Train only on the stretch since the last refill (weight jumping UP by >5 g),
    # so an old refill doesn't flatten the slope.
    w = df["weight_g"].values
    jumps = [i for i in range(1, len(w)) if w[i] - w[i - 1] > 5]
    recent = df.iloc[jumps[-1]:] if jumps else df
    if len(recent) < MIN_POINTS_TO_TRAIN:
        recent = df.tail(MIN_POINTS_TO_TRAIN)
    
    span_days = (recent["ts"].iloc[-1] - recent["ts"].iloc[0]) / 86400
    if span_days < MIN_SPAN_DAYS:
        return None   # too short a window to extrapolate to days

    X = recent[["ts"]].values
    y = recent["weight_g"].values

    model = LinearRegression()
    model.fit(X, y)
    r_squared = model.score(X, y)

    slope_per_sec = model.coef_[0]          # grams per second (negative = depleting)
    # The slope is learned from history; the starting point is the LIVE net stock weight
    # (the same value the GUI shows), not the container-inclusive weight_g.
    current_weight = net_weight_g if net_weight_g is not None else y[-1]

    if slope_per_sec >= 0:
        return {
            "rate_g_per_day": 0,
            "predicted_days_to_empty": None,
            "r_squared": round(r_squared, 3),
            "trained_on_points": len(recent),
        }

    rate_g_per_day = abs(slope_per_sec) * 86400
    days_to_empty = round(current_weight / rate_g_per_day, 1)

    return {
        "rate_g_per_day": round(rate_g_per_day, 2),
        "predicted_days_to_empty": days_to_empty,
        "r_squared": round(r_squared, 3),
        "trained_on_points": len(recent),
    }


def push_prediction(bin_id: str, prediction: dict):
    payload = {**prediction, "trained_at": int(time.time())}
    r = requests.patch(f"{FIREBASE_DB_URL}/bins/{bin_id}/model_prediction.json",
                        json=payload, timeout=10)
    r.raise_for_status()


def fetch_bin_config(bin_id: str) -> dict:
    """Reads name + any bin-specific reorder settings. Falls back to defaults
    if the bin hasn't set its own lead_time / buffer / last_alert_sent yet."""
    r = requests.get(f"{FIREBASE_DB_URL}/bins/{bin_id}.json", timeout=10)
    r.raise_for_status()
    data = r.json() or {}
    return {
        "name": data.get("name", bin_id),
        "reorder_lead_days": data.get("reorder_lead_days", DEFAULT_REORDER_LEAD_DAYS),
        "reorder_buffer_days": data.get("reorder_buffer_days", DEFAULT_REORDER_BUFFER_DAYS),
        "last_alert_sent": data.get("last_alert_sent"),  # unix timestamp or None
        "net_weight_g": data.get("totalWeightGrams"),   # real stock weight, same source as GUI qty
        "qty": data.get("qty"),
        "rate_per_day": data.get("rate_per_day"),
    }   

def dashboard_days_left(config: dict):
    """Same number the dashboard shows: qty / rate_per_day."""
    qty, rate = config.get("qty"), config.get("rate_per_day")
    if qty is None or not rate:
        return None
    return round(qty / rate, 1)

def should_alert(days_to_empty, config: dict) -> bool:
    if days_to_empty is None:
        return False

    threshold = config["reorder_lead_days"] + config["reorder_buffer_days"]
    if days_to_empty > threshold:
        return False

    last_sent = config["last_alert_sent"]
    if last_sent is not None:
        hours_since = (time.time() - last_sent) / 3600
        if hours_since < ALERT_COOLDOWN_HOURS:
            return False  # already alerted recently, don't spam

    return True


def send_reorder_email(bin_id: str, config: dict, prediction: dict):
    subject = f"Reorder needed: {config['name']} ({bin_id})"
    body = (
        f"{config['name']} is predicted to run out in "
        f"{prediction['predicted_days_to_empty']} day(s), based on a "
        f"burn rate of {prediction['rate_g_per_day']} g/day learned from "
        f"logged sensor data.\n\n"
        f"Reorder lead time for this component: {config['reorder_lead_days']} day(s)\n"
        f"Safety buffer: {config['reorder_buffer_days']} day(s)\n\n"
        f"Place a reorder now to avoid a stockout before the replacement arrives."
    )

    if not EMAIL_ENABLED:
        print(f"    [would email] {subject}  (EMAIL_ENABLED is False — set it "
              f"True once your app password is configured)")
        return False

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
            server.sendmail(EMAIL_FROM, [EMAIL_TO], msg.as_string())
        return True
    except smtplib.SMTPException as e:
        print(f"    [!] Email failed to send: {e}")
        return False


def send_whatsapp_alert(bin_id: str, config: dict, prediction: dict) -> bool:
    message = (
        f"Reorder needed: {config['name']} ({bin_id}). "
        f"Predicted to run out in {prediction['predicted_days_to_empty']} day(s) "
        f"at {prediction['rate_g_per_day']} g/day. "
        f"Lead time {config['reorder_lead_days']}d + buffer {config['reorder_buffer_days']}d."
    )

    if not WHATSAPP_ENABLED:
        print(f"    [would WhatsApp] {message}  (WHATSAPP_ENABLED is False)")
        return False

    url = (
        "https://api.callmebot.com/whatsapp.php"
        f"?phone={WHATSAPP_PHONE}&text={quote(message)}&apikey={WHATSAPP_APIKEY}"
    )
    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"    [!] WhatsApp send failed: {e}")
        return False


def mark_alert_sent(bin_id: str):
    requests.patch(f"{FIREBASE_DB_URL}/bins/{bin_id}.json",
                    json={"last_alert_sent": int(time.time())}, timeout=10)


def main():
    if "YOUR-PROJECT" in FIREBASE_DB_URL:
        print("Set FIREBASE_DB_URL at the top of this file before running.")
        return

    bin_ids = fetch_bin_ids()
    if not bin_ids:
        print("No bins found yet — is simulate_gateway.py (or real hardware) running?")
        return

    print(f"Found {len(bin_ids)} bin(s). Training...\n")
    for bin_id in bin_ids:
        df = fetch_history(bin_id)
        config = fetch_bin_config(bin_id)
        prediction = train_and_predict(df, config["net_weight_g"])

        if prediction is None:
            print(f"  {bin_id:<16} only {len(df)} point(s) logged — need "
                  f"{MIN_POINTS_TO_TRAIN} points over {MIN_SPAN_DAYS} day(s) to train the AI model; using live dashboard value for alerts.")
            prediction = {"rate_g_per_day": 0, "predicted_days_to_empty": None,
                          "r_squared": None, "trained_on_points": len(df)}
        else:
            push_prediction(bin_id, prediction)
        eta = prediction["predicted_days_to_empty"]
        eta_str = f"{eta}d" if eta is not None else "n/a (not depleting)"
        print(f"  {bin_id:<16} rate={prediction['rate_g_per_day']:>6.1f} g/day  "
              f"forecast={eta_str:<10} fit(R²)={prediction['r_squared']}  "
              f"(n={prediction['trained_on_points']})")

        #config = fetch_bin_config(bin_id)
        dash_days = dashboard_days_left(config)
        candidates = [d for d in (eta, dash_days) if d is not None]
        alert_days = min(candidates) if candidates else None   # alert on whichever is lower

        if should_alert(alert_days, config):
            print(f"    -> {alert_days}d left (AI model: {eta}, dashboard: {dash_days}) is below "
                  f"reorder threshold ({config['reorder_lead_days']}+{config['reorder_buffer_days']}d) — alerting")
            alert_info = {**prediction, "predicted_days_to_empty": alert_days}
            email_sent = send_reorder_email(bin_id, config, alert_info)
            whatsapp_sent = send_whatsapp_alert(bin_id, config, alert_info)
            if email_sent or whatsapp_sent:
                mark_alert_sent(bin_id)
                channels = ", ".join(c for c, ok in
                                      [("email", email_sent), ("WhatsApp", whatsapp_sent)] if ok)
                print(f"    -> alert sent via {channels}")

    print("\nPredictions written to /bins/{id}/model_prediction in Firebase.")


CHECK_INTERVAL_SECONDS = 120

if __name__ == "__main__":
    while True:
        try:
            main()
        except Exception as e:
            print(f"[!] Run failed: {e}")
        time.sleep(CHECK_INTERVAL_SECONDS)

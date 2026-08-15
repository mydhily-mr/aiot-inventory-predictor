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
import smtplib
from email.mime.text import MIMEText
from urllib.parse import quote
import requests
import pandas as pd
from sklearn.linear_model import LinearRegression

# ================= CONFIG =================
FIREBASE_DB_URL = "https://aiot-inventory-predictor-default-rtdb.asia-southeast1.firebasedatabase.app/"
MIN_POINTS_TO_TRAIN = 10   # don't trust a regression fit on fewer points than this

# Per-bin defaults if a bin doesn't specify its own in Firebase.
# lead_time: how many days it actually takes to get a reorder delivered.
# buffer: extra safety margin on top of lead time before you'd want the alert.
DEFAULT_REORDER_LEAD_DAYS = 3
DEFAULT_REORDER_BUFFER_DAYS = 2

# How long to wait before re-sending an alert for the same bin, so it doesn't
# email/message you again every single time this script runs while still critical.
ALERT_COOLDOWN_HOURS = 24

# Leave EMAIL_ENABLED as False until you've set up an app password — the
# script runs fine without it, it just won't send anything.
EMAIL_ENABLED = True
EMAIL_FROM = "youraddress@gmail.com"
EMAIL_APP_PASSWORD = "PASTE_GMAIL_APP_PASSWORD_HERE"   # not your normal password — see note below
EMAIL_TO = "storekeeper@example.com"

# WhatsApp via CallMeBot (free, personal-use). Get your API key by messaging
# the bot first — see the setup steps in the project README.
WHATSAPP_ENABLED = True
WHATSAPP_PHONE = "91XXXXXXXXXX"       # your number, country code, no + or spaces
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


def train_and_predict(df: pd.DataFrame) -> dict | None:
    if len(df) < MIN_POINTS_TO_TRAIN:
        return None

    X = df[["ts"]].values
    y = df["weight_g"].values

    model = LinearRegression()
    model.fit(X, y)
    r_squared = model.score(X, y)

    slope_per_sec = model.coef_[0]          # grams lost per second (negative = depleting)
    current_weight = y[-1]
    current_ts = X[-1][0]

    if slope_per_sec >= 0:
        # not depleting (or noisy/flat) — no meaningful forecast yet
        return {
            "rate_g_per_day": 0,
            "predicted_days_to_empty": None,
            "r_squared": round(r_squared, 3),
            "trained_on_points": len(df),
        }

    rate_g_per_day = abs(slope_per_sec) * 86400
    seconds_to_empty = current_weight / abs(slope_per_sec)
    days_to_empty = round(seconds_to_empty / 86400, 1)

    return {
        "rate_g_per_day": round(rate_g_per_day, 2),
        "predicted_days_to_empty": days_to_empty,
        "r_squared": round(r_squared, 3),
        "trained_on_points": len(df),
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
    }


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
        prediction = train_and_predict(df)

        if prediction is None:
            print(f"  {bin_id:<16} only {len(df)} point(s) logged — need "
                  f"{MIN_POINTS_TO_TRAIN} to train. Let the gateway run longer.")
            continue

        push_prediction(bin_id, prediction)
        eta = prediction["predicted_days_to_empty"]
        eta_str = f"{eta}d" if eta is not None else "n/a (not depleting)"
        print(f"  {bin_id:<16} rate={prediction['rate_g_per_day']:>6.1f} g/day  "
              f"forecast={eta_str:<10} fit(R²)={prediction['r_squared']}  "
              f"(n={prediction['trained_on_points']})")

        config = fetch_bin_config(bin_id)
        if should_alert(eta, config):
            print(f"    -> below reorder threshold "
                  f"({config['reorder_lead_days']}+{config['reorder_buffer_days']}d) — alerting")
            email_sent = send_reorder_email(bin_id, config, prediction)
            whatsapp_sent = send_whatsapp_alert(bin_id, config, prediction)
            if email_sent or whatsapp_sent:
                mark_alert_sent(bin_id)
                channels = ", ".join(c for c, ok in
                                      [("email", email_sent), ("WhatsApp", whatsapp_sent)] if ok)
                print(f"    -> alert sent via {channels}")

    print("\nPredictions written to /bins/{id}/model_prediction in Firebase.")


if __name__ == "__main__":
    main()

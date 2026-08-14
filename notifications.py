# notifications.py
# "Alert the hospital." Uses Twilio SMS if TWILIO_* env vars
# are set. Otherwise logs the alert (console + local file) so
# you can see exactly what WOULD have been sent, with zero
# telephony provider needed. Swap in Twilio, MSG91, Exotel,
# or plain email later — nothing else in the app changes,
# they'd all just implement send_hospital_alert().

import os
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

from core import build_hospital_message
import database

load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_SENDER_NUMBER = os.getenv("TWILIO_IVR_NUMBER")
HOSPITAL_PHONE_NUMBER = os.getenv("HOSPITAL_PHONE_NUMBER")

_twilio_client = None
_using_twilio = False

if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN and TWILIO_SENDER_NUMBER and HOSPITAL_PHONE_NUMBER:
    try:
        from twilio.rest import Client
        _twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
        _using_twilio = True
    except Exception as e:
        print(f"[notifications] Twilio configured but failed to init, "
              f"falling back to local log: {e}")


def send_hospital_alert(snake, patient_contact, channel):
    """
    Fires a hospital alert. Returns True/False. Never raises —
    a failed alert should never crash the caller-facing flow.
    """
    message = build_hospital_message(snake, patient_contact, channel)

    if _using_twilio:
        try:
            _twilio_client.messages.create(
                body=message,
                from_=TWILIO_SENDER_NUMBER,
                to=HOSPITAL_PHONE_NUMBER,
            )
            print(f"[notifications] SMS sent to hospital for {snake}")
            database.log_alert(snake, patient_contact, channel, message, sent_via_sms=True)
            return True
        except Exception as e:
            print(f"[notifications] Twilio send failed, logging instead: {e}")

    print(f"[notifications] (no SMS provider configured) "
          f"Hospital alert for {snake}:\n{message}\n")
    database.log_alert(snake, patient_contact, channel, message, sent_via_sms=False)
    return True


def get_alerts(limit=50):
    """Returns recent hospital alerts, newest first — for the demo UI."""
    return database.get_alerts(limit)


def notification_backend():
    return "twilio sms" if _using_twilio else "logged to database"

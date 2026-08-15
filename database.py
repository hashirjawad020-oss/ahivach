# database.py
# Logs every case. Uses Supabase if SUPABASE_URL/SUPABASE_KEY
# are set in the environment. Otherwise falls back to a local
# JSON file (data/cases.json) so the whole app runs with ZERO
# accounts set up. Swapping to Supabase later needs no code
# changes anywhere else — just set the two env vars.

import os
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

DATA_DIR = Path(__file__).parent / "data"
LOCAL_DB_FILE = DATA_DIR / "cases.json"
LOCAL_ALERTS_FILE = DATA_DIR / "hospital_alerts.json"

_supabase_client = None
_using_supabase = False

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        _supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
        _using_supabase = True
    except Exception as e:
        print(f"[database] Supabase configured but failed to connect, "
              f"falling back to local file: {e}")


def _ensure_local_files():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    if not LOCAL_DB_FILE.exists():
        LOCAL_DB_FILE.write_text("[]")
    if not LOCAL_ALERTS_FILE.exists():
        LOCAL_ALERTS_FILE.write_text("[]")

def _read_local(file_path=LOCAL_DB_FILE):
    _ensure_local_files()
    try:
        return json.loads(file_path.read_text())
    except json.JSONDecodeError:
        return []

def _write_local(data, file_path=LOCAL_DB_FILE):
    _ensure_local_files()
    file_path.write_text(json.dumps(data, indent=2))


def log_case(patient_contact, channel, snake_identified, answers):
    """
    Logs a case. channel = 'whatsapp' | 'ivr' | 'web'
    Returns True on success, False on failure (never raises —
    a logging failure should never break the user-facing flow).
    """
    record = {
        "id": str(uuid.uuid4()),
        "patient_contact": patient_contact,
        "channel": channel,
        "snake_identified": snake_identified,
        "answers": str(answers),
        "ambulance_status": "requested",
        "confirmed_species": None,
        "created_at": datetime.now(timezone.utc).isoformat(),
    }

    if _using_supabase:
        try:
            _supabase_client.table("cases").insert({
                "patient_contact": patient_contact,
                "channel": channel,
                "snake_identified": snake_identified,
                "answers": str(answers),
                "ambulance_status": "requested",
            }).execute()
            print(f"[database] Case logged to Supabase: "
                  f"{snake_identified} via {channel}")
            return True
        except Exception as e:
            print(f"[database] Supabase insert failed, "
                  f"writing to local file instead: {e}")

    try:
        cases = _read_local()
        cases.append(record)
        _write_local(cases)
        print(f"[database] Case logged locally: "
              f"{snake_identified} via {channel}")
        return True
    except Exception as e:
        print(f"[database] Local write failed: {e}")
        return False


def update_case_field(case_id, field, value):
    """
    Updates a single field on a case record. Works with both
    Supabase and local JSON backends. Used for ambulance status
    transitions and confirmed species feedback.
    Returns True on success, False on failure (never raises).
    """
    if _using_supabase:
        try:
            _supabase_client.table("cases").update(
                {field: value, "status_updated_at": datetime.now(timezone.utc).isoformat()}
            ).eq("id", case_id).execute()
            print(f"[database] Updated {field}={value} for case {case_id} (Supabase)")
            return True
        except Exception as e:
            print(f"[database] Supabase update failed, "
                  f"trying local file: {e}")

    try:
        cases = _read_local()
        for c in cases:
            if c.get("id") == case_id:
                c[field] = value
                c["status_updated_at"] = datetime.now(timezone.utc).isoformat()
                _write_local(cases)
                print(f"[database] Updated {field}={value} for case {case_id} (local)")
                return True
        print(f"[database] Case {case_id} not found in local file")
        return False
    except Exception as e:
        print(f"[database] Local update failed: {e}")
        return False


def get_cases(limit=50):
    """
    Returns the most recent cases, newest first.
    """
    if _using_supabase:
        try:
            res = (
                _supabase_client.table("cases")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data
        except Exception as e:
            print(f"[database] Supabase read failed, "
                  f"reading local file instead: {e}")

    cases = _read_local(LOCAL_DB_FILE)
    cases.sort(key=lambda c: c.get("created_at", ""), reverse=True)
    return cases[:limit]


def log_alert(snake, patient_contact, channel, message, sent_via_sms):
    """Logs a hospital alert to Supabase or local file. Never raises."""
    try:
        record = {
            "id": str(uuid.uuid4()),
            "snake": snake,
            "patient_contact": patient_contact,
            "channel": channel,
            "message": message,
            "sent_via_sms": sent_via_sms,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }

        if _using_supabase:
            try:
                _supabase_client.table("hospital_alerts").insert({
                    "snake": snake,
                    "patient_contact": patient_contact,
                    "channel": channel,
                    "message": message,
                    "sent_via_sms": sent_via_sms
                }).execute()
                print(f"[database] Alert logged to Supabase for {snake}")
                return True
            except Exception as e:
                print(f"[database] Supabase alert insert failed, "
                      f"writing to local file instead: {e}")

        try:
            alerts = _read_local(LOCAL_ALERTS_FILE)
            alerts.append(record)
            _write_local(alerts, LOCAL_ALERTS_FILE)
            return True
        except Exception as e:
            print(f"[database] Local alert write failed: {e}")
            return False
    except Exception as e:
        print(f"[database] log_alert completely failed (non-fatal): {e}")
        return False


def get_alerts(limit=50):
    """Returns the most recent hospital alerts."""
    if _using_supabase:
        try:
            res = (
                _supabase_client.table("hospital_alerts")
                .select("*")
                .order("created_at", desc=True)
                .limit(limit)
                .execute()
            )
            return res.data
        except Exception as e:
            print(f"[database] Supabase alert read failed, reading local file instead: {e}")

    alerts = _read_local(LOCAL_ALERTS_FILE)
    alerts.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    return alerts[:limit]


def storage_backend():
    return "supabase" if _using_supabase else "local file (data/cases.json)"


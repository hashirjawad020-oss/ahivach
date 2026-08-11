"""
test_ahivach.py — run with: pytest test_ahivach.py -v

Exercises every channel end to end with ZERO Twilio/Supabase
credentials configured (proves the local fallback works), and
specifically checks the bug that was in the original ivr.py:
that /voice must NOT fire an alert/log, and /voice/snake-selected
must fire EXACTLY ONE alert and ONE log per call.
"""
import json
import shutil
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

DATA_DIR = Path(__file__).parent / "data"


@pytest.fixture(autouse=True)
def clean_state():
    """Wipe local data + in-memory sessions before every test."""
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)
    import main
    import whatsapp
    import web
    whatsapp.sessions.clear()
    web.message_sessions.clear()
    yield
    if DATA_DIR.exists():
        shutil.rmtree(DATA_DIR)


@pytest.fixture
def client():
    import main
    return TestClient(main.app)


# ── Core logic sanity ──────────────────────────────────────

def test_identify_snake_all_branches():
    from core import identify_snake
    assert identify_snake(["yes", "no", "no", "no"]) == "Indian Cobra"
    assert identify_snake(["no", "yes", "no", "no"]) == "Common Krait"
    assert identify_snake(["no", "no", "yes", "no"]) == "Russell's Viper"
    assert identify_snake(["no", "no", "no", "yes"]) == "Saw-Scaled Viper"
    assert identify_snake(["no", "no", "no", "no"]) == "Unknown"
    # First "yes" wins if multiple are yes (matches original elif chain)
    assert identify_snake(["yes", "yes", "yes", "yes"]) == "Indian Cobra"


def test_all_snakes_have_first_aid_and_ivr_content():
    from core import FIRST_AID, IVR_WARNINGS, SNAKE_MAP
    for snake in set(SNAKE_MAP.values()):
        assert snake in FIRST_AID, f"{snake} missing from FIRST_AID"
        assert snake in IVR_WARNINGS, f"{snake} missing from IVR_WARNINGS"


# ── WhatsApp channel: full 4-question flow ─────────────────

def test_whatsapp_full_flow_identifies_cobra_and_logs_once(client):
    phone = "whatsapp:+919876543210"

    r1 = client.post("/whatsapp", data={"From": phone, "Body": "hi"})
    assert r1.status_code == 200
    assert "Q1" in r1.text

    r2 = client.post("/whatsapp", data={"From": phone, "Body": "yes"})
    assert "Q2" in r2.text

    r3 = client.post("/whatsapp", data={"From": phone, "Body": "no"})
    assert "Q3" in r3.text

    r4 = client.post("/whatsapp", data={"From": phone, "Body": "no"})
    assert "Q4" in r4.text

    r5 = client.post("/whatsapp", data={"From": phone, "Body": "no"})
    assert "INDIAN COBRA" in r5.text
    assert "HOSPITAL" in r5.text

    # Exactly one case logged
    cases = json.loads((DATA_DIR / "cases.json").read_text())
    assert len(cases) == 1
    assert cases[0]["snake_identified"] == "Indian Cobra"
    assert cases[0]["channel"] == "whatsapp"

    # Exactly one hospital alert fired
    alerts = json.loads((DATA_DIR / "hospital_alerts.json").read_text())
    assert len(alerts) == 1
    assert alerts[0]["snake"] == "Indian Cobra"


def test_whatsapp_invalid_answer_reprompts_without_logging(client):
    phone = "whatsapp:+919999999999"
    client.post("/whatsapp", data={"From": phone, "Body": "hi"})
    r = client.post("/whatsapp", data={"From": phone, "Body": "maybe"})
    assert "YES" in r.text and "NO" in r.text
    assert not DATA_DIR.exists() or not (DATA_DIR / "cases.json").exists()


def test_whatsapp_restart_resets_session(client):
    phone = "whatsapp:+911111111111"
    client.post("/whatsapp", data={"From": phone, "Body": "hi"})
    client.post("/whatsapp", data={"From": phone, "Body": "yes"})
    r = client.post("/whatsapp", data={"From": phone, "Body": "restart"})
    assert "Q1" in r.text
    import whatsapp
    assert whatsapp.sessions[phone]["step"] == 0


def test_whatsapp_completed_session_blocks_further_logging(client):
    phone = "whatsapp:+922222222222"
    for body in ["hi", "no", "no", "no", "no"]:
        client.post("/whatsapp", data={"From": phone, "Body": body})
    r = client.post("/whatsapp", data={"From": phone, "Body": "yes"})
    assert "already been logged" in r.text
    cases = json.loads((DATA_DIR / "cases.json").read_text())
    assert len(cases) == 1  # still just one, no duplicate


# ── IVR channel: the critical bug fix ──────────────────────

def test_voice_incoming_does_not_fire_alert_or_log(client):
    """
    This is THE bug from the original code: /voice used to fire
    a hospital alert + case log immediately on connect, before
    the caller pressed anything. Confirm that no longer happens.
    """
    r = client.post("/voice", data={"From": "+919876543210"})
    assert r.status_code == 200
    assert "AHIVACH Snakebite Emergency" in r.text
    assert not DATA_DIR.exists() or not (DATA_DIR / "cases.json").exists()
    assert not DATA_DIR.exists() or not (DATA_DIR / "hospital_alerts.json").exists()


def test_voice_snake_selected_fires_exactly_once_per_call(client):
    r = client.post(
        "/voice/snake-selected",
        data={"Digits": "2", "From": "+919876543210"},
    )
    assert "Common Krait" in r.text

    cases = json.loads((DATA_DIR / "cases.json").read_text())
    assert len(cases) == 1
    assert cases[0]["snake_identified"] == "Common Krait"
    assert cases[0]["channel"] == "ivr"

    alerts = json.loads((DATA_DIR / "hospital_alerts.json").read_text())
    assert len(alerts) == 1


def test_voice_snake_selected_handles_empty_digits_as_timeout(client):
    """Simulates action_on_empty_result=True firing with no Digits."""
    r = client.post("/voice/snake-selected", data={"From": "+919876543210"})
    assert "Snake species unknown" in r.text
    cases = json.loads((DATA_DIR / "cases.json").read_text())
    assert len(cases) == 1
    assert cases[0]["snake_identified"] == "Unknown"
    assert cases[0]["answers"] == "no_input"


def test_voice_full_call_only_logs_once_total(client):
    """
    End-to-end: connecting the call must not log anything; only
    the keypress step should. Total across a full call = 1 log,
    1 alert — not 2 (that was the original bug).
    """
    client.post("/voice", data={"From": "+919876543210"})
    client.post("/voice/snake-selected", data={"Digits": "4", "From": "+919876543210"})

    cases = json.loads((DATA_DIR / "cases.json").read_text())
    alerts = json.loads((DATA_DIR / "hospital_alerts.json").read_text())
    assert len(cases) == 1
    assert len(alerts) == 1
    assert cases[0]["snake_identified"] == "Saw-Scaled Viper"


# ── Web simulator channel ──────────────────────────────────

def test_web_message_flow_matches_whatsapp_logic(client):
    sid = "test-session-1"
    r1 = client.post("/web/message", json={"session_id": sid, "message": ""})
    assert "Q1" in r1.json()["reply"]

    for ans in ["no", "no", "no", "yes"]:
        r = client.post("/web/message", json={"session_id": sid, "message": ans})
    assert "SAW-SCALED VIPER" in r.json()["reply"]
    assert r.json()["complete"] is True

    cases = json.loads((DATA_DIR / "cases.json").read_text())
    assert len(cases) == 1
    assert cases[0]["channel"] == "web"


def test_web_call_simulator_fires_once_on_keypress_not_on_start(client):
    sid = "test-call-1"
    client.post("/web/call/start", json={"session_id": sid})
    assert not DATA_DIR.exists() or not (DATA_DIR / "cases.json").exists()

    r = client.post("/web/call/keypress", json={"session_id": sid, "digit": "1"})
    assert "Cobra" in r.json()["message"]

    cases = json.loads((DATA_DIR / "cases.json").read_text())
    assert len(cases) == 1
    assert cases[0]["channel"] == "ivr-sim"


# ── Dashboard / status API ──────────────────────────────────

def test_api_status_reports_local_fallback_with_no_credentials(client):
    r = client.get("/api/status")
    data = r.json()
    assert data["database_backend"] == "local file (data/cases.json)"
    assert "no SMS provider" not in data["notification_backend"]  # just a label check
    assert data["notification_backend"] == "local log only (data/hospital_alerts.json)"


def test_api_cases_reflects_multiple_channels(client):
    client.post("/whatsapp", data={"From": "whatsapp:+91111", "Body": "hi"})
    for b in ["yes", "no", "no", "no"]:
        client.post("/whatsapp", data={"From": "whatsapp:+91111", "Body": b})
    client.post("/voice/snake-selected", data={"Digits": "2", "From": "+92222"})

    r = client.get("/api/cases")
    cases = r.json()["cases"]
    assert len(cases) == 2
    channels = {c["channel"] for c in cases}
    assert channels == {"whatsapp", "ivr"}


def test_dashboard_and_simulator_pages_load(client):
    assert client.get("/dashboard").status_code == 200
    assert client.get("/simulator").status_code == 200


def test_home_health_check(client):
    r = client.get("/")
    data = r.json()
    assert data["status"] == "AHIVACH is running"
    assert "WhatsApp Bot" in data["systems"]

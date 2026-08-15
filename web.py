# web.py
# Web channel adapter — lets you exercise the EXACT same
# logic (core.py), EXACT same database writes (database.py),
# and EXACT same hospital-alert calls (notifications.py) as
# WhatsApp/IVR would, but from a plain browser page. No Twilio
# account, no phone, no WhatsApp needed. This is a stand-in
# for testing today; swap/add real channels later without
# touching core.py, database.py, or notifications.py.

from fastapi import Body
from notifications import send_hospital_alert
from database import log_case
from core import (
    QUESTIONS,
    FIRST_AID,
    identify_snake,
    COMMON_PROTOCOL,
    IVR_WARNINGS,
    SNAKE_MAP,
    recommended_hospitals_text,
    build_hospital_message,
    HOSPITAL_PREP,
)

import hashlib

def get_fake_contact(session_id, prefix="98765"):
    h = int(hashlib.sha256(session_id.encode()).hexdigest(), 16)
    return f"+91{prefix}{h % 100000:05d}"

# Key = session_id (a random id the browser generates per tab),
# value = progress through the 4 questions. Same in-memory
# caveat as whatsapp.py's sessions.
message_sessions = {}


def setup_web_routes(app):

    @app.post("/web/message")
    async def web_message(payload: dict = Body(...)):
        """
        Simulates the WhatsApp question flow.
        payload: {"session_id": str, "message": str}
        First call for a new session_id should send message="" to
        get Q1 without it being interpreted as an answer.
        """
        session_id = payload.get("session_id", "unknown")
        incoming = (payload.get("message") or "").strip().lower()

        if session_id not in message_sessions:
            message_sessions[session_id] = {
                "step": 0, "answers": [], "complete": False
            }
            return {"reply": QUESTIONS[0], "complete": False}

        session = message_sessions[session_id]

        if incoming == "restart":
            message_sessions[session_id] = {
                "step": 0, "answers": [], "complete": False
            }
            return {"reply": "Starting a new report.\n\n" + QUESTIONS[0], "complete": False}

        if session["complete"]:
            return {
                "reply": (
                    "This case has already been logged and the hospital "
                    "alerted.\n\nType RESTART to start a new report."
                ),
                "complete": True,
            }

        step = session["step"]

        if incoming not in ["yes", "no"]:
            return {
                "reply": "Please reply with YES or NO only.\n\n" + QUESTIONS[step],
                "complete": False,
            }

        session["answers"].append(incoming)
        session["step"] += 1

        if session["step"] < 4:
            return {"reply": QUESTIONS[session["step"]], "complete": False}

        # All 4 answered — identify, respond, alert, log (exactly once)
        snake = identify_snake(session["answers"])
        session["complete"] = True

        contact = get_fake_contact(session_id, prefix="98765")
        send_hospital_alert(snake, contact, "web")
        log_case(contact, "web", snake, session["answers"])

        reply = FIRST_AID[snake] + "\n\n" + recommended_hospitals_text()
        hospital_preview = build_hospital_message(
            snake, contact, "web"
        )
        return {
            "reply": reply,
            "complete": True,
            "snake": snake,
            "hospital_alert_preview": hospital_preview,
            "hospital_prep": HOSPITAL_PREP.get(snake, HOSPITAL_PREP["Unknown"]),
        }

    @app.post("/web/call/start")
    async def web_call_start(payload: dict = Body(...)):
        """
        Simulates the simplified outbound call flow:
        Plays the common protocol, logs the case as Unknown,
        and fires the hospital alert immediately (no keypress).
        """
        session_id = payload.get("session_id", "unknown")
        contact = get_fake_contact(session_id, prefix="91234")
        
        # Fire hospital alert
        send_hospital_alert("Unknown", contact, "ivr-sim")
        
        # Log case
        log_case(
            contact, "ivr-sim", "Unknown", "auto_logged_on_call"
        )

        follow_up = (
            "Your case has been registered with AHIVACH. "
            "A hospital has been alerted and an ambulance has been requested. "
            "Stay calm, keep the bitten limb below heart level, "
            "and do not apply any tourniquet or cut the wound. "
            "Help is on the way. Goodbye."
        )

        return {"message": COMMON_PROTOCOL + "\n\n(English Follow-up)\n" + follow_up}

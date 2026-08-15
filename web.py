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
        Simulates IVR call connect: plays the common protocol only.
        No alert or case log here — same rule as /voice in ivr.py.
        """
        return {"message": COMMON_PROTOCOL}

    @app.post("/web/call/keypress")
    async def web_call_keypress(payload: dict = Body(...)):
        """
        Simulates /voice/snake-selected: one keypress → one alert,
        one case log, species-specific warning.
        """
        session_id = payload.get("session_id", "unknown")
        digit = str(payload.get("digit", ""))
        snake = SNAKE_MAP.get(digit, "Unknown")
        warning = IVR_WARNINGS[snake]
        contact = get_fake_contact(session_id, prefix="91234")

        send_hospital_alert(snake, contact, "ivr-sim")
        log_case(
            contact,
            "ivr-sim",
            snake,
            f"key_{digit}" if digit else "no_input",
        )

        return {"message": warning, "snake": snake}
       
# whatsapp.py
# WhatsApp channel adapter. Owns the WhatsApp-specific bits
# (Twilio's MessagingResponse/TwiML, session-by-phone-number).
# All snake-ID logic and message content comes from core.py —
# this file just adapts that shared logic to WhatsApp's shape.

from fastapi import Form, Response
from twilio.twiml.messaging_response import MessagingResponse
from notifications import send_hospital_alert
from database import log_case
from core import QUESTIONS, FIRST_AID, identify_snake

# Key = phone number (Twilio's "From", e.g. "whatsapp:+91..."),
# value = that user's progress through the 4 questions.
# In-memory: resets on server restart. Fine for a demo; move to
# Supabase if this needs to survive restarts in production.
sessions = {}


def setup_whatsapp_routes(app):

    @app.post("/whatsapp")
    async def whatsapp_webhook(
        From: str = Form(...),
        Body: str = Form(...)
    ):
        incoming = Body.strip().lower()
        sender = From

        response = MessagingResponse()
        msg = response.message()

        # ── NEW USER ─────────────────────────────────────
        if sender not in sessions:
            sessions[sender] = {"step": 0, "answers": [], "complete": False}
            msg.body(QUESTIONS[0])
            return Response(content=str(response), media_type="application/xml")

        session = sessions[sender]

        # ── RESTART COMMAND ──────────────────────────────
        if incoming == "restart":
            sessions[sender] = {"step": 0, "answers": [], "complete": False}
            msg.body("Starting a new report.\n\n" + QUESTIONS[0])
            return Response(content=str(response), media_type="application/xml")

        # ── CONVERSATION COMPLETE ─────────────────────────
        if session["complete"]:
            msg.body(
                "This case has already been logged and the hospital "
                "alerted.\n\nTo start a new report type *RESTART*"
            )
            return Response(content=str(response), media_type="application/xml")

        # ── ANSWERING QUESTIONS ───────────────────────────
        step = session["step"]

        if incoming not in ["yes", "no"]:
            msg.body("Please reply with *YES* or *NO* only.\n\n" + QUESTIONS[step])
            return Response(content=str(response), media_type="application/xml")

        session["answers"].append(incoming)
        session["step"] += 1

        if session["step"] < 4:
            msg.body(QUESTIONS[session["step"]])
            return Response(content=str(response), media_type="application/xml")

        # All 4 answered — identify, respond, alert, log (exactly once)
        snake = identify_snake(session["answers"])
        session["complete"] = True

        msg.body(FIRST_AID[snake])
        send_hospital_alert(snake, sender, "whatsapp")
        log_case(sender, "whatsapp", snake, session["answers"])

        return Response(content=str(response), media_type="application/xml")

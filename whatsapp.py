# whatsapp.py
# WhatsApp channel adapter. Owns two parallel WhatsApp entry
# points that both drive the same 4-question flow:
#   - /whatsapp       Twilio's WhatsApp sandbox/API (TwiML reply)
#   - /webhook/meta   Meta's WhatsApp Cloud API direct (HTTP POST reply)
# All snake-ID logic and message content comes from core.py —
# this file just adapts that shared logic to each provider's shape.

import os
import httpx
from fastapi import Form, Request, Response
from twilio.twiml.messaging_response import MessagingResponse
from notifications import send_hospital_alert
from database import log_case
from core import QUESTIONS, FIRST_AID, identify_snake, recommended_hospitals_text

# Two separate session dicts, kept apart deliberately: Twilio's
# sender id looks like "whatsapp:+91..." and Meta's looks like
# "91..." (no prefix, no plus). Sharing one dict keyed by raw
# sender string risks an accidental collision between the same
# phone number arriving via two different providers, and makes
# it unclear at a glance which provider a session came from.
# Both are in-memory: resets on server restart. Fine for a demo;
# move to Supabase if this needs to survive restarts in production.
sessions = {}          # Twilio WhatsApp sessions
meta_sessions = {}     # Meta Cloud API sessions

WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")


def _advance_conversation(session, incoming, sender, channel_label):
    """
    Shared step logic for the 4-question YES/NO flow, used by
    both the Twilio and Meta webhooks so the two providers can't
    drift apart on how a message is handled.

    Returns the reply text to send back. Mutates `session` in
    place. Fires the hospital alert + case log exactly once, on
    the turn that completes the 4th answer — same guarantee the
    original Twilio-only version had.
    """
    step = session["step"]

    if incoming not in ["yes", "no"]:
        return "Please reply with *YES* or *NO* only.\n\n" + QUESTIONS[step]

    session["answers"].append(incoming)
    session["step"] += 1

    if session["step"] < 4:
        return QUESTIONS[session["step"]]

    # All 4 answered — identify, respond, alert, log (exactly once)
    snake = identify_snake(session["answers"])
    session["complete"] = True

    reply = FIRST_AID[snake] + "\n\n" + recommended_hospitals_text()
    send_hospital_alert(snake, sender, channel_label)
    log_case(sender, channel_label, snake, session["answers"])

    return reply


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
        reply_text = _advance_conversation(session, incoming, sender, "whatsapp")
        msg.body(reply_text)
        return Response(content=str(response), media_type="application/xml")

    # ── META WHATSAPP CLOUD API ───────────────────────────
    # Same 4-question flow as above, different transport: Meta
    # expects webhook verification on GET, and replies are sent
    # as an outbound HTTP POST to the Graph API rather than
    # returned inline as TwiML.

    @app.get("/webhook/meta")
    async def meta_verify(request: Request):
        params = request.query_params
        if (params.get("hub.mode") == "subscribe"
                and params.get("hub.verify_token") == WHATSAPP_VERIFY_TOKEN):
            return Response(content=params.get("hub.challenge"), media_type="text/plain")
        return Response(status_code=403)

    @app.post("/webhook/meta")
    async def meta_receive(request: Request):
        body = await request.json()
        try:
            entry = body["entry"][0]["changes"][0]["value"]
            message = entry["messages"][0]
            sender = message["from"]
            text = message["text"]["body"]
        except (KeyError, IndexError):
            # Not an inbound text message (delivery receipt, status
            # update, etc). Nothing to reply to.
            return {"status": "ignored"}

        incoming = text.strip().lower()

        # ── NEW USER ─────────────────────────────────────
        if sender not in meta_sessions:
            meta_sessions[sender] = {"step": 0, "answers": [], "complete": False}
            reply_text = QUESTIONS[0]

        else:
            session = meta_sessions[sender]

            # ── RESTART COMMAND ──────────────────────────
            if incoming == "restart":
                meta_sessions[sender] = {"step": 0, "answers": [], "complete": False}
                reply_text = "Starting a new report.\n\n" + QUESTIONS[0]

            # ── CONVERSATION COMPLETE ─────────────────────
            elif session["complete"]:
                reply_text = (
                    "This case has already been logged and the hospital "
                    "alerted.\n\nTo start a new report type *RESTART*"
                )

            # ── ANSWERING QUESTIONS ────────────────────────
            else:
                reply_text = _advance_conversation(session, incoming, sender, "whatsapp_meta")

        async with httpx.AsyncClient() as client:
            await client.post(
                f"https://graph.facebook.com/v20.0/{WHATSAPP_PHONE_NUMBER_ID}/messages",
                headers={"Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"},
                json={
                    "messaging_product": "whatsapp",
                    "to": sender,
                    "text": {"body": reply_text}
                }
            )

        return {"status": "ok"}

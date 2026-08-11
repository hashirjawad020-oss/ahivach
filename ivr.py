from fastapi import Request, Response, Form
from twilio.twiml.voice_response import VoiceResponse, Gather
from notifications import send_hospital_alert
from database import log_case
from core import SNAKE_MAP, COMMON_PROTOCOL, IVR_WARNINGS

# ── VOICE SCRIPTS ─────────────────────────────────────────
# All snake-ID logic and script text now live in core.py —
# the single source of truth shared with the WhatsApp and
# web channels. This file only concerns itself with turning
# that content into TwiML and wiring up Twilio's request/
# response shape.
#
# Swap gather.say(...) / response.say(...) for
# gather.play(URL) / response.play(URL) once you have Kannada
# MP3s hosted somewhere Twilio can fetch them (see audio/README.md).

# ── IVR ROUTES ────────────────────────────────────────────
# These get added to main.py's app object
# Import this file in main.py

def setup_ivr_routes(app):

    @app.post("/voice")
    async def voice_incoming(request: Request):
        """
        Fires when someone calls your Twilio IVR number.
        Plays the common protocol, then waits for a keypress.

        IMPORTANT: this function only BUILDS the TwiML — it
        does not know yet whether the caller will press a key.
        Any side effect (SMS, database write) written here would
        fire the instant the call connects, before the caller has
        heard anything or had a chance to respond. That was the
        bug in the original version: it fired a bogus "Unknown"
        hospital alert and case-log on every single call.

        So this route does ONE thing: play the protocol and
        gather a keypress. action_on_empty_result=True makes
        Twilio call /voice/snake-selected even on timeout (with
        Digits empty) instead of silently hanging up — that
        route is where the real alert + log happens exactly once,
        whether the caller pressed a key or not.
        """
        response = VoiceResponse()

        gather = Gather(
            num_digits=1,
            action="/voice/snake-selected",
            method="POST",
            timeout=10,
            action_on_empty_result=True,
        )
        gather.say(COMMON_PROTOCOL, language="en-IN")
        response.append(gather)

        # Safety net: only reached if action_on_empty_result somehow
        # doesn't fire (e.g. caller hangs up mid-prompt). No alert/log
        # here — nothing to log for a call that never completed.
        response.say(
            "We did not receive your input. Goodbye.",
            language="en-IN"
        )

        return Response(
            content=str(response),
            media_type="application/xml"
        )

    @app.post("/voice/snake-selected")
    async def snake_selected(
        Digits: str = Form(default=""),
        From: str = Form(default="unknown")
    ):
        """
        Fires exactly once per call: either the caller pressed a
        key, or the Gather above timed out (Digits will be empty,
        which SNAKE_MAP.get(..., "Unknown") already handles).
        Plays the species-specific warning, fires ONE hospital
        alert, logs ONE case.
        """
        snake = SNAKE_MAP.get(Digits, "Unknown")
        warning = IVR_WARNINGS[snake]

        response = VoiceResponse()
        response.say(warning, language="en-IN")

        # Repeat the warning once
        response.pause(length=1)
        response.say("Repeating the instructions. " + warning, language="en-IN")

        # Fire hospital alert — exactly once per call
        send_hospital_alert(snake, From, "ivr")

        # Log case — exactly once per call
        log_case(From, "ivr", snake, f"key_{Digits}" if Digits else "no_input")

        return Response(
            content=str(response),
            media_type="application/xml"
        )

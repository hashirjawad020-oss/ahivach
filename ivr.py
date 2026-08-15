from fastapi import Request, Response, Form
from twilio.twiml.voice_response import VoiceResponse, Gather
from notifications import send_hospital_alert
from database import log_case
from core import SNAKE_MAP, IVR_WARNINGS

# ── VOICE SCRIPTS ─────────────────────────────────────────
# The common protocol now plays as a real Kannada recording
# (audio/common_protocol_kannada.mp3) instead of English TTS —
# it's a spoken SUMMARY covering the key first-aid points and
# the keypad options, not a word-for-word reading of core.py's
# COMMON_PROTOCOL text. If a full, section-by-section Kannada
# recording arrives later, this is the only file that needs to
# change — swap gather.play(...) below for one .play() per
# section, same pattern as before.
#
# The 4 species-specific warnings (IVR_WARNINGS in core.py)
# still use English TTS for now — same swap-in pattern applies
# once those are recorded too.

COMMON_PROTOCOL_AUDIO_PATH = "/audio/common_protocol_kannada.mp3"

# ── IVR ROUTES ────────────────────────────────────────────
# These get added to main.py's app object
# Import this file in main.py

def setup_ivr_routes(app):

    @app.post("/voice")
    async def voice_incoming(request: Request):
        """
        Fires when someone calls your Twilio IVR number.
        Plays the Kannada common-protocol recording, then waits
        for a keypress.

        IMPORTANT: this function only BUILDS the TwiML — it
        does not know yet whether the caller will press a key.
        Any side effect (SMS, database write) written here would
        fire the instant the call connects, before the caller has
        heard anything or had a chance to respond. That was the
        bug in the original version: it fired a bogus "Unknown"
        hospital alert and case-log on every single call.

        So this route does ONE thing: play the recording and
        gather a keypress. action_on_empty_result=True makes
        Twilio call /voice/snake-selected even on timeout (with
        Digits empty) instead of silently hanging up — that
        route is where the real alert + log happens exactly once,
        whether the caller pressed a key or not.
        """
        base_url = str(request.base_url).rstrip("/")

        response = VoiceResponse()

        gather = Gather(
            num_digits=1,
            action="/voice/snake-selected",
            method="POST",
            timeout=10,
            action_on_empty_result=True,
        )
        gather.play(base_url + COMMON_PROTOCOL_AUDIO_PATH)
        # Keypad menu spoken in English after the Kannada summary,
        # since the recording itself doesn't include per-digit
        # prompts. Caller can press any time during either part.
        gather.say(
            "Press 1 for cobra, 2 for krait, 3 for Russell's viper, "
            "4 for saw-scaled viper, 5 if unsure.",
            language="en-IN",
        )
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
        try:
            send_hospital_alert(snake, From, "ivr")
        except Exception as e:
            print(f"[ivr] Hospital alert failed (non-fatal): {e}")

        # Log case — exactly once per call
        try:
            log_case(From, "ivr", snake, f"key_{Digits}" if Digits else "no_input")
        except Exception as e:
            print(f"[ivr] Case logging failed (non-fatal): {e}")

        return Response(
            content=str(response),
            media_type="application/xml"
        )

# Audio files (not needed yet)

The IVR currently speaks in English via Twilio's built-in
text-to-speech (see `core.py`'s `COMMON_PROTOCOL` / `IVR_WARNINGS`,
used by `ivr.py`). That already works with zero files in this
folder.

When Kannada recordings are ready, put them here:

- common_protocol.mp3
- cobra_warning.mp3
- krait_warning.mp3
- russells_warning.mp3
- sawscaled_warning.mp3
- disclaimer.mp3

Host them somewhere Twilio can fetch over HTTPS (e.g. commit to
this repo and serve as static files from the deployed app, or
Supabase Storage). Then in `ivr.py`, change:

    gather.say(COMMON_PROTOCOL, language="en-IN")

to:

    gather.play("https://your-app-url/audio/common_protocol.mp3")

— same pattern for each `response.say(...)` call. No other file
needs to change.

Two ways to get the recordings:
1. Record with a Kannada speaker reading the text in core.py.
2. Generate with Google Cloud Text-to-Speech, which supports
   Kannada (kn-IN) and has a generous free monthly quota.

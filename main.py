# main.py
# Wires everything together. This file should stay small —
# it has no snake logic, no message content, no storage logic
# of its own. Each channel (whatsapp.py, ivr.py, web.py) owns
# its own routes; core.py/database.py/notifications.py own the
# actual product.

from pathlib import Path
from fastapi import FastAPI, Body
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from whatsapp import setup_whatsapp_routes
from ivr import setup_ivr_routes
from web import setup_web_routes
from followup_routes import setup_followup_routes
import database
import notifications

load_dotenv()

app = FastAPI(title="AHIVACH")

setup_whatsapp_routes(app)
setup_ivr_routes(app)
setup_web_routes(app)
setup_followup_routes(app)

BASE_DIR = Path(__file__).parent


# ── DASHBOARD + SIMULATOR DATA API ────────────────────────
# The dashboard and simulator pages hit these instead of
# talking to Supabase/Twilio directly, so they work identically
# whether those are configured or not.

@app.get("/api/cases")
def api_cases(limit: int = 50):
    return {"cases": database.get_cases(limit=limit)}


@app.get("/api/alerts")
def api_alerts(limit: int = 50):
    return {"alerts": notifications.get_alerts(limit=limit)}


@app.get("/api/status")
def api_status():
    return {
        "database_backend": database.storage_backend(),
        "notification_backend": notifications.notification_backend(),
    }


# ── AMBULANCE CONFIRM-BEFORE-DISPATCH FLOW ─────────────────
# Doctor-validated: hospital must confirm via phone call before
# ambulance is dispatched, to prevent abuse. Two-step flow:
# 1. Hospital receives alert → taps "Confirm" after calling patient
# 2. Hospital taps "Dispatch" → ambulance status updates

@app.post("/api/cases/{case_id}/ambulance/confirm")
def ambulance_confirm(case_id: str):
    """Step 1: Hospital confirms the case is genuine after calling the patient."""
    success = database.update_case_field(case_id, "ambulance_status", "confirmed")
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "confirmed", "case_id": case_id}


@app.post("/api/cases/{case_id}/ambulance/dispatch")
def ambulance_dispatch(case_id: str):
    """Step 2: Hospital dispatches ambulance after confirmation."""
    success = database.update_case_field(case_id, "ambulance_status", "dispatched")
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "dispatched", "case_id": case_id}


@app.post("/api/cases/{case_id}/ambulance/arrived")
def ambulance_arrived(case_id: str):
    """Optional: mark ambulance as arrived at patient location."""
    success = database.update_case_field(case_id, "ambulance_status", "arrived")
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "arrived", "case_id": case_id}


# ── SPECIES FEEDBACK LOOP ──────────────────────────────────
# After treatment, hospital confirms the actual species. This
# feeds back to improve screening questions over time.

@app.post("/api/cases/{case_id}/confirm-species")
def confirm_species(case_id: str, payload: dict = Body(...)):
    """Hospital confirms the actual species after treatment."""
    confirmed = payload.get("confirmed_species")
    if not confirmed:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="confirmed_species is required")
    success = database.update_case_field(case_id, "confirmed_species", confirmed)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Case not found")
    return {"status": "species_confirmed", "case_id": case_id, "confirmed_species": confirmed}


# ── STATIC PAGES ───────────────────────────────────────────

@app.get("/dashboard")
def dashboard_page():
    return FileResponse(BASE_DIR / "dashboard" / "index.html")


@app.get("/audio/{filename}")
def audio_file(filename: str):
    # Twilio's gather.play() / response.play() needs a plain
    # public HTTPS URL to fetch audio from — this serves whatever
    # is in the audio/ folder. filename is constrained to this
    # folder only (no path traversal) since FastAPI's path param
    # doesn't include slashes by default.
    path = BASE_DIR / "audio" / filename
    if not path.is_file():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(path, media_type="audio/mpeg")


@app.get("/simulator")
def simulator_page():
    return FileResponse(BASE_DIR / "pages" / "simulator.html")


@app.get("/prevention")
def prevention_page():
    return FileResponse(BASE_DIR / "pages" / "prevention.html")


@app.get("/emergency-card")
def emergency_card_page():
    return FileResponse(BASE_DIR / "pages" / "emergency-card.html")


@app.get("/manifest.json")
def manifest():
    return FileResponse(BASE_DIR / "public" / "manifest.json")


@app.get("/sw.js")
def service_worker():
    return FileResponse(BASE_DIR / "public" / "sw.js")


@app.get("/icons/{filename}")
def icon_file(filename: str):
    path = BASE_DIR / "public" / "icons" / filename
    if not path.is_file():
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Icon not found")
    return FileResponse(path)


# ── HEALTH CHECK ─────────────────────────────────────────
@app.get("/")
def home():
    return {
        "status": "AHIVACH is running",
        "systems": ["WhatsApp Bot", "IVR Bot", "Web Simulator"],
        "try": ["/simulator", "/dashboard", "/prevention", "/emergency-card"],
        "version": "1.2",
    }

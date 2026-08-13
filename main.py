# main.py
# Wires everything together. This file should stay small —
# it has no snake logic, no message content, no storage logic
# of its own. Each channel (whatsapp.py, ivr.py, web.py) owns
# its own routes; core.py/database.py/notifications.py own the
# actual product.

from pathlib import Path
from fastapi import FastAPI
from fastapi.responses import FileResponse
from dotenv import load_dotenv

from whatsapp import setup_whatsapp_routes
from ivr import setup_ivr_routes
from web import setup_web_routes
import database
import notifications

load_dotenv()

app = FastAPI(title="AHIVACH")

setup_whatsapp_routes(app)
setup_ivr_routes(app)
setup_web_routes(app)

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


# ── HEALTH CHECK ─────────────────────────────────────────
@app.get("/")
def home():
    return {
        "status": "AHIVACH is running",
        "systems": ["WhatsApp Bot", "IVR Bot", "Web Simulator"],
        "database_backend": database.storage_backend(),
        "notification_backend": notifications.notification_backend(),
        "try": ["/simulator", "/dashboard"],
        "version": "1.0",
    }

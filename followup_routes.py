# followup_routes.py
# Case status / rescuer dispatch / follow-up routes.
# Python/FastAPI translation of followup_routes_reference.js.
#
# Wired in by main.py via setup_followup_routes(app).
# Requires Supabase to be configured (SUPABASE_URL + SUPABASE_KEY in .env).
# These three endpoints are no-ops (return 503) when running on the local-file
# fallback so the rest of the app still works without Supabase.

from datetime import datetime, timezone
from fastapi import Body, HTTPException
from database import _supabase_client, _using_supabase

VALID_STATUSES = [
    "reported",
    "hospital_alerted",
    "rescuer_dispatched",
    "admitted",
    "follow_up_pending",
    "resolved",
]
TERMINAL_OUTCOMES = ["recovered", "deceased", "lost_to_followup"]


def _require_supabase():
    if not _using_supabase:
        raise HTTPException(
            status_code=503,
            detail=(
                "Supabase is not configured. "
                "Set SUPABASE_URL and SUPABASE_KEY in your .env file."
            ),
        )


def _now_iso():
    return datetime.now(timezone.utc).isoformat()


def setup_followup_routes(app):

    # ── PATCH /api/cases/{case_id}/status ─────────────────────────────────
    # Body: { "case_status": "<one of VALID_STATUSES>" }
    # Updates the status column and status_updated_at timestamp.
    @app.patch("/api/cases/{case_id}/status")
    async def update_case_status(case_id: str, payload: dict = Body(...)):
        _require_supabase()
        case_status = payload.get("case_status")
        if case_status not in VALID_STATUSES:
            raise HTTPException(
                status_code=400,
                detail=f"invalid case_status. Must be one of: {VALID_STATUSES}",
            )
        try:
            res = (
                _supabase_client.table("cases")
                .update({"case_status": case_status, "status_updated_at": _now_iso()})
                .eq("id", case_id)
                .execute()
            )
            return {"case": res.data[0] if res.data else None}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ── POST /api/cases/{case_id}/rescuer ─────────────────────────────────
    # Body: { "rescuer_name": str, "contact_number": str, "notes": str }
    # Inserts a rescuer_dispatches row and bumps case_status to
    # 'rescuer_dispatched'.
    @app.post("/api/cases/{case_id}/rescuer")
    async def dispatch_rescuer(case_id: str, payload: dict = Body(...)):
        _require_supabase()
        rescuer_name = payload.get("rescuer_name")
        contact_number = payload.get("contact_number")
        notes = payload.get("notes")
        try:
            dispatch_res = (
                _supabase_client.table("rescuer_dispatches")
                .insert(
                    {
                        "case_id": case_id,
                        "rescuer_name": rescuer_name,
                        "contact_number": contact_number,
                        "notes": notes,
                    }
                )
                .execute()
            )
            _supabase_client.table("cases").update(
                {
                    "case_status": "rescuer_dispatched",
                    "status_updated_at": _now_iso(),
                }
            ).eq("id", case_id).execute()
            return {"dispatch": dispatch_res.data[0] if dispatch_res.data else None}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ── POST /api/cases/{case_id}/followup ────────────────────────────────
    # Body: { "outcome": "<recovered|still_under_treatment|lost_to_followup|deceased>",
    #         "notes": str }
    # Inserts a follow_ups row and bumps case_status to 'resolved' if the
    # outcome is terminal (recovered / deceased / lost_to_followup).
    @app.post("/api/cases/{case_id}/followup")
    async def log_followup(case_id: str, payload: dict = Body(...)):
        _require_supabase()
        outcome = payload.get("outcome")
        notes = payload.get("notes")
        try:
            followup_res = (
                _supabase_client.table("follow_ups")
                .insert({"case_id": case_id, "outcome": outcome, "notes": notes})
                .execute()
            )
            if outcome in TERMINAL_OUTCOMES:
                _supabase_client.table("cases").update(
                    {"case_status": "resolved", "status_updated_at": _now_iso()}
                ).eq("id", case_id).execute()
            return {"followup": followup_res.data[0] if followup_res.data else None}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

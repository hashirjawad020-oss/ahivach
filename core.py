# core.py
# ── THE PRODUCT ITSELF ────────────────────────────────────
# Snake ID logic, first-aid content, IVR scripts, hospital
# prep notes. No Twilio, no Supabase, no channel-specific code
# lives here — this is the part that stays IDENTICAL no matter
# what turns out to carry the WhatsApp/call/SMS later.

QUESTIONS = [
    (
        "🐍 AHIVACH Snakebite Emergency\n\n"
        "Stay calm. I will ask 4 quick questions "
        "to identify the snake.\n\n"
        "Q1: Did the snake spread a wide HOOD "
        "or flatten its neck?"
    ),
    (
        "Q2: Was the bite at NIGHT while the "
        "person was sleeping, and was it nearly "
        "PAINLESS?"
    ),
    (
        "Q3: Was the snake THICK-BODIED with "
        "a zigzag or chain pattern on its back?"
    ),
    (
        "Q4: Was the snake SMALL (under 60cm), "
        "sandy/brown coloured, and did it make a "
        "SIZZLING sound when threatened?"
    ),
]

def identify_snake(answers):
    """answers = list of 4 'yes'/'no' strings, in order."""
    if answers[0] == "yes":
        return "Indian Cobra"
    elif answers[1] == "yes":
        return "Common Krait"
    elif answers[2] == "yes":
        return "Russell's Viper"
    elif answers[3] == "yes":
        return "Saw-Scaled Viper"
    else:
        return "Unknown"

# ── Ambulance status constants ────────────────────────────
# Tracks the ambulance lifecycle per case. The hospital must
# confirm before dispatch to prevent abuse (per doctor advice).
AMBULANCE_REQUESTED = "requested"
AMBULANCE_CONFIRMED = "confirmed"
AMBULANCE_DISPATCHED = "dispatched"
AMBULANCE_ARRIVED = "arrived"

AMBULANCE_STATUSES = [
    AMBULANCE_REQUESTED,
    AMBULANCE_CONFIRMED,
    AMBULANCE_DISPATCHED,
    AMBULANCE_ARRIVED,
]

# ── Why species matters (shown to patient) ────────────────
# The doctor confirmed: every patient gets the same polyvalent
# antivenom. The species prediction drives WHAT THE HOSPITAL
# PREPARES FOR — different monitoring tracks, different teams
# on standby. This text makes that explicit for the caller.
_WHY_IT_MATTERS = {
    "Indian Cobra": (
        "🏥 WHY THIS MATTERS: The hospital is now preparing "
        "ventilator support and airway management based on this "
        "assessment. All patients receive the same polyvalent "
        "antivenom — the species tells the team what COMPLICATIONS "
        "to watch for, not what to inject."
    ),
    "Common Krait": (
        "🏥 WHY THIS MATTERS: The hospital is now preparing "
        "ICU monitoring and delayed-collapse watch based on this "
        "assessment. All patients receive the same polyvalent "
        "antivenom — the species tells the team what COMPLICATIONS "
        "to watch for, not what to inject."
    ),
    "Russell's Viper": (
        "🏥 WHY THIS MATTERS: The hospital is now preparing "
        "dialysis and clotting support based on this assessment. "
        "All patients receive the same polyvalent antivenom — "
        "the species tells the team what COMPLICATIONS to watch "
        "for, not what to inject."
    ),
    "Saw-Scaled Viper": (
        "🏥 WHY THIS MATTERS: The hospital is now preparing "
        "blood products and haematology standby based on this "
        "assessment. All patients receive the same polyvalent "
        "antivenom — the species tells the team what COMPLICATIONS "
        "to watch for, not what to inject."
    ),
    "Unknown": (
        "🏥 The hospital is preparing for all scenarios. "
        "All patients receive polyvalent antivenom regardless "
        "of species — doctors confirm treatment on arrival."
    ),
}

FIRST_AID = {
    "Indian Cobra": (
        "⚠️ LIKELY MATCH: INDIAN COBRA "
        "(based on your description)\n\n"
        "COMMON FIRST AID — DO THIS NOW:\n"
        "✅ Stay calm, lie down, keep still\n"
        "✅ Keep bitten limb BELOW heart level\n"
        "✅ Remove rings, watches, tight clothing\n"
        "❌ Do NOT cut the wound\n"
        "❌ Do NOT tie a tourniquet\n"
        "❌ Do NOT suck the venom\n"
        "❌ Do NOT give food, water or alcohol\n\n"
        "⚠️ COBRA WARNING:\n"
        "Watch for drooping eyelids, difficulty "
        "swallowing or breathing. These mean "
        "paralysis is starting. The hospital has "
        "been alerted to prepare ventilator support.\n\n"
        + _WHY_IT_MATTERS["Indian Cobra"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
    "Common Krait": (
        "⚠️ LIKELY MATCH: COMMON KRAIT "
        "(based on your description)\n\n"
        "COMMON FIRST AID — DO THIS NOW:\n"
        "✅ Stay calm, lie down, keep still\n"
        "✅ Keep bitten limb BELOW heart level\n"
        "✅ Remove rings, watches, tight clothing\n"
        "❌ Do NOT cut the wound\n"
        "❌ Do NOT tie a tourniquet\n"
        "❌ Do NOT suck the venom\n"
        "❌ Do NOT give food, water or alcohol\n\n"
        "🚨 CRITICAL KRAIT WARNING:\n"
        "This venom works SLOWLY. The patient may "
        "seem completely fine right now but can "
        "collapse suddenly in 2-6 hours, especially "
        "at night. DO NOT leave them alone under "
        "any circumstances. The hospital has been "
        "alerted for ICU monitoring.\n\n"
        + _WHY_IT_MATTERS["Common Krait"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
    "Russell's Viper": (
        "⚠️ LIKELY MATCH: RUSSELL'S VIPER "
        "(based on your description)\n\n"
        "COMMON FIRST AID — DO THIS NOW:\n"
        "✅ Stay calm, lie down, keep still\n"
        "✅ Keep bitten limb BELOW heart level\n"
        "✅ Remove rings, watches, tight clothing\n"
        "❌ Do NOT cut the wound\n"
        "❌ Do NOT tie a tourniquet\n"
        "❌ Do NOT suck the venom\n"
        "❌ Do NOT give food, water or alcohol\n\n"
        "⚠️ RUSSELL'S VIPER WARNING:\n"
        "Watch for spreading swelling, blood in "
        "urine, or bleeding from gums. Kidney "
        "failure is likely. The hospital has been "
        "alerted to prepare dialysis and clotting "
        "support.\n\n"
        + _WHY_IT_MATTERS["Russell's Viper"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
    "Saw-Scaled Viper": (
        "⚠️ LIKELY MATCH: SAW-SCALED VIPER "
        "(based on your description)\n\n"
        "COMMON FIRST AID — DO THIS NOW:\n"
        "✅ Stay calm, lie down, keep still\n"
        "✅ Keep bitten limb BELOW heart level\n"
        "✅ Remove rings, watches, tight clothing\n"
        "❌ Do NOT cut the wound\n"
        "❌ Do NOT tie a tourniquet\n"
        "❌ Do NOT suck the venom\n"
        "❌ Do NOT give food, water or alcohol\n\n"
        "⚠️ SAW-SCALED VIPER WARNING:\n"
        "Watch for bleeding from the bite that "
        "will not stop. Patient needs blood products "
        "urgently. The hospital has been alerted. "
        "Leave for hospital immediately.\n\n"
        + _WHY_IT_MATTERS["Saw-Scaled Viper"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
    "Unknown": (
        "⚠️ SNAKEBITE EMERGENCY — SPECIES UNCONFIRMED\n\n"
        "COMMON FIRST AID — DO THIS NOW:\n"
        "✅ Stay calm, lie down, keep still\n"
        "✅ Keep bitten limb BELOW heart level\n"
        "✅ Remove rings, watches, tight clothing\n"
        "❌ Do NOT cut the wound\n"
        "❌ Do NOT tie a tourniquet\n"
        "❌ Do NOT suck the venom\n"
        "❌ Do NOT give food, water or alcohol\n\n"
        + _WHY_IT_MATTERS["Unknown"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
}

# ── IVR-equivalent scripts (what the caller would hear) ───
SNAKE_MAP = {
    "1": "Indian Cobra",
    "2": "Common Krait",
    "3": "Russell's Viper",
    "4": "Saw-Scaled Viper",
    "5": "Unknown",
}

COMMON_PROTOCOL = (
    "AHIVACH Snakebite Emergency. Stay calm. Lay the person down. "
    "Do not cut the wound. Do not tie a cloth or tourniquet. "
    "Do not suck the venom. Remove rings and tight clothing near "
    "the bite. Keep the bitten limb below heart level. Do not give "
    "food, water, or alcohol. Now, based on what you saw, press a "
    "key. Press 1 if it raised a wide hood, like a cobra. "
    "Press 2 if it was a small dark snake, often a night bite while "
    "sleeping, like a krait. Press 3 if it was thick-bodied with a "
    "chain or zigzag pattern, like Russell's viper. Press 4 if it "
    "was small and sandy-coloured and made a sizzling sound, like a "
    "saw-scaled viper. Press 5 if you are not sure."
)

# ── Recommended antivenom-stocked hospitals (Bengaluru) ────
# Hardcoded for now — a real nearest-hospital-with-ASV-in-stock
# system needs live inventory data hospitals don't publish, so
# this is a deliberate, honest MVP scope: we recommend hospitals
# known to stock polyvalent ASV rather than guessing "nearest."
# Karnataka has had real district-level ASV shortages (KSMSCL,
# 2026), so this distinction is a genuine clinical point, not
# just a scope excuse. Swap/expand this list per-district later.
RECOMMENDED_HOSPITALS_BENGALURU = [
    {
        "name": "St John's Medical College & Hospital",
        "area": "Koramangala, Bengaluru",
        "note": "Tertiary care, stocks polyvalent ASV",
    },
    {
        "name": "Bowring & Lady Curzon Hospital",
        "area": "Shivaji Nagar, Bengaluru",
        "note": "Government hospital, ASV stocked per Karnataka snakebite protocol",
    },
    {
        "name": "Manipal Hospital (Old Airport Road)",
        "area": "HAL, Bengaluru",
        "note": "Tertiary care, stocks polyvalent ASV",
    },
]

IVR_WARNINGS = {
    "Indian Cobra": (
        "Likely match: Indian Cobra, based on your description. "
        "Watch for drooping eyelids, "
        "difficulty swallowing, or breathing difficulty — paralysis "
        "starting. Hospital alerted for ventilator support. "
        "An ambulance request has been sent. "
        "Go to hospital immediately."
    ),
    "Common Krait": (
        "Likely match: Common Krait, based on your description. "
        "Critical warning: this venom works "
        "slowly. The patient may seem fine now but can collapse "
        "suddenly in two to six hours, especially at night. Do not "
        "leave them alone. Hospital alerted for ICU monitoring. "
        "An ambulance request has been sent. "
        "Go to hospital immediately."
    ),
    "Russell's Viper": (
        "Likely match: Russell's Viper, based on your description. "
        "Watch for rapid swelling, blood "
        "in urine, or bleeding from gums. Kidney failure is likely "
        "within hours. Hospital alerted to prepare dialysis and "
        "clotting support. An ambulance request has been sent. "
        "Go to hospital immediately."
    ),
    "Saw-Scaled Viper": (
        "Likely match: Saw-Scaled Viper, based on your description. "
        "Watch for bleeding from the "
        "bite that will not stop. Patient needs blood products "
        "urgently. Hospital alerted. An ambulance request has "
        "been sent. Go to hospital immediately."
    ),
    "Unknown": (
        "Snake species could not be determined from your answers. "
        "Hospital alerted and preparing for "
        "your arrival with full snakebite protocol. "
        "An ambulance request has been sent. "
        "Go to hospital immediately."
    ),
}

# ── What the hospital's alert message should contain ──────
HOSPITAL_PREP = {
    "Indian Cobra": (
        "PREPARE: Airway management, ventilator standby, "
        "neostigmine readiness. WATCH: Drooping eyelids, "
        "breathing difficulty."
    ),
    "Common Krait": (
        "PREPARE: ICU monitoring, ventilator standby. "
        "CRITICAL: Do NOT discharge early — delayed collapse "
        "risk 2-6 hours post-bite. Patient may seem fine."
    ),
    "Russell's Viper": (
        "PREPARE: Nephrology alert, coagulation panel, "
        "FFP, dialysis standby. WATCH: AKI onset, "
        "bleeding from gums, blood in urine."
    ),
    "Saw-Scaled Viper": (
        "PREPARE: Blood products, FFP transfusion, "
        "haematology alert. WATCH: Uncontrolled bleeding "
        "from bite site."
    ),
    "Unknown": (
        "PREPARE: General polyvalent ASV protocol. "
        "Species unconfirmed — prepare for all scenarios."
    ),
}

# ── Confidence levels for the 4-question screening ────────
_CONFIDENCE = {
    "Indian Cobra": "MODERATE",
    "Common Krait": "MODERATE",
    "Russell's Viper": "MODERATE",
    "Saw-Scaled Viper": "MODERATE",
    "Unknown": "LOW — species could not be determined",
}

def build_hospital_message(snake, patient_contact, channel):
    prep = HOSPITAL_PREP.get(snake, HOSPITAL_PREP["Unknown"])
    confidence = _CONFIDENCE.get(snake, "LOW")
    return (
        f"🚨 AHIVACH EMERGENCY ALERT\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"LIKELY SPECIES: {snake}\n"
        f"ASSESSMENT CONFIDENCE: {confidence} "
        f"(4-question rapid screening)\n"
        f"PATIENT CONTACT: {patient_contact}\n"
        f"CHANNEL: {channel.upper()}\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"{prep}\n\n"
        f"TREATMENT: Administer polyvalent ASV regardless "
        f"of species. Confirm species on arrival.\n\n"
        f"🚑 AMBULANCE: Requested. Tap CONFIRM on dashboard "
        f"after verification call to patient, then DISPATCH.\n"
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        f"— AHIVACH Emergency Response System"
    )


def recommended_hospitals_text():
    """
    Patient-facing text: which hospitals to go to. Not the alert
    sent TO the hospital — this is shown/spoken to the caller.
    """
    lines = [
        "🏥 Go to a hospital that stocks polyvalent antivenom — not "
        "just the nearest one. Right antivenom availability matters "
        "more than distance."
    ]
    for h in RECOMMENDED_HOSPITALS_BENGALURU:
        lines.append(f"• {h['name']} ({h['area']})")
    return "\n".join(lines)

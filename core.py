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
        "to help identify the snake.\n\n"
        "Q1: Did the snake spread its neck wide like a fan "
        "or stand up with a flattened hood?"
    ),
    (
        "Q2: Did the bite happen at NIGHT while someone was "
        "sleeping, with little or no pain and hardly any "
        "visible bite mark?"
    ),
    (
        "Q3: Was the snake thick-bodied with large dark "
        "oval or chain-like spots in rows on its back?"
    ),
    (
        "Q4: Was the snake small (under 80 cm), brown or "
        "sandy coloured, and did it make a rasping or "
        "scraping sound when threatened?"
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
        "🏥 WHY THIS MATTERS: Based on your answers, the hospital "
        "is preparing ventilator support and Atropine-Neostigmine "
        "readiness. All patients receive the same polyvalent "
        "antivenom — species info tells the team what to PREPARE "
        "FOR, not what to inject."
    ),
    "Common Krait": (
        "🏥 WHY THIS MATTERS: Based on your answers, the hospital "
        "is preparing ICU monitoring and mechanical ventilation. "
        "Krait venom does NOT respond to Atropine-Neostigmine. "
        "All patients receive the same polyvalent antivenom — "
        "species info tells the team what to PREPARE FOR, not "
        "what to inject."
    ),
    "Russell's Viper": (
        "🏥 WHY THIS MATTERS: Based on your answers, the hospital "
        "is preparing dialysis, blood products, and clotting tests "
        "(20WBCT). All patients receive the same polyvalent "
        "antivenom — species info tells the team what to PREPARE "
        "FOR, not what to inject."
    ),
    "Saw-Scaled Viper": (
        "🏥 WHY THIS MATTERS: Based on your answers, the hospital "
        "is preparing blood products and clotting tests (20WBCT). "
        "All patients receive the same polyvalent antivenom — "
        "species info tells the team what to PREPARE FOR, not "
        "what to inject."
    ),
    "Unknown": (
        "🏥 The hospital is preparing for all scenarios. "
        "All patients receive polyvalent antivenom regardless "
        "of species — doctors confirm treatment on arrival."
    ),
}

_COMMON_FIRST_AID = (
    "COMMON FIRST AID — DO THIS NOW:\n"
    "✅ Stay calm — about 70% of bites are non-venomous; "
    "panic spreads venom faster\n"
    "✅ Immobilise the bitten limb like a fracture — splint "
    "with any rigid object (stick, spade, rolled newspaper)\n"
    "✅ Keep bitten limb BELOW heart level\n"
    "✅ Remove rings, watches, tight clothing near the bite\n"
    "✅ Transport passively — patient must NOT walk, run, or drive\n"
    "✅ Note the time of bite — if safe, photograph the snake "
    "without approaching it\n"
    "✅ Call 108 and alert the nearest hospital IMMEDIATELY\n"
    "✅ Nothing by mouth until at hospital\n"
    "❌ Do NOT apply a tourniquet or tight binding\n"
    "❌ Do NOT cut the wound or try to suck out venom\n"
    "❌ Do NOT wash or interfere with the bite wound\n"
    "❌ Do NOT use traditional remedies, black stones, herbs, "
    "or electric shock\n"
    "❌ Do NOT attempt to kill or capture the snake\n"
    "❌ Do NOT give aspirin or NSAIDs — paracetamol only, "
    "at hospital\n"
)

FIRST_AID = {
    "Indian Cobra": (
        "⚠️ MOST LIKELY: INDIAN COBRA "
        "(based on what you described — not a diagnosis)\n\n"
        + _COMMON_FIRST_AID + "\n\n"
        "⚠️ COBRA WARNING:\n"
        "Watch for drooping eyelids, difficulty swallowing, "
        "or breathing problems — descending paralysis may start "
        "within 30 minutes to 6 hours. Local swelling and "
        "burning at the bite are common. The hospital has been "
        "alerted to prepare ventilator support.\n\n"
        + _WHY_IT_MATTERS["Indian Cobra"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY — do not wait at home\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
    "Common Krait": (
        "⚠️ MOST LIKELY: COMMON KRAIT "
        "(based on what you described — not a diagnosis)\n\n"
        + _COMMON_FIRST_AID + "\n\n"
        "🚨 CRITICAL KRAIT WARNING:\n"
        "Krait bites are often invisible — little or no pain "
        "and no visible mark. Symptoms are DELAYED: 6–12 hours "
        "after the bite. The patient may seem fine now but can "
        "collapse suddenly with paralysis. DO NOT leave them "
        "alone. DO NOT wait at home to see if symptoms appear. "
        "The hospital has been alerted for ICU monitoring and "
        "ventilator standby.\n\n"
        + _WHY_IT_MATTERS["Common Krait"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY — do not wait at home\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
    "Russell's Viper": (
        "⚠️ MOST LIKELY: RUSSELL'S VIPER "
        "(based on what you described — not a diagnosis)\n\n"
        + _COMMON_FIRST_AID + "\n\n"
        "⚠️ RUSSELL'S VIPER WARNING:\n"
        "Watch for intense pain, rapid swelling, bleeding from "
        "gums or bite site, and blood in urine. Clotting failure "
        "can begin within 30 minutes. Kidney failure may follow "
        "over hours to days. In some Karnataka and Tamil Nadu "
        "regions this snake also causes paralysis — do not "
        "ignore breathing difficulty. The hospital has been "
        "alerted to prepare dialysis and blood products.\n\n"
        + _WHY_IT_MATTERS["Russell's Viper"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY — do not wait at home\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
    "Saw-Scaled Viper": (
        "⚠️ MOST LIKELY: SAW-SCALED VIPER "
        "(based on what you described — not a diagnosis)\n\n"
        + _COMMON_FIRST_AID + "\n\n"
        "⚠️ SAW-SCALED VIPER WARNING:\n"
        "Watch for bleeding from gums, nose, or bite site that "
        "will not stop — severe clotting failure can begin within "
        "1–3 hours. Unlike Russell's Viper, kidney failure is "
        "rare. The hospital has been alerted to prepare blood "
        "products and clotting tests.\n\n"
        + _WHY_IT_MATTERS["Saw-Scaled Viper"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY — do not wait at home\n"
        "🚑 An ambulance request has been sent to "
        "the hospital. They will call you to confirm "
        "your location before dispatching."
    ),
    "Unknown": (
        "⚠️ SNAKEBITE EMERGENCY — SPECIES UNCONFIRMED\n\n"
        + _COMMON_FIRST_AID + "\n\n"
        "⚠️ ALL BITES ARE EMERGENCIES until a hospital confirms "
        "otherwise — even with no visible bite mark or pain.\n\n"
        + _WHY_IT_MATTERS["Unknown"] + "\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY — do not wait at home\n"
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
    "AHIVACH Snakebite Emergency. Stay calm. Immobilise the bitten "
    "limb like a broken bone — use a stick or any rigid object as a "
    "splint. Keep the limb below heart level. Do not cut the wound. "
    "Do not tie a tourniquet or tight band. Do not suck the venom. "
    "Do not wash the bite. Remove rings and tight clothing near the "
    "bite. The patient must not walk, run, or drive — carry them or "
    "use a vehicle. Do not give food, water, alcohol, aspirin, or "
    "painkillers except paracetamol at hospital. Call one zero eight "
    "immediately. Now, based on what you saw, press a key. Press 1 "
    "if it spread its neck wide like a fan, like a cobra. Press 2 if "
    "it was a dark banded snake and the bite was at night while "
    "sleeping with little pain, like a krait. Press 3 if it was "
    "thick-bodied with oval or chain-like spots in rows, like "
    "Russell's viper. Press 4 if it was small, sandy-coloured, and "
    "made a rasping sound, like a saw-scaled viper. Press 5 if you "
    "are not sure."
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
        "Most likely Indian Cobra, based on what you described — "
        "not a diagnosis. Watch for drooping eyelids, difficulty "
        "swallowing, or breathing problems — descending paralysis "
        "may start within 30 minutes to 6 hours. Hospital alerted "
        "for ventilator support and Atropine-Neostigmine readiness. "
        "An ambulance request has been sent. Go to hospital "
        "immediately — do not wait at home."
    ),
    "Common Krait": (
        "Most likely Common Krait, based on what you described — "
        "not a diagnosis. Critical warning: krait bites are often "
        "invisible with little pain. Symptoms are delayed 6 to 12 "
        "hours. The patient may seem fine now but can collapse "
        "suddenly with paralysis. Do not leave them alone. Do not "
        "wait at home. Hospital alerted for ICU monitoring and "
        "ventilator standby. An ambulance request has been sent. "
        "Go to hospital immediately."
    ),
    "Russell's Viper": (
        "Most likely Russell's Viper, based on what you described — "
        "not a diagnosis. Watch for intense pain, rapid swelling, "
        "bleeding from gums, and blood in urine. Clotting failure "
        "can begin within 30 minutes. Kidney failure may follow. "
        "In some regions this snake also causes paralysis. Hospital "
        "alerted to prepare dialysis and blood products. An "
        "ambulance request has been sent. Go to hospital "
        "immediately."
    ),
    "Saw-Scaled Viper": (
        "Most likely Saw-Scaled Viper, based on what you described — "
        "not a diagnosis. Watch for bleeding from gums, nose, or "
        "bite site that will not stop — clotting failure within 1 "
        "to 3 hours. Kidney failure is rare with this species. "
        "Hospital alerted to prepare blood products. An ambulance "
        "request has been sent. Go to hospital immediately."
    ),
    "Unknown": (
        "Snake species unknown — could not be determined from your "
        "answers. All bites are emergencies until a hospital confirms "
        "otherwise — even with no visible bite mark. Hospital "
        "alerted and preparing full snakebite protocol. An "
        "ambulance request has been sent. Go to hospital "
        "immediately — do not wait at home."
    ),
}

# ── What the hospital's alert message should contain ──────
HOSPITAL_PREP = {
    "Indian Cobra": (
        "PREPARE: Ventilator standby, airway management, "
        "Atropine-Neostigmine challenge readiness. "
        "WATCH: Descending paralysis, ptosis, local necrosis. "
        "ASV: Polyvalent, IV only — 10 vials if envenomation "
        "confirmed. Same dose for children."
    ),
    "Common Krait": (
        "PREPARE: ICU monitoring, mechanical ventilation standby "
        "(may be needed for days). Pre-synaptic neurotoxin — "
        "does NOT respond to Atropine-Neostigmine. "
        "CRITICAL: Bite often invisible; symptoms delayed 6–12 "
        "hours. Do NOT discharge early. ASV: Polyvalent, IV only "
        "— 10 vials if envenomation confirmed."
    ),
    "Russell's Viper": (
        "PREPARE: Run 20WBCT immediately. Dialysis standby, FFP "
        "and blood products, nephrology alert. WATCH: Coagulopathy "
        "within 30 min, AKI, systemic capillary leak syndrome. "
        "NOTE: Some Karnataka/Tamil Nadu populations also cause "
        "neuroparalysis — do not rule out. ASV: Polyvalent, IV "
        "only — 10 vials if envenomation confirmed."
    ),
    "Saw-Scaled Viper": (
        "PREPARE: Run 20WBCT. Blood products, FFP transfusion, "
        "haematology alert. WATCH: Severe coagulopathy within "
        "1–3 hours; AKI is rare. ASV: Polyvalent, IV only — "
        "6 vials if envenomation confirmed (lower than Russell's)."
    ),
    "Unknown": (
        "PREPARE: General polyvalent ASV protocol — run 20WBCT, "
        "ventilator and dialysis standby. Species unconfirmed — "
        "prepare for all scenarios. ASV: IV only, never IM or "
        "local. No absolute contraindications when envenomation "
        "confirmed."
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
        f"(4-question screening — not a diagnosis)\n"
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

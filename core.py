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

FIRST_AID = {
    "Indian Cobra": (
        "⚠️ PROBABLE: INDIAN COBRA\n\n"
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
        "🏥 GO TO HOSPITAL IMMEDIATELY\n\n"
        "This is a guide only. All patients receive "
        "polyvalent antivenom regardless of species. "
        "Doctors confirm all treatment on arrival."
    ),
    "Common Krait": (
        "⚠️ PROBABLE: COMMON KRAIT\n\n"
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
        "🏥 GO TO HOSPITAL IMMEDIATELY\n\n"
        "This is a guide only. All patients receive "
        "polyvalent antivenom regardless of species. "
        "Doctors confirm all treatment on arrival."
    ),
    "Russell's Viper": (
        "⚠️ PROBABLE: RUSSELL'S VIPER\n\n"
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
        "🏥 GO TO HOSPITAL IMMEDIATELY\n\n"
        "This is a guide only. All patients receive "
        "polyvalent antivenom regardless of species. "
        "Doctors confirm all treatment on arrival."
    ),
    "Saw-Scaled Viper": (
        "⚠️ PROBABLE: SAW-SCALED VIPER\n\n"
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
        "🏥 GO TO HOSPITAL IMMEDIATELY\n\n"
        "This is a guide only. All patients receive "
        "polyvalent antivenom regardless of species. "
        "Doctors confirm all treatment on arrival."
    ),
    "Unknown": (
        "⚠️ SNAKEBITE EMERGENCY — SPECIES UNKNOWN\n\n"
        "COMMON FIRST AID — DO THIS NOW:\n"
        "✅ Stay calm, lie down, keep still\n"
        "✅ Keep bitten limb BELOW heart level\n"
        "✅ Remove rings, watches, tight clothing\n"
        "❌ Do NOT cut the wound\n"
        "❌ Do NOT tie a tourniquet\n"
        "❌ Do NOT suck the venom\n"
        "❌ Do NOT give food, water or alcohol\n\n"
        "The hospital has been alerted and is "
        "preparing for your arrival.\n\n"
        "🏥 GO TO HOSPITAL IMMEDIATELY\n\n"
        "This is a guide only. All patients receive "
        "polyvalent antivenom regardless of species. "
        "Doctors confirm all treatment on arrival."
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
        "Indian Cobra identified. Watch for drooping eyelids, "
        "difficulty swallowing, or breathing difficulty — paralysis "
        "starting. Hospital alerted for ventilator support. "
        "Go to hospital immediately."
    ),
    "Common Krait": (
        "Common Krait identified. Critical warning: this venom works "
        "slowly. The patient may seem fine now but can collapse "
        "suddenly in two to six hours, especially at night. Do not "
        "leave them alone. Hospital alerted for ICU monitoring. "
        "Go to hospital immediately."
    ),
    "Russell's Viper": (
        "Russell's Viper identified. Watch for rapid swelling, blood "
        "in urine, or bleeding from gums. Kidney failure is likely "
        "within hours. Hospital alerted to prepare dialysis and "
        "clotting support. Go to hospital immediately."
    ),
    "Saw-Scaled Viper": (
        "Saw-Scaled Viper identified. Watch for bleeding from the "
        "bite that will not stop. Patient needs blood products "
        "urgently. Hospital alerted. Go to hospital immediately."
    ),
    "Unknown": (
        "Snake species unknown. Hospital alerted and preparing for "
        "your arrival with full snakebite protocol. "
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

def build_hospital_message(snake, patient_contact, channel):
    prep = HOSPITAL_PREP.get(snake, HOSPITAL_PREP["Unknown"])
    return (
        f"AHIVACH EMERGENCY ALERT\n"
        f"Probable: {snake}\n"
        f"Patient: {patient_contact}\n"
        f"Channel: {channel.upper()}\n"
        f"{prep}\n"
        f"Administer polyvalent ASV regardless of species.\n"
        f"— AHIVACH System"
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

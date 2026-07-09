# In-memory stores for the build (ADR-0004, ADR-0013). Production swaps these
# for Postgres/Redis without changing graph logic.

SOP_NOTES: dict[str, str] = {
    "wifi": "The wifi network is 'CoastalBreeze' and the password is 'SunnyDays2024!'.",
    "checkin": "Check-in is at 3pm. Self-checkout with a keypad code sent the day before arrival.",
    "parking": "One parking spot is available in the driveway; street parking is permitted after 6pm.",
}

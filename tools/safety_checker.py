from utils.logger import logger

# Mock interaction rules — in production, replace with a real drug DB API
INTERACTION_RULES = {
    ("warfarin", "aspirin"): "Major bleeding risk: Warfarin + Aspirin",
    ("warfarin", "ibuprofen"): "Major bleeding risk: Warfarin + NSAIDs",
    ("insulin", "metformin"): "Monitor glucose closely: Insulin + Metformin",
    ("meropenem", "valproate"): "Risk of reduced valproate levels: Meropenem + Valproate",
    ("metformin", "contrast"): "Contrast nephropathy risk: hold Metformin before contrast studies",
}


def check_safety(
    medications: list,
    pending_results: list,
) -> list[str]:
    """
    Check for known drug interactions and pending result alerts.
    Returns a list of alert strings.
    Medications can be strings or dicts with a 'name' key.
    """
    alerts = []

    # Normalize medication names to lowercase strings
    med_names = []
    for m in medications:
        if isinstance(m, dict):
            med_names.append(m.get("name", "").lower().strip())
        elif isinstance(m, str):
            med_names.append(m.lower().strip())

    # Check interactions
    for (drug1, drug2), warning in INTERACTION_RULES.items():
        d1_present = any(drug1 in m for m in med_names)
        d2_present = any(drug2 in m for m in med_names)
        if d1_present and d2_present:
            alerts.append(f"DRUG INTERACTION: {warning}")
            logger.warning(f"Safety alert: {warning}")

    # Pending results alert
    if pending_results:
        clean = [r for r in pending_results if r and r != "MISSING"]
        if clean:
            alerts.append(
                f"PENDING RESULTS REQUIRE REVIEW BEFORE DISCHARGE: "
                f"{', '.join(clean)}"
            )

    return alerts

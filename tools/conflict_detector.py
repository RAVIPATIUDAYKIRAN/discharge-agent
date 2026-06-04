from collections import defaultdict


def detect_conflicts(
    field_name: str,
    extracted_results: list[dict],
) -> dict:
    """
    Detect conflicting values for a given field across multiple sources.

    Input:
        extracted_results = [
            {"source": "Admission Note", "value": "DKA"},
            {"source": "Progress Note", "value": "Pyelonephritis"},
        ]

    Returns a conflict dict if values differ, or a no-conflict dict.
    """
    if not extracted_results:
        return {"conflict": False, "field": field_name}

    values = defaultdict(list)

    for item in extracted_results:
        val = item.get("value", "").strip()
        src = item.get("source", "Unknown")
        if val and val.upper() not in ("MISSING", ""):
            values[val].append(src)

    unique_values = list(values.keys())

    if len(unique_values) <= 1:
        return {
            "conflict": False,
            "field": field_name,
            "value": unique_values[0] if unique_values else "MISSING",
        }

    return {
        "conflict": True,
        "field": field_name,
        "conflicting_values": [
            {"value": v, "sources": s}
            for v, s in values.items()
        ],
        "review_required": True,
    }

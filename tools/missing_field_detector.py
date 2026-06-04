REQUIRED_FIELDS = [
    "patient_name",
    "admission_date",
    "discharge_date",
    "principal_diagnosis",
    "discharge_condition",
    "hospital_course",
]


def detect_missing_fields(summary) -> list[str]:
    """
    Check which required fields are absent, empty, or explicitly MISSING
    in the generated discharge summary.
    """
    missing = []

    data = summary.model_dump() if hasattr(summary, "model_dump") else summary

    for field in REQUIRED_FIELDS:
        value = data.get(field)

        if (
            value is None
            or value == ""
            or (isinstance(value, str) and value.upper() in ("MISSING", ""))
            or (isinstance(value, list) and len(value) == 0)
        ):
            missing.append(field)

    return missing

def reconcile_medications(
    admission_meds: list[dict],
    discharge_meds: list[dict],
) -> dict:
    """
    Compare admission vs discharge medications.
    Flags:
      - added: new medications at discharge
      - removed: medications stopped at discharge
      - changed: same drug but different dose
      - undocumented_changes: changes with no documented reason
    """
    result = {
        "added": [],
        "removed": [],
        "changed": [],
        "undocumented_changes": [],
    }

    if not admission_meds and not discharge_meds:
        return result

    # Normalize to lowercase name lookup
    admission_lookup = {
        med.get("name", "").lower().strip(): med
        for med in admission_meds
        if med.get("name")
    }

    discharge_lookup = {
        med.get("name", "").lower().strip(): med
        for med in discharge_meds
        if med.get("name")
    }

    # Added at discharge
    for name, med in discharge_lookup.items():
        if name not in admission_lookup:
            entry = {
                "medication": med.get("name"),
                "change_type": "added",
                "new_dose": med.get("dose", "MISSING"),
                "reason": med.get("reason", "NOT_DOCUMENTED"),
                "review_required": "reason" not in med,
            }
            result["added"].append(entry)
            if "reason" not in med or not med.get("reason"):
                result["undocumented_changes"].append(
                    med.get("name", name)
                )

    # Removed at discharge
    for name, med in admission_lookup.items():
        if name not in discharge_lookup:
            entry = {
                "medication": med.get("name"),
                "change_type": "removed",
                "old_dose": med.get("dose", "MISSING"),
                "reason": "NOT_DOCUMENTED",
                "review_required": True,
            }
            result["removed"].append(entry)
            result["undocumented_changes"].append(
                med.get("name", name)
            )

    # Dose changed
    for name in admission_lookup:
        if name in discharge_lookup:
            adm = admission_lookup[name]
            dis = discharge_lookup[name]

            adm_dose = adm.get("dose", "")
            dis_dose = dis.get("dose", "")

            if adm_dose and dis_dose and adm_dose != dis_dose:
                has_reason = bool(dis.get("reason", "").strip())
                entry = {
                    "medication": adm.get("name"),
                    "change_type": "dose_changed",
                    "old_dose": adm_dose,
                    "new_dose": dis_dose,
                    "reason": dis.get("reason", "NOT_DOCUMENTED"),
                    "review_required": not has_reason,
                }
                result["changed"].append(entry)
                if not has_reason:
                    result["undocumented_changes"].append(
                        adm.get("name", name)
                    )

    return result

from models.discharge_summary import DischargeSummary, MedicationChange, Conflict


def build_summary(state) -> DischargeSummary:
    """
    Assemble a DischargeSummary Pydantic model from the current agent state.
    """
    demographics = state.demographics or {}
    diagnoses = state.diagnoses or {}
    medications = state.medications or {}

    # Build medication changes list
    med_changes = []
    raw_changes = state.medication_changes or {}

    for change_type in ("added", "removed", "changed"):
        for item in raw_changes.get(change_type, []):
            med_changes.append(
                MedicationChange(
                    medication=item.get("medication", "UNKNOWN"),
                    change_type=change_type,
                    old_dose=item.get("old_dose"),
                    new_dose=item.get("new_dose"),
                    reason=item.get("reason", "NOT_DOCUMENTED"),
                    review_required=item.get("review_required", True),
                )
            )

    # Build conflicts list
    conflict_models = []
    for c in state.conflicts:
        if c.get("conflict"):
            vals = [
                v["value"]
                for v in c.get("conflicting_values", [])
            ]
            srcs = [
                s
                for v in c.get("conflicting_values", [])
                for s in v.get("sources", [])
            ]
            conflict_models.append(
                Conflict(
                    field=c.get("field", "unknown"),
                    values=vals,
                    sources=srcs,
                    review_required=True,
                )
            )

    # Discharge medications as flat list of strings
    discharge_meds_raw = medications.get("discharge_medications", [])
    discharge_meds = []
    for m in discharge_meds_raw:
        if isinstance(m, dict):
            name = m.get("name", "")
            dose = m.get("dose", "")
            freq = m.get("frequency", "")
            parts = [p for p in [name, dose, freq] if p and p != "MISSING"]
            discharge_meds.append(" - ".join(parts))
        elif isinstance(m, str):
            discharge_meds.append(m)

    return DischargeSummary(
        patient_name=demographics.get("patient_name"),
        age=demographics.get("age"),
        gender=demographics.get("gender"),
        admission_date=demographics.get("admission_date"),
        discharge_date=demographics.get("discharge_date"),
        principal_diagnosis=diagnoses.get("principal_diagnosis"),
        secondary_diagnoses=diagnoses.get("secondary_diagnoses", []),
        hospital_course=state.hospital_course or None,
        procedures=state.procedures,
        allergies=state.allergies,
        discharge_medications=discharge_meds,
        medication_changes=med_changes,
        follow_up_instructions=state.followups,
        pending_results=state.pending_results,
        discharge_condition=state.discharge_condition or None,
        conflicts=conflict_models,
        missing_fields=state.missing_fields,
        review_flags=[
            str(f) for f in state.review_flags
        ],
    )

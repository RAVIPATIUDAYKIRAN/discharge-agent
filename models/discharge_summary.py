from pydantic import BaseModel
from typing import List, Optional


class MedicationChange(BaseModel):
    medication: str
    change_type: str          # added | removed | dose_changed
    old_dose: Optional[str] = None
    new_dose: Optional[str] = None
    reason: str
    review_required: bool


class Conflict(BaseModel):
    field: str
    values: List[str]
    sources: List[str] = []
    review_required: bool = True


class DischargeSummary(BaseModel):

    patient_name: Optional[str] = None
    age: Optional[str] = None
    gender: Optional[str] = None
    admission_date: Optional[str] = None
    discharge_date: Optional[str] = None

    principal_diagnosis: Optional[str] = None
    secondary_diagnoses: List[str] = []

    hospital_course: Optional[str] = None

    procedures: List[str] = []
    allergies: List[str] = []

    discharge_medications: List[str] = []
    medication_changes: List[MedicationChange] = []

    follow_up_instructions: List[str] = []
    pending_results: List[str] = []

    discharge_condition: Optional[str] = None

    conflicts: List[Conflict] = []
    missing_fields: List[str] = []
    review_flags: List[str] = []

    # Meta
    draft_notice: str = (
        "THIS IS A DRAFT FOR CLINICIAN REVIEW ONLY. "
        "NOT A FINALIZED CLINICAL DOCUMENT."
    )

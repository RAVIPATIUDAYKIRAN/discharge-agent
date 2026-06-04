from pydantic import BaseModel


class ClinicianFeedback(BaseModel):
    field: str
    original_value: str
    corrected_value: str
    reason: str
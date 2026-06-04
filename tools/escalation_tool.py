from utils.constants import REVIEW_REQUIRED


def escalate(issue: str, severity: str = "MEDIUM") -> dict:
    """
    Create a structured escalation flag for clinician review.
    severity: HIGH | MEDIUM | LOW
    """
    return {
        "status": REVIEW_REQUIRED,
        "severity": severity,
        "issue": issue,
    }

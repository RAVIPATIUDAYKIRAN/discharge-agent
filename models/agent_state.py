from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set


@dataclass
class AgentState:
    """Central state object used by the discharge summary agent."""

    # Agent Control
    goal: str = "Generate discharge summary"
    step_count: int = 0
    current_action: str = ""
    last_error: str = ""
    pdf_loaded: bool = False

    # Tracks steps attempted (even if they returned empty)
    # so the planner never retries a failed step indefinitely
    _attempted_steps: Set[str] = field(default_factory=set)

    # Source Data
    raw_text: str = ""
    retrieved_chunks: List[str] = field(default_factory=list)
    vector_store: Optional[Any] = None

    # Clinical Extraction Results
    demographics: Dict = field(default_factory=dict)
    diagnoses: Dict = field(default_factory=dict)
    medications: Dict = field(default_factory=dict)
    medication_changes: Dict = field(default_factory=dict)
    labs: List = field(default_factory=list)
    procedures: List = field(default_factory=list)
    allergies: List = field(default_factory=list)
    followups: List = field(default_factory=list)
    pending_results: List = field(default_factory=list)
    discharge_condition: str = ""
    hospital_course: str = ""

    # Validation
    conflicts: List = field(default_factory=list)
    missing_fields: List[str] = field(default_factory=list)
    safety_alerts: List[str] = field(default_factory=list)
    escalations: List[Dict] = field(default_factory=list)
    review_flags: List = field(default_factory=list)

    # Workflow Flags
    conflicts_checked: bool = False
    reconciliation_done: bool = False
    safety_checked: bool = False
    feedback_processed: bool = False
    feedback_memory: List[Dict] = field(default_factory=list)
    summary_generated: bool = False

    # Evidence Tracking
    source_evidence: Dict = field(default_factory=dict)

    # Observability
    trace: List[Dict] = field(default_factory=list)

    # Final Output
    summary: Optional[Any] = None

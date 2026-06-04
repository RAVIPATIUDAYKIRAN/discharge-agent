from utils.logger import logger


class Planner:
    """
    Determines the next action based on the current agent state.

    Design goals:
    - Never retry failed extraction steps indefinitely
    - Complete all mandatory extraction tasks
    - Load clinician feedback before extraction begins
    - Generate summary only after validation steps finish
    - Return "done" when workflow is complete
    """

    SKIPPABLE_STEPS = {
        "extract_demographics",
        "extract_diagnoses",
        "extract_medications",
        "extract_labs",
        "extract_procedures",
        "extract_followups",
        "extract_hospital_course",
        "extract_discharge_condition",
        "extract_allergies",
    }

    def next_action(self, state) -> str:

        logger.info(
            f"Planner evaluating state at step {state.step_count}"
        )

        # --------------------------------------------------
        # STEP 0: Load PDF
        # --------------------------------------------------
        if not state.pdf_loaded:
            return "load_pdf"

        # --------------------------------------------------
        # STEP 1: Load clinician feedback memory
        # (Part 2 learning loop)
        # --------------------------------------------------
        if not getattr(state, "feedback_processed", False):
            return "learn_from_feedback"

        # Track steps that already failed
        attempted = getattr(
            state,
            "_attempted_steps",
            set()
        )

        def should_skip(
            step_name: str,
            completed: bool
        ) -> bool:
            """
            Skip a step if:
            - already completed
            - already attempted and failed
            """
            return (
                completed
                or step_name in attempted
            )

        # --------------------------------------------------
        # Extraction Phase
        # --------------------------------------------------

        if not should_skip(
            "extract_demographics",
            bool(state.demographics)
        ):
            return "extract_demographics"

        if not should_skip(
            "extract_diagnoses",
            bool(state.diagnoses)
        ):
            return "extract_diagnoses"

        if not should_skip(
            "extract_medications",
            bool(state.medications)
        ):
            return "extract_medications"

        if not should_skip(
            "extract_labs",
            bool(state.labs)
        ):
            return "extract_labs"

        if not should_skip(
            "extract_procedures",
            bool(state.procedures)
        ):
            return "extract_procedures"

        if not should_skip(
            "extract_followups",
            bool(state.followups)
        ):
            return "extract_followups"

        if not should_skip(
            "extract_hospital_course",
            bool(state.hospital_course)
        ):
            return "extract_hospital_course"

        if not should_skip(
            "extract_discharge_condition",
            bool(state.discharge_condition)
        ):
            return "extract_discharge_condition"

        if not should_skip(
            "extract_allergies",
            bool(state.allergies)
        ):
            return "extract_allergies"

        # --------------------------------------------------
        # Validation Phase
        # --------------------------------------------------

        if not state.conflicts_checked:
            return "detect_conflicts"

        if not state.reconciliation_done:
            return "reconcile_medications"

        if not state.safety_checked:
            return "run_safety_checks"

        # --------------------------------------------------
        # Summary Generation
        # --------------------------------------------------

        if not getattr(
            state,
            "summary_generated",
            False
        ):
            return "generate_summary"

        # --------------------------------------------------
        # Workflow Complete
        # --------------------------------------------------

        return "done"
import json
import os

from config import MAX_AGENT_STEPS, SUMMARY_OUTPUT_PATH, OPENAI_API_KEY
from models.agent_state import AgentState
from planner import Planner
from rag.chunker import chunk_text
from rag.vector_store import create_vector_store
from tools.conflict_detector import detect_conflicts
from tools.escalation_tool import escalate
from tools.extractor import extract_section
from tools.feedback_loader import load_feedback
from tools.medication_reconciliation import reconcile_medications
from tools.missing_field_detector import detect_missing_fields
from tools.pdf_loader import load_patient_pdf
from tools.retriever import Retriever
from tools.safety_checker import check_safety
from tools.summary_builder import build_summary
from utils.logger import logger
from utils.retry_handler import execute_with_retry
from utils.trace_manager import TraceManager


class DischargeAgent:

    def __init__(self):
        self._validate_api_key()
        self.state = AgentState()
        self.planner = Planner()
        self.trace = TraceManager()
        self.retriever: Retriever | None = None
        self.all_chunks: list[str] = []

    @staticmethod
    def _validate_api_key():
        """Fail fast with a clear message if API key is not configured."""
        if not OPENAI_API_KEY or OPENAI_API_KEY in (
            "", "your_openai_api_key_here", "sk-..."
        ):
            raise EnvironmentError(
                "OPENAI_API_KEY is not set or still has the placeholder value.\n"
                "Fix: open your .env file and set OPENAI_API_KEY=sk-<your-real-key>"
            )

    # ------------------------------------------------------------------
    # PDF Loading
    # ------------------------------------------------------------------

    def load_pdf(self, pdf_path: str):
        logger.info(f"Loading PDF: {pdf_path}")

        text = execute_with_retry(load_patient_pdf, pdf_path)

        if not text or not text.strip():
            raise ValueError(f"No text extracted from: {pdf_path}")

        self.state.raw_text = text
        logger.info(f"TEXT LENGTH = {len(text)}")

        self.all_chunks = chunk_text(text)
        logger.info(f"Total chunks: {len(self.all_chunks)}")

        vector_store = create_vector_store(self.all_chunks)
        self.state.vector_store = vector_store

        self.retriever = Retriever(
            vector_store=vector_store,
            all_chunks=self.all_chunks,
        )
        self.state.pdf_loaded = True
        logger.info("PDF loaded and indexed.")

    # ------------------------------------------------------------------
    # Smart retrieval
    # ------------------------------------------------------------------

    def _retrieve(self, query: str, k_extra: int = 3) -> list[str]:
        targeted = []
        if self.retriever:
            targeted = self.retriever.retrieve(query)

        header_chunks = self.all_chunks[:k_extra]

        seen = set()
        combined = []
        for c in (header_chunks + targeted):
            if c not in seen:
                seen.add(c)
                combined.append(c)
        return combined

    # ------------------------------------------------------------------
    # Extraction steps
    # ------------------------------------------------------------------

    def extract_demographics(self):
        chunks = self._retrieve(
            "patient name age gender admission date discharge date "
            "date of admission nursing assessment case record",
            k_extra=5
        )
        result = extract_section("demographics", chunks)
        if result:
            self.state.demographics = result
            logger.info(f"Demographics: {result}")

    def extract_diagnoses(self):
        chunks = self._retrieve(
            "diagnosis assessment impression final diagnosis provisional "
            "DKA diabetic ketoacidosis pyelonephritis AFI T2DM uncontrolled "
            "cholelithiasis synovitis drug chart ER observation",
            k_extra=4
        )
        result = extract_section("diagnoses", chunks)
        if result:
            self.state.diagnoses = result
            logger.info(f"Diagnoses: {result}")

    def extract_medications(self):
        chunks = self._retrieve(
            "medications drug chart prescription admission medications "
            "discharge medications advice on discharge insulin meropenem "
            "pantoprazole lantus actrapid dolo emeset raciper oflox",
            k_extra=3
        )
        result = extract_section("medications", chunks)
        if result:
            self.state.medications = result

    def extract_labs(self):
        chunks = self._retrieve(
            "laboratory lab results blood CBC creatinine sodium potassium "
            "blood sugar glucose ketones CRP ABG haematology biochemistry "
            "pending culture sensitivity widal",
            k_extra=2
        )
        result = extract_section("labs", chunks)
        if result:
            self.state.labs = result.get("abnormal_labs", [])
            self.state.pending_results = result.get("pending_results", [])

    def extract_procedures(self):
        chunks = self._retrieve(
            "procedure imaging CT KUB USG abdomen pelvis ECG echo "
            "IV cannulation foley catheter blood culture urine culture "
            "procedure chart ABG arterial blood gas oxygen",
            k_extra=3
        )
        result = extract_section("procedures", chunks)
        if result:
            self.state.procedures = result.get("procedures", [])

    def extract_followups(self):
        chunks = self._retrieve(
            "follow up discharge instructions advice review OPD "
            "diet counselling urine culture report awaited",
            k_extra=2
        )
        result = extract_section("followups", chunks)
        if result:
            self.state.followups = result.get("followups", [])

    def extract_hospital_course(self):
        mid = len(self.all_chunks) // 2
        mid_chunks = self.all_chunks[mid - 3: mid + 3]
        targeted = self._retrieve(
            "hospital course treatment admitted ward ICU HDU management "
            "plan clinical progress fever DKA diabetes pyelonephritis "
            "meropenem insulin IV fluids CT KUB echo blood sugar",
            k_extra=4
        )
        combined = list({c: None for c in (mid_chunks + targeted)}.keys())
        result = extract_section("hospital_course", combined)
        if result:
            self.state.hospital_course = result.get("hospital_course", "")

    def extract_discharge_condition(self):
        chunks = self._retrieve(
            "condition at discharge hemodynamically stable improved "
            "discharge condition status advice discharge",
            k_extra=2
        )
        result = extract_section("discharge_condition", chunks)
        if result:
            self.state.discharge_condition = result.get(
                "discharge_condition", ""
            )

    def extract_allergies(self):
        chunks = self._retrieve(
            "allergy drug allergy known allergies not known no allergy",
            k_extra=3
        )
        result = extract_section("allergies", chunks)
        if result:
            self.state.allergies = result.get("allergies", [])

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def run_conflict_detection(self):
        diagnoses = self.state.diagnoses

        if not diagnoses:
            self.state.conflicts_checked = True
            return

        principal = diagnoses.get("principal_diagnosis", "")
        secondary = diagnoses.get("secondary_diagnoses", [])
        sources = diagnoses.get("diagnosis_sources", [])

        if principal == "CONFLICT_DETECTED":
            conflict = {
                "conflict": True,
                "field": "principal_diagnosis",
                "conflicting_values": [
                    {
                        "value": s.get("diagnosis", ""),
                        "sources": [s.get("source", "")]
                    }
                    for s in sources
                ] if sources else [
                    {"value": d, "sources": ["Multiple notes"]}
                    for d in secondary
                ],
                "review_required": True,
            }
            self.state.conflicts.append(conflict)
            self.state.review_flags.append(
                "⚠ DIAGNOSIS CONFLICT: Multiple source notes disagree on "
                "principal diagnosis. Clinician MUST resolve. "
                f"Found: {', '.join(secondary)}"
            )

        elif len(secondary) > 1:
            competing = [
                d for d in secondary
                if any(kw in d.upper() for kw in [
                    "DKA", "PYELONEPHRITIS", "AFI", "T2DM",
                    "KETOACIDOSIS", "FEBRILE", "DIABETES"
                ])
            ]
            if len(competing) > 1:
                conflict = detect_conflicts(
                    "principal_diagnosis",
                    [{"source": "Notes", "value": d} for d in competing]
                )
                if conflict.get("conflict"):
                    self.state.conflicts.append(conflict)
                    self.state.review_flags.append(
                        "⚠ POTENTIAL DIAGNOSIS CONFLICT: Competing acute "
                        f"diagnoses found: {', '.join(competing)}. "
                        "Clinician review required."
                    )

        self.state.conflicts_checked = True

    def reconcile_medications(self):
        meds = self.state.medications or {}
        result = reconcile_medications(
            admission_meds=meds.get("admission_medications", []),
            discharge_meds=meds.get("discharge_medications", []),
        )
        self.state.medication_changes = result

        if result.get("undocumented_changes"):
            names = ", ".join(str(x) for x in result["undocumented_changes"])
            self.state.review_flags.append(
                f"⚠ MEDICATION RECONCILIATION: Undocumented changes for: "
                f"{names}. Reasons must be documented before finalising."
            )
        self.state.reconciliation_done = True

    def run_safety_checks(self):
        meds = self.state.medications or {}
        discharge_meds = meds.get("discharge_medications", [])
        alerts = check_safety(
            medications=discharge_meds,
            pending_results=self.state.pending_results,
        )
        self.state.safety_alerts = alerts
        for alert in alerts:
            self.state.review_flags.append(f"⚠ SAFETY: {alert}")
        self.state.safety_checked = True




    # ------------------------------------------------------------------
    # Part 2 Learning
    # ------------------------------------------------------------------

    def learn_from_feedback(self):

        feedback = load_feedback()

        self.state.feedback_memory = feedback

        self.state.feedback_processed = True

        logger.info(
            f"Loaded {len(feedback)} clinician corrections."
        )

    # ------------------------------------------------------------------
    # Summary Generation
    # ------------------------------------------------------------------

    def generate_summary(self):
        temp_summary = build_summary(self.state)
        self.state.missing_fields = detect_missing_fields(temp_summary)

        for conflict in self.state.conflicts:
            if conflict.get("conflict"):
                esc = escalate(
                    issue=f"Conflict in: {conflict.get('field', 'unknown')}",
                    severity="HIGH",
                )
                self.state.review_flags.append(
                    f"[ESCALATE-HIGH] {esc['issue']}"
                )

        if self.state.missing_fields:
            esc = escalate(
                issue=f"Missing required fields: "
                      f"{', '.join(self.state.missing_fields)}",
                severity="MEDIUM",
            )
            self.state.review_flags.append(
                f"[ESCALATE-MEDIUM] {esc['issue']}"
            )

        self.state.summary = build_summary(self.state)
        self.state.summary.missing_fields = self.state.missing_fields
        self.state.summary.review_flags = [
            str(f) for f in self.state.review_flags
        ]
        self.state.summary_generated = True

        os.makedirs("outputs", exist_ok=True)
        with open(SUMMARY_OUTPUT_PATH, "w", encoding="utf-8") as f:
            json.dump(
                self.state.summary.model_dump(),
                f, indent=4, ensure_ascii=False
            )
        logger.info(f"Summary saved → {SUMMARY_OUTPUT_PATH}")

    # ------------------------------------------------------------------
    # Action Dispatcher
    # ------------------------------------------------------------------

    def execute_action(self, action: str, pdf_path: str):
        action_map = {
            "load_pdf":
                lambda: self.load_pdf(pdf_path),
            "learn_from_feedback":
                self.learn_from_feedback,
            "extract_demographics":
                self.extract_demographics,
            "extract_diagnoses":
                self.extract_diagnoses,
            "extract_medications":
                self.extract_medications,
            "extract_labs":
                self.extract_labs,
            "extract_procedures":
                self.extract_procedures,
            "extract_followups":
                self.extract_followups,
            "extract_hospital_course":
                self.extract_hospital_course,
            "extract_discharge_condition":
                self.extract_discharge_condition,
            "extract_allergies":
                self.extract_allergies,
            "detect_conflicts":
                self.run_conflict_detection,
            "reconcile_medications":
                self.reconcile_medications,
            "run_safety_checks":
                self.run_safety_checks,
        }

        if action not in action_map:
            raise ValueError(f"Unknown action: {action}")

        action_map[action]()

    # ------------------------------------------------------------------
    # Main Agent Loop
    # ------------------------------------------------------------------

    def run(self, pdf_path: str) -> dict:

        logger.info(
            f"=== Agent START | Goal: {self.state.goal} | PDF: {pdf_path} ==="
        )

        while self.state.step_count < MAX_AGENT_STEPS:

            action = self.planner.next_action(self.state)
            logger.info(f"[Step {self.state.step_count}] Action → {action}")

            self.trace.add_step(
                step=self.state.step_count,
                reasoning="Planner evaluated state and selected action",
                tool=action,
                input_data=f"pdf={pdf_path}",
                result="executing...",
                next_decision="continue",
            )
            self.state.trace.append(
                {"step": self.state.step_count, "action": action}
            )

            if action == "generate_summary":

                self.generate_summary()

                self.trace.steps[-1]["result"] = (
                    "summary generated"
                )

                self.trace.steps[-1]["next_decision"] = (
                    "continue"
                )

                self.state.step_count += 1

                continue


            if action == "done":

                self.trace.steps[-1]["result"] = (
                    "workflow complete"
                )

                self.trace.steps[-1]["next_decision"] = (
                    "stop"
                )

                break

            try:
                self.execute_action(action, pdf_path)
                self.trace.steps[-1]["result"] = "success"

            except Exception as e:
                logger.exception(
                    f"Action '{action}' failed at step "
                    f"{self.state.step_count}: {e}"
                )
                self.state.last_error = str(e)
                self.state.review_flags.append(
                    f"[ESCALATE-HIGH] Step '{action}' failed: {e}"
                )
                self.trace.steps[-1]["result"] = f"ERROR: {e}"

            finally:
                # ✅ KEY FIX: always mark step as attempted so planner moves on
                self.state._attempted_steps.add(action)

            self.state.step_count += 1

        self.trace.save()

        if self.state.summary:
            logger.info("=== Agent DONE ===")
            return self.state.summary.model_dump()

        logger.warning("Agent exited without generating summary.")
        return {
            "status": "incomplete",
            "error": self.state.last_error or "Max steps reached",
            "trace": self.state.trace,
        }

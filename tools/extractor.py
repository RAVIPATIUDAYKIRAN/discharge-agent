from utils.llm_client import call_llm
from utils.prompts import SYSTEM_PROMPT
from utils.logger import logger
from tools.feedback_loader import load_feedback


SECTION_PROMPTS = {

    "demographics": """
Extract patient demographics from the clinical notes below.

Return ONLY a JSON object:
{
  "patient_name": "string or MISSING",
  "age": "string or MISSING",
  "gender": "string or MISSING",
  "patient_id": "string or MISSING",
  "admission_date": "DD/MM/YYYY or MISSING",
  "discharge_date": "DD/MM/YYYY or MISSING"
}

INSTRUCTIONS:
- Look for dates in nursing documentation headers, case records, monitoring charts
- Admission date appears as "Date of Admission" or the earliest date in nursing notes
- Discharge date appears as the last consultation date or discharge checklist date
- Use MISSING only if truly absent after searching all notes
- Do NOT invent any value

Source notes:
""",

    "diagnoses": """
Extract ALL diagnoses from every document in the clinical notes below.

Return ONLY a JSON object:
{
  "principal_diagnosis": "CONFLICT_DETECTED if multiple notes disagree, else single diagnosis string, else MISSING",
  "secondary_diagnoses": ["complete list of ALL diagnoses found across ALL notes"],
  "diagnosis_sources": [
    {"source": "document name or date", "diagnosis": "diagnosis found in that document"}
  ],
  "evidence": ["direct quotes from notes"]
}

CRITICAL RULES:
- Search EVERY document: ER chart, drug chart, case record, consultation sheets, ICU chart
- If ANY two documents state different principal diagnoses → set principal_diagnosis to "CONFLICT_DETECTED"
- List ALL diagnoses found (DKA, T2DM, AFI, Pyelonephritis, Cholelithiasis, Synovitis, etc.)
- NEVER pick one diagnosis over another
- Common abbreviations: DKA=Diabetic Ketoacidosis, AFI=Acute Febrile Illness, T2DM=Type 2 Diabetes Mellitus

Source notes:
""",

    "medications": """
Extract all medications from the clinical notes below.

Return ONLY a JSON object:
{
  "admission_medications": [
    {"name": "drug name", "dose": "dose or MISSING", "route": "route or MISSING", "frequency": "freq or MISSING"}
  ],
  "discharge_medications": [
    {"name": "drug name", "dose": "dose or MISSING", "route": "route or MISSING", "frequency": "freq or MISSING", "duration": "duration or MISSING"}
  ],
  "evidence": ["supporting quotes"]
}

INSTRUCTIONS:
- Extract ONLY medications explicitly documented in source notes.
- Admission medications are drugs administered during hospital stay.
- Discharge medications are drugs listed under discharge advice.
- Do NOT infer medications.
- Do NOT use examples.
- Use MISSING when information is absent.

Source notes:
""",

    "labs": """
Extract laboratory results from the clinical notes below.

Return ONLY a JSON object:
{
  "abnormal_labs": [
    {"test": "name", "value": "value", "unit": "unit or MISSING", "flag": "high/low/abnormal", "date": "date or MISSING"}
  ],
  "pending_results": ["list of tests sent but results not yet received at discharge"],
  "evidence": ["supporting quotes"]
}

INSTRUCTIONS:
- Extract abnormal laboratory values explicitly present in notes.
- Extract pending investigations.
- Do NOT infer results.
- Do NOT use example values.
- Include supporting evidence.

Source notes:
""",

    "procedures": """
Extract ALL procedures and investigations performed during hospitalisation.

Return ONLY a JSON object:
{
  "procedures": ["complete list"],
  "evidence": ["supporting quotes"]
}

Look for ALL of these in the notes:
- IV Cannulation (date, gauge)
- Foley's Catheterisation
- CT KUB (Plain)
- USG Abdomen and Pelvis
- 2D Echo / Trans-Thoracic Echo
- ECG
- Blood Culture and Sensitivity
- Urine Culture and Sensitivity
- ABG (Arterial Blood Gas)
- Oxygen therapy

Source notes:
""",

    "followups": """
Extract discharge advice and follow-up instructions.

Return ONLY a JSON object:
{
  "followups": ["complete list of instructions"],
  "evidence": ["supporting quotes"]
}

Look for sections labelled: "Advice on Discharge", "Follow-up Instructions", 
"Review", "OPD", diet advice, pending reports to collect.

Source notes:
""",

"hospital_course": """
Generate a hospital course using ONLY evidence present in the source notes.

Return ONLY a JSON object:
{
  "hospital_course": "concise summary"
}

RULES:
- Use ONLY facts explicitly documented in the notes.
- Do NOT invent chronology.
- Do NOT infer diagnoses.
- Do NOT merge information from different patients.
- If multiple conflicting patient narratives are detected,
  return:
  "REVIEW_REQUIRED_MULTIPLE_PATIENTS"
- If insufficient evidence exists:
  return "MISSING"

Source notes:
""",

    "discharge_condition": """
Extract the patient's condition at discharge.

Return ONLY a JSON object:
{
  "discharge_condition": "string or MISSING"
}

Look for: "Condition at Discharge", "hemodynamically stable", "stable", "improved", discharge status.

Source notes:
""",

    "allergies": """
Extract documented allergies from the clinical notes.

Return ONLY a JSON object:
{
  "allergies": ["list — use ['Not Known'] if explicitly documented as not known"]
}

Look in: nursing notes header "Known Drug Allergies", case record allergy history, drug charts.
Do NOT invent allergies.

Source notes:
""",
}


def build_feedback_context() -> str:
    """
    Load recent clinician feedback and convert it into prompt guidance.
    """

    feedback = load_feedback()

    if not feedback:
        return ""

    recent_feedback = feedback[-10:]

    feedback_lines = []

    for item in recent_feedback:
        field = item.get("field", "unknown")
        corrected = item.get("corrected_value", "")
        reason = item.get("reason", "")

        feedback_lines.append(
            f"- Field: {field} | Correction: {corrected} | Reason: {reason}"
        )

    return (
        "PREVIOUS CLINICIAN FEEDBACK:\n"
        "Use this feedback to improve extraction accuracy.\n"
        "Do NOT override source evidence.\n"
        "Do NOT invent facts.\n\n"
        + "\n".join(feedback_lines)
        + "\n\n"
    )


def extract_section(section_name: str, chunks: list[str]) -> dict:
    """
    Use the LLM to extract a specific clinical section from retrieved chunks.
    Returns a dict. On failure returns empty dict — never raises.
    """
    if not chunks:
        logger.warning(f"No chunks for section: {section_name}")
        return {}

    prompt_prefix = SECTION_PROMPTS.get(
        section_name,
        f"Extract information for: {section_name}\n"
        f"Return ONLY valid JSON. Use 'MISSING' for absent fields.\n\nSource notes:\n"
    )

    # Use up to 10 chunks but cap total context
    context_chunks = chunks[:10]
    context = "\n\n---\n\n".join(context_chunks)

    # Hard cap at ~6000 chars to stay within token limits
    if len(context) > 6000:
        context = context[:6000] + "\n...[truncated]"

    feedback_context = build_feedback_context()

    full_prompt = (
        feedback_context
        + prompt_prefix
        + "\n"
        + context
    ) 

    result = call_llm(
        system_prompt=SYSTEM_PROMPT,
        user_prompt=full_prompt,
        expect_json=True,
    )

    if isinstance(result, dict) and "error" in result:
        logger.error(f"Extraction failed for {section_name}: {result['error']}")
        return {}

    logger.info(f"Section '{section_name}' extracted OK.")
    return result

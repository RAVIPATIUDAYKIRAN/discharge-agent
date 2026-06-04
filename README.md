# Discharge Summary Agent

An agentic AI system that reads patient source-note PDFs (including **scanned/handwritten** records) and produces a structured, clinically safe discharge summary draft for clinician review.

---

## Project Structure

```
discharge-agent/
├── app.py                  # FastAPI application
├── agent.py                # Agent loop (planning, execution, tracing)
├── planner.py              # Dynamic action planner
├── config.py               # Central configuration (env vars)
│
├── models/
│   ├── agent_state.py      # Agent state dataclass
│   └── discharge_summary.py# Pydantic output models
│
├── rag/
│   ├── chunker.py          # Text splitting
│   └── vector_store.py     # FAISS vector store
│
├── tools/
│   ├── pdf_loader.py       # Smart loader: text extraction + OCR fallback
│   ├── pdf_reader.py       # PyMuPDF digital text extraction
│   ├── ocr_tool.py         # pytesseract OCR for scanned PDFs
│   ├── retriever.py        # FAISS retriever with fallback
│   ├── extractor.py        # LLM-based section extraction
│   ├── conflict_detector.py
│   ├── medication_reconciliation.py
│   ├── safety_checker.py   # Drug interaction checker (mocked)
│   ├── escalation_tool.py
│   ├── missing_field_detector.py
│   └── summary_builder.py
│
├── utils/
│   ├── constants.py
│   ├── llm_client.py       # OpenAI wrapper with JSON parsing
│   ├── logger.py
│   ├── prompts.py          # Clinical system prompt
│   ├── retry_handler.py    # tenacity retry decorator
│   └── trace_manager.py
│
├── data/                   # Place patient PDFs here
├── outputs/                # Generated summary.json, trace.json, agent.log
├── .env.example
└── requirements.txt
```

---

## Setup

```bash
# 1. Install system dependencies (Ubuntu/Debian)
sudo apt-get install -y tesseract-ocr poppler-utils

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate

# 3. Install Python packages
pip install -r requirements.txt

# 4. Configure API key
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...

# 5. Place your patient PDF
cp /path/to/patient.pdf data/patient2.pdf
```

---

## Running

```bash
uvicorn app:app --reload
```

Open **http://127.0.0.1:8000/docs** in your browser.

### API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| POST | `/generate-summary` | Upload PDF and generate summary |
| POST | `/generate-summary/default` | Run on `data/patient2.pdf` |
| GET | `/last-summary` | Retrieve last generated summary |
| GET | `/last-trace` | Retrieve last agent trace |

---

## Key Design Decisions

### 1. No Fabrication Guardrail
- The LLM system prompt forbids inventing clinical facts
- Missing values are always `"MISSING"` — never plausible guesses
- Conflicting values are always `"CONFLICT_DETECTED"` — never resolved silently

### 2. Real Agent Loop
- `Planner` evaluates state at each step and selects the next action
- Re-planning happens naturally: if an extraction fails, it's retried; if a required section is empty, the planner loops back
- Hard `MAX_AGENT_STEPS` cap prevents infinite loops

### 3. Scanned PDF Support
- `pdf_loader.py` tries PyMuPDF first (fast, digital PDFs)
- Automatically falls back to pytesseract OCR for scanned/handwritten records

### 4. Conflict Detection
- All extracted diagnoses are listed — none are chosen over others
- When notes disagree, `CONFLICT_DETECTED` is returned and flagged for clinician review

### 5. Medication Reconciliation
- Admission vs discharge meds are compared explicitly
- Added, removed, and dose-changed medications are all surfaced
- Any change without a documented reason is flagged as `NOT_DOCUMENTED`

### 6. Observability
- Every step is logged to `outputs/agent.log`
- Full trace saved to `outputs/trace.json`
- Summary saved to `outputs/summary.json`

---

## Limitations

- Drug interaction checker is **mocked** — production would use a real clinical drug DB (e.g. RxNorm, DrugBank)
- OCR quality depends on scan resolution and handwriting legibility
- LLM extraction accuracy depends on model quality and note structure
- No real-time clinician review integration (by design — output is always a draft)

---

## What I Would Do With More Time

- Add Part 2: simulated reviewer + learning loop (contextual bandit or DPO)
- Replace mocked drug interaction checker with real API
- Add structured logging with Langfuse for production observability
- Add a simple HTML frontend for non-technical clinical staff
- Fine-tune extraction prompts on domain-specific data

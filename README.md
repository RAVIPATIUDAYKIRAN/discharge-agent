# discharge-agent


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
│   └──feedback.py          # feedback access
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
    ├── feedback_loader.py
    ├── feedback_store.py
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
| POST | `/feedback`  |   Retrieve the stored doctor edits  |
| GET | `/last-summary` | Retrieve last generated summary |
| GET | `/last-trace` | Retrieve last agent trace |

---

Part 2 – Learning From Clinician Feedback

1. Agent generates discharge summary.
2. Clinician reviews and submits corrections.
3. Corrections stored in feedback memory.
4. Future agent runs incorporate previous corrections.
5. Improvement metrics are tracked across iterations.

This simulates a human-in-the-loop learning system without requiring expensive RLHF training.

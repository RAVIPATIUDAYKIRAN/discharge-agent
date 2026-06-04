import os
import shutil
import json
import traceback

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from models.feedback import ClinicianFeedback
from tools.feedback_store import save_feedback
from utils.logger import logger

app = FastAPI(
    title="Discharge Summary Agent",
    description=(
        "Agentic AI system that reads patient source-note PDFs and produces "
        "a structured, clinically safe discharge summary draft for clinician review."
    ),
    version="1.0.0",
)

DATA_DIR = "data"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs("outputs", exist_ok=True)


@app.get("/", summary="Health check")
def root():
    from config import OPENAI_API_KEY
    key_ok = bool(OPENAI_API_KEY) and OPENAI_API_KEY not in (
        "", "your_openai_api_key_here", "sk-..."
    )
    return {
        "status": "running",
        "api_key_configured": key_ok,
        "message": (
            "Discharge Summary Agent is live. "
            "POST to /generate-summary with a PDF file."
            if key_ok else
            "⚠ WARNING: OPENAI_API_KEY is not configured. "
            "Edit your .env file and set OPENAI_API_KEY=sk-<your-real-key>"
        ),
    }


@app.post(
    "/generate-summary",
    summary="Generate discharge summary from uploaded PDF",
)
async def generate_summary(
    file: UploadFile = File(
        ...,
        description="Patient source-note PDF (scanned or digital)"
    )
):
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are accepted."
        )

    save_path = os.path.join(DATA_DIR, file.filename)
    try:
        with open(save_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        logger.info(f"Uploaded file saved: {save_path}")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save uploaded file: {e}"
        )

    try:
        from agent import DischargeAgent
        agent = DischargeAgent()
        summary = agent.run(save_path)
        return JSONResponse(
            content={
                "status": "success",
                "file": file.filename,
                "summary": summary,
            }
        )

    except EnvironmentError as e:
        # API key not configured — clear actionable message
        raise HTTPException(status_code=500, detail=str(e))

    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))

    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Agent run failed:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@app.post(
    "/generate-summary/default",
    summary="Run agent on data/patient2.pdf (no upload needed)",
)
def generate_summary_default():
    pdf_path = os.path.join(DATA_DIR, "patient2.pdf")

    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404,
            detail=(
                f"Default PDF not found at {pdf_path}. "
                "Copy your PDF to data/patient2.pdf or use "
                "the /generate-summary upload endpoint."
            ),
        )

    try:
        from agent import DischargeAgent
        agent = DischargeAgent()
        summary = agent.run(pdf_path)
        return JSONResponse(
            content={"status": "success", "summary": summary}
        )

    except EnvironmentError as e:
        raise HTTPException(status_code=500, detail=str(e))

    except Exception as e:
        logger.error(f"Agent run failed:\n{traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Agent error: {str(e)}"
        )


@app.get("/last-summary", summary="Retrieve the last generated summary")
def get_last_summary():
    path = "outputs/summary.json"
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="No summary generated yet."
        )
    with open(path, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))



@app.post("/feedback")
def submit_feedback(
    feedback: ClinicianFeedback
):
    save_feedback(
        feedback.dict()
    )

    return {
        "status": "stored"
    }


@app.get("/last-trace", summary="Retrieve the last agent trace")
def get_last_trace():
    path = "outputs/trace.json"
    if not os.path.exists(path):
        raise HTTPException(
            status_code=404,
            detail="No trace generated yet."
        )
    with open(path, "r", encoding="utf-8") as f:
        return JSONResponse(content=json.load(f))

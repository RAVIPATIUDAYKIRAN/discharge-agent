import os
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o")

MAX_AGENT_STEPS = int(os.getenv("MAX_AGENT_STEPS", 15))

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", 1200))

CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", 200))

TOP_K = int(os.getenv("TOP_K", 6))

SUMMARY_OUTPUT_PATH = "outputs/summary.json"

TRACE_OUTPUT_PATH = "outputs/trace.json"

LOG_FILE_PATH = "outputs/agent.log"

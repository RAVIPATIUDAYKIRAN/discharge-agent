import json
import os

from config import TRACE_OUTPUT_PATH
from utils.logger import logger


class TraceManager:

    def __init__(self):
        self.steps = []

    def add_step(
        self,
        step: int,
        reasoning: str,
        tool: str,
        input_data: str,
        result: str,
        next_decision: str,
    ):
        self.steps.append(
            {
                "step": step,
                "reasoning": reasoning,
                "tool": tool,
                "input": input_data,
                "result": result,
                "next_decision": next_decision,
            }
        )

    def save(self):
        try:
            os.makedirs(
                os.path.dirname(TRACE_OUTPUT_PATH),
                exist_ok=True
            )
            with open(
                TRACE_OUTPUT_PATH, "w", encoding="utf-8"
            ) as f:
                json.dump(self.steps, f, indent=4, ensure_ascii=False)
            logger.info(f"Trace saved to {TRACE_OUTPUT_PATH}")
        except Exception as e:
            logger.error(f"Failed to save trace: {e}")

    def to_list(self):
        return self.steps

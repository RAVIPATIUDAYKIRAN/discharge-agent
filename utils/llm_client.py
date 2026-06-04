import json
import re

from openai import OpenAI

from config import OPENAI_API_KEY, MODEL_NAME
from utils.logger import logger


client = OpenAI(api_key=OPENAI_API_KEY)


def call_llm(
    system_prompt: str,
    user_prompt: str,
    expect_json: bool = True
) -> dict | str:
    """
    Call the LLM and return parsed JSON or raw text.
    Returns an error dict on failure — never raises.
    """
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0,
            max_tokens=2000,
        )

        raw = response.choices[0].message.content or ""

        if not expect_json:
            return raw

        # Strip markdown fences if present
        clean = re.sub(
            r"^```(?:json)?\s*|\s*```$",
            "",
            raw.strip()
        )

        return json.loads(clean)

    except json.JSONDecodeError as e:
        logger.error(f"JSON parse error: {e} | raw: {raw[:300]}")
        return {"error": f"JSON parse error: {str(e)}", "raw": raw[:500]}

    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        return {"error": str(e)}

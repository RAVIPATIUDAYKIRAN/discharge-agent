import json
from pathlib import Path

FILE = "data/feedback_memory.json"


def save_feedback(feedback):
    path = Path(FILE)

    if path.exists():
        data = json.loads(path.read_text())
    else:
        data = []

    data.append(feedback)

    path.write_text(
        json.dumps(data, indent=4)
    )
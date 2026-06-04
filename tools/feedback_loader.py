import json


def load_feedback():

    try:
        with open(
            "data/feedback_memory.json",
            "r"
        ) as f:

            return json.load(f)

    except:
        return []
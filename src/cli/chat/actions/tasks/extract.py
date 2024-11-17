import re
import json


from src.schema import TaskMeta


def extract_task_meta(message: str) -> TaskMeta:
    json_match = re.search(r"```json\s*(.*?)\s*```", message, re.DOTALL)
    task_meta = json.loads(json_match.group(1))
    return TaskMeta(**task_meta)


def extract_task_script(message: str) -> str:
    python_match = re.search(r"```python\s*(.*?)\s*```", message, re.DOTALL)
    return python_match.group(1)

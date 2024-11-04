import sys
import os
import json
import importlib

from jsonschema import validate

from .settings import TASKS_DIR
from .schema import TaskMeta, TaskTool
from .web import fetch_text_for_url

TASKS_META_FILE = TASKS_DIR / "index.json"
TOOLS = {
    "web": TaskTool(
        function=fetch_text_for_url,
        name="fetch_text_for_url",
        description="Fetches cleaned text from a webpage",
        input_schema={
            "type": "object",
            "properties": {"url": {"type": "string"}},
            "required": ["url"],
        },
        output_schema={"type": ["string", "null"]},
    ),
}

# Add task directory to Python path
if str(TASKS_DIR) not in sys.path:
    sys.path.append(str(TASKS_DIR))


def run_task(slug: str, input_data: dict) -> dict:
    tasks = load_tasks()
    task = tasks[slug]
    task_entrypoint = load_task_entrypoint(task, tasks)
    return task_entrypoint(input_data)


def load_task_entrypoint(task: TaskMeta, tasks: list[TaskMeta]):
    task_module = importlib.import_module(task.slug)

    def task_entrypoint(input_data: dict) -> dict:
        validate(instance=input_data, schema=task.input_schema)
        dependencies = {}
        for dep_slug in task.depends_on:
            dep_task = tasks[dep_slug]
            dependencies[dep_slug] = load_task_entrypoint(dep_task, tasks)

        output = task_module.run(input_data, dependencies, TOOLS)
        validate(instance=output, schema=task.output_schema)
        return output

    return task_entrypoint


def load_tasks() -> dict[str, TaskMeta]:
    if not TASKS_META_FILE.exists():
        return {}
    with open(TASKS_META_FILE, "r") as f:
        task_index = json.load(f)
        return {slug: TaskMeta(**task_data) for slug, task_data in task_index.items()}


def save_tasks(tasks: dict[str, TaskMeta]):
    os.makedirs(TASKS_DIR, exist_ok=True)
    with open(TASKS_META_FILE, "w") as f:
        return json.dump({slug: t.model_dump() for slug, t in tasks.items()}, f, indent=2)


def save_task(task: TaskMeta, python_script: str):
    tasks = load_tasks()
    tasks[task.slug] = task
    save_tasks(tasks)
    task_script_path = TASKS_DIR / f"{task.slug}.py"
    with open(task_script_path, "w") as f:
        f.write(python_script)


def delete_task(slug: str) -> list[TaskMeta]:
    tasks = load_tasks()
    for task_slug, task in tasks.items():
        if slug in task.depends_on:
            raise ValueError(
                f"Cannot delete task '{slug}' because task '{task_slug}' depends on it"
            )

    del tasks[slug]
    save_tasks(tasks)
    task_script_path = TASKS_DIR / f"{slug}.py"
    os.remove(task_script_path)

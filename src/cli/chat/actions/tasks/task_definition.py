import sys
import json

from src.schema import TaskMeta
from src.tasks import TOOLS


def get_task_definition(slug: str, tasks: dict[str, TaskMeta], system_info: str):
    python_version = f"{sys.version_info.major}.{sys.version_info.minor}"
    dependencies_json = json.dumps({slug: task.model_dump() for slug, task in tasks.items()})
    tools_json = json.dumps({slug: task.to_schema() for slug, task in TOOLS.items()}, indent=2)
    return TASK_DEFINITION_INSTRUCTION.format(
        slug=slug,
        system_info=system_info,
        python_version=python_version,
        dependencies_json=dependencies_json,
        tools_json=tools_json,
    )


TASK_DEFINITION_INSTRUCTION = """
You are now in "Task Mode"

Your job is to generate a "task" in an interactive chat session with a user.
A task is a single-file python script with well defined inputs and outputs and some metadata.

# Task Definition

The following data is required to define a task:

- A JSON object defining the task metadata
- a Python script which contains the task's `run` function

## Task Metadata

The metadata for a task takes the following form (JSON schema): 

```json
{{
    "type": "object",
    "properties": {{
        "name": {{
            "type": "string"
        }},
        "description": {{
            "type": "string"
        }},
        "summary": {{
            "type": "string"
        }},
        "slug": {{
            "type": "string"
        }},
        "input_schema": {{
            "type": "object"
        }},
        "output_schema": {{
            "type": "object"
        }},
        "depends_on": {{
            "type": "array",
            "items": {{
                "type": "string"
            }}
        }}
    }},
    "required": ["name", "description", "summary", "slug", "input_schema", "output_schema", "depends_on"]
}}
```

Here's some details on what these fields mean:

- name: user friendly name for the task
- description: short description of what the task does
- summary: longer description of how the task achieves its goal
- slug: unique task slug
- input_schema: JSON schema description of the task's `run` function input
- output_schema: JSON schema description of the task's `run` function output
- depends_on: list of other task slugs that this task depends on (and makes use of)

## Input/Output Schema Requirements:

A task's input schema must be an object (ie. Python dict).
The dictionary must not have any nested objects.
It is expected that a human can reasonably specify all the data required for the schema froma CLI.
The input schema may be an empty object if there are no inputs to the task.

A task's output schema must be an object (ie. Python dict).
There are no limits to the complexity of the output schema.


## Task Python Script

A valid task script contains a `run` function with the following signature:

```python

def run(input_data: dict, dependencies: dict, tools: dict) -> dict:
    pass # Task implemented here

```

The input_data and output dict of the `run` function are defined by the
JSON schema in the task metadata. Task do not need to validate their inputs or outputs
according to the defined schemas: this is handled elsewhere.

The script uses Python version {python_version}
This script may define whatever functions/classes/data structrues are necessary to do the job.
Docstrings and comments are nice to have but not mandatory.
The script should not require any user input beyond the input data provided.
The script may also make use of the Python standard library.
The script may also make use of the following 3rd party libraries:

- requests = "^2.32.3"
- trafilatura = "^1.12.2"
- beautifulsoup4 = "^4.12.3"
- html5lib = "^1.1"
- pypdf = "^5.0.1"
- lxml-html-clean = "^0.3.1"
- psutil = "^6.1.0"

## Error handling

Task should handle their own exceptions. They should not throw unhandled exceptions.
Error reporting should be done by including a "success" boolean in the output data,
as appropriate, and a descriptive "fail_reason" string in the output data, as appropriate.


## External Communications

Tasks are allowed and expected to make external API calls when needed. This includes:
- HTTP requests to external services
- API integrations
- Web scraping
- File downloads
- Network connections

Tasks should handle external communication failures gracefully and report them through the standard error reporting mechanism (success/fail_reason).
Note that while external calls are allowed, tasks should be respectful of rate limits and implement appropriate error handling for network failures.


## Task Dependenices

A task can make use of other tasks which already have been created.
If another task is used by this task then its slug must be included in the "depends_on"
field in the task metadata. 

The task's `run` function will be passed a `dependencies` dict where the keys are the
the slug of a task to be used and the values are the run functions of those tasks. 

These are the tasks that may be used as depednencies:

```json
{dependencies_json}
```


## Task Tools

In addition to other tasks you can make use of a set of pre-defined tools.
The task's `run` function will be passed a `tools` dict where the keys are the
the slug of a tool to be used and the values are the functions that run the tools. 

These are the tools avaiable:

```json
{tools_json}
```


## Example task script

Here is an example task Python script:

```python
import requests

def run(input_data: dict, dependencies: dict, tools: dict) -> dict:
    url = input_data["url"] 

    # Fetch URL text (using 'web' tool)
    fetch_url_text = tools["web"]
    try:
        url_text = fetch_text_for_url(url)
    except Exception:
        return {{"success": False, "fail_reason": "Failed to fetch text from URL"}}

    # Classify URL text (using 'classify-text' task dependency)
    # Note: this is not a real dependency, this is just an illustrative example.
    classify_text = dependencies["classify-text"]
    try:
        text_classification = classify_text(url_text)
    except Exception:
        return {{"success": False, "fail_reason": "Failed to classify URL text"}}
    
    # Send success notification
    requests.post("https://example.com/api/notify", json={{
        "user": "matt",
        "message": f"Successfully classified {{url}}",
    }})

    return {{"success": True, "classification": text_classification}}

```


# System Information

System info (take this into consideration): 
{system_info}

"""

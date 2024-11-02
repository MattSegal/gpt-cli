# General UX
- saved / resumable chat history
- cost tracking of user queries
- file UX improvements
    - file path completion?
    - file explorer ui?

# Distribution

- pip install
- changelog + publish to pypi


# Search
- index folders / RAG on disk
- openai based text enbeddings
- siglip based image embeddings


# Tasks System

## Core Concepts
- Tasks are self-contained modules that can be dynamically loaded
- Each task has a clear single responsibility
- Tasks can be chained together in workflows
- Tasks can be shared and installed from a repository

## Task Commands
```bash
\task list
\task create
\task delete <name>
\task update  <name>
\task inspect <name>
\task <name> [args]     # Run a specific task
\workflow               # Create/manage task workflows

```

## Task Structure
```
~/.ask/tasks/
├── index.json             # Task registry
├── workflows/             # Saved task workflows
└── installed/            
    ├── web-scraper/      # Example task
    │   ├── manifest.json
    │   ├── entrypoint.py
    │   ├── requirements.txt
    │   └── schemas/
    │       ├── input.json
    │       └── output.json
    └── summarizer/
        └── ...
```

## Task Registry (index.json)
```json
{
    "tasks": [
        {
            "type": "task",
            "name": "Web Scraper",
            "description": "Scrapes content from websites with customizable rules",
            "slug": "web-scraper",
            "requirements": ["requests", "beautifulsoup4"],
            "entrypoint": "entrypoint.py:task_handler",
            "input_schema": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "format": "uri"
                        }
                    },
                    "selectors": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string"},
                            "content": {"type": "string"}
                        },
                        "required": ["content"]
                    }
                },
                "required": ["urls"]
            },
            "output_schema": {
                "type": "object",
                "properties": {
                    "results": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "url": {"type": "string"},
                                "title": {"type": "string"},
                                "content": {"type": "string"},
                                "timestamp": {"type": "string", "format": "date-time"}
                            },
                            "required": ["url", "content"]
                        }
                    }
                },
                "required": ["results"]
            }
        },
        {
            "type": "workflow",
            "name": "News Aggregator",
            "description": "Scrapes news and generates summaries",
            "slug": "web-scraper",

            "steps": [
                {
                    "task": "web-scraper",
                    "config": {
                        "urls": ["..."],
                        "selectors": {"..."}
                    }
                },
                {
                    "task": "summarizer",
                    "config": {
                        "max_length": 200
                    }
                }
            ]
        }
    ]
}
```

## Task Implementation (entrypoint.py)
```python
from typing import Dict, Any
from ask.tasks import TaskResult, TaskContext

def task_handler(context: TaskContext, input_data: Dict[str, Any]) -> TaskResult:
    """
    Main entry point for the task.
    
    Args:
        context: Task execution context (logging, state, etc.)
        input_data: Validated input matching input_schema
        
    Returns:
        TaskResult containing output matching output_schema
    """
    # Task implementation
    pass

def validate() -> bool:
    """Validate task requirements and dependencies"""
    pass

def cleanup() -> None:
    """Clean up any resources"""
    pass
```

## Advanced Features

### Task Context
- Provides logging, state management, and progress tracking
- Access to shared resources and credentials
- Rate limiting and quota management
- Caching layer for intermediate results

### Workflow Engine
- Visual workflow builder in CLI
- Parallel task execution where possible
- Error handling and retry logic
- Conditional branching based on task outputs
- Progress visualization
- Workflow export/import

### Task Repository
- Central repository for sharing tasks
- Version management
- Dependency resolution
- Security scanning
- Rating and review system

### Documentation
- Auto-generated task documentation
- Usage examples and templates
- Input/output schema visualization
- Performance metrics and requirements

### Integration Features
- Event hooks for task lifecycle
- Plugin system for extending functionality
- API endpoints for remote execution
- Export results in multiple formats
- Integration with external tools

This structure provides a robust foundation for:
1. Easy task development and sharing
2. Complex workflow automation
3. Proper error handling and validation
4. Scalability and maintenance
5. Community contribution

Would you like me to elaborate on any particular aspect?


# Tasks

- dynamic user defined tasks (eg summarise, crawl)
- documentation mode (document the steps you took)
- multiple threads

\agent  use all available commands to complete a task
\tasks  list all tasks
\task   execute a particular task with a prompt


task
    - scrape these news websites
    - get articles from each category
    - allow user to see the news (news summary?)


task output

~/.ask/tasks
~/.ask/tasks/index.json
```json
[
    {
        name: "Task Name",
        description: "Task description",
        slug: "task-name" # Unique
        input
    }

]
```

~/.ask/tasks/task-slug/
    entrypoint.py
        def task_handler
    # other files as required
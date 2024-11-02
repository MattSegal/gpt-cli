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
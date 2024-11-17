# General UX

- saved / resumable chat history
- cost tracking of user queries
- file UX improvements
    - file path completion?
    - file explorer ui?

# Command mode

- make it more generic, handling many modes
    - docker exec
    - aws ecs shell
    - ssh
    - commands on local machine
    - psql

# Distribution

- pip install
- changelog + publish to pypi


# Search

- index folders / RAG on disk
- openai based text enbeddings
- siglip based image embeddings


# Tasks

workflow (current)

1) initial task definition
    - task mode prompt
    - define task w/ user feedback
    - one-shot generate script
2) save task
    - save metadata and script to disk
3) run task
    - load and run script's `run` method


workflow (ideal)

1) initial task definition
    - task mode prompt
    - define task w/ user feedback
    - output task metadata inc a new "user_goal" key 
    - save metadata to index.json with "status": "CREATING"
    - save results to README.md
2) incremental script generation
    - generate a script plan defining the incremental units required to make the script work
    - save plan to README.md
    - for each incremental unit
        - write a function for that unit
        - add the function to the main method
        - write a test for that function ()
        - run the script to check for data (eg. html)
        - request data from the user if required (eg. documentation) (save to README.md)
    - once all units are written and tested move to final test and acceptance
3) final test and acceptance
    - run the task end-to end
    - ask the user if it looks good
    - if not go back to step 2


X) save task
X) run taks
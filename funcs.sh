function gpt {
    if [ -z "$GPT_HOME" ]
    then
        echo "GPT_HOME not set"
        exit 1
    fi
    PROMPT="$@"
    $GPT_HOME/venv/bin/python $GPT_HOME/gpt.py "$PROMPT"
}

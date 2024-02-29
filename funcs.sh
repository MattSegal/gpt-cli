function gpt {
    if [ -z "$GPT_HOME" ]
    then
        echo "GPT_HOME not set"
        return
    fi
    GPT_PROMPT="$@"
    if [ -z "$GPT_PROMPT" ] || [ "$1" == "--help" ]
    then
        gpt_help_text
        return
    fi
    $GPT_HOME/venv/bin/python $GPT_HOME/gpt.py "$GPT_PROMPT"
}

function gpt_help_text {
    echo ""
    echo "Ask GPT-4 a question. Usage:"
    echo ""
    echo "  gpt how do I flatten a list in python"
    echo "  gpt ffmpeg convert webm to a gif"
    echo "  gpt what is the best restaurant in melbourne"
    echo ""
}

PEX_PREFIX="as an expert, please explain technical terms and jargon here in precise detail, one by one in a list, assuming a sophisticated audience:"

function pex {
    if [ -z "$GPT_HOME" ]
    then
        echo "GPT_HOME not set"
        return
    fi
    if [ -z `which xclip` ]
    then
        echo "xclip is not installed"
        return
    fi
    CLIPBOARD_TEXT=`xclip -o sel clip`
    if [ -z "$CLIPBOARD_TEXT" ] || [ "$1" == "--help" ]
    then
        pex_help_text
        return
    fi
    GPT_PROMPT="$PEX_PREFIX $CLIPBOARD_TEXT"
    $GPT_HOME/venv/bin/python $GPT_HOME/gpt.py "$GPT_PROMPT"
    # Empty clipboard
    cat /dev/null | xclip -i


}

function pex_help_text {
    echo ""
    echo "Ask GPT-4 to (please) explain the technical terms in the contents of your clipboard."
    echo "Usage:"
    echo ""
    echo "  pex"
    echo ""
    echo "Prompt prefix:"
    echo ""
    echo "  $PEX_PREFIX"
    echo ""
}
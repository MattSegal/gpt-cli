function dalle {
    if [ -z "$GPT_HOME" ]; then
        echo "GPT_HOME not set"
        return
    fi
    DALLE_PROMPT="$@"
    if [ -z "$DALLE_PROMPT" ] || [ "$1" == "--help" ]; then
        dalle_help_text
        return
    fi
    TEMPFILE=$(mktemp)
    $GPT_HOME/venv/bin/python $GPT_HOME/dalle.py $TEMPFILE "$DALLE_PROMPT"
    IMAGE_URL=$(cat $TEMPFILE)
    URL_REGEX='(https?|ftp|file)://[-[:alnum:]\+&@#/%?=~_|!:,.;]*[-[:alnum:]\+&@#/%=~_|]'
    if [[ $IMAGE_URL =~ $URL_REGEX ]]; then
        echo "Opening generated image with $DALLE_IMAGE_OPENER"
        $DALLE_IMAGE_OPENER $IMAGE_URL
    else
        echo "$IMAGE_URL"
    fi
}

function dalle_help_text {
    echo ""
    echo "Ask DALL-E-3 to generate an image. Usage:"
    echo ""
    echo "  dalle the best hamburger ever"
    echo "  dalle a skier doing a backflip high quality photorealistic"
    echo "  dalle an oil painting of the best restaurant in melbourne"
    echo ""
}

function gpt {
    if [ -z "$GPT_HOME" ]; then
        echo "GPT_HOME not set"
        return
    fi
    GPT_PROMPT="$@"
    if [ -z "$GPT_PROMPT" ] || [ "$1" == "--help" ]; then
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
    if [ -z "$GPT_HOME" ]; then
        echo "GPT_HOME not set"
        return
    fi
    if [ -z $(which xclip) ]; then
        echo "xclip is not installed"
        return
    fi
    if [ "$1" == "--empty" ]; then
        empty_clipboard
        echo "Clipboard emptied"
        return
    fi
    CLIPBOARD_TEXT=$(xclip -o sel clip)
    if [ "$1" == "--check" ]; then
        echo -e "Clipboard contents:\n\n${CLIPBOARD_TEXT}\n"
        return
    fi
    if [ -z "$CLIPBOARD_TEXT" ] || [ "$1" == "--help" ]; then
        pex_help_text
        return
    fi
    GPT_PROMPT="$PEX_PREFIX $CLIPBOARD_TEXT"
    $GPT_HOME/venv/bin/python $GPT_HOME/gpt.py "$GPT_PROMPT"
    empty_clipboard
}

function empty_clipboard {
    cat /dev/null | xclip -i
}

function pex_help_text {
    echo ""
    echo "Ask GPT-4 to (please) explain the technical terms in the contents of your clipboard."
    echo "Usage:"
    echo ""
    echo "  pex          # Query GPT-4 with clipboard contents"
    echo "  pex --empty  # Empties clipboard"
    echo "  pex --check  # Check contents of clipboard"
    echo "  pex --help   # Print this message"
    echo ""
    echo "Prompt prefix:"
    echo ""
    echo "  $PEX_PREFIX"
    echo ""
}

DIFFCHECK_PREFIX="the following code is a git diff for my codebase, check it for any errors or mistakes"

function diffcheck {
    if [ -z "$GPT_HOME" ]; then
        echo "GPT_HOME not set"
        return
    fi
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        DIFF=$(git diff)
        if [ -z "$DIFF" ] || [ "$1" == "--help" ]; then
            diffcheck_help_text
            return
        fi
        GPT_PROMPT="$DIFFCHECK_PREFIX\n$@\n$DIFF"
        $GPT_HOME/venv/bin/python $GPT_HOME/gpt.py "$GPT_PROMPT"
    else
        echo "Not inside a Git repository"
        diffcheck_help_text
        return
    fi
}

function diffcheck_help_text {
    echo ""
    echo "Ask GPT-4 to check your git diff for errors or mistakes."
    echo "Usage:"
    echo ""
    echo "  diffcheck          # Query GPT-4 with diff"
    echo "  diffcheck --help   # Print this message"
    echo ""
    echo "Prompt prefix:"
    echo ""
    echo "  $DIFFCHECK_PREFIX"
    echo ""
}

COMMITMSG_PREFIX="the following code is a git diff for my codebase, please write a commit message"

function commitmsg {
    if [ -z "$GPT_HOME" ]; then
        echo "GPT_HOME not set"
        return
    fi
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        DIFF=$(git diff)
        if [ -z "$DIFF" ] || [ "$1" == "--help" ]; then
            commitmsg_help_text
            return
        fi
        GPT_PROMPT="$COMMITMSG_PREFIX\n$@\n$DIFF"
        $GPT_HOME/venv/bin/python $GPT_HOME/gpt.py "$GPT_PROMPT"
    else
        echo "Not inside a Git repository"
        commitmsg_help_text
        return
    fi
}

function commitmsg_help_text {
    echo ""
    echo "Ask GPT-4 to write you a commit message."
    echo "Usage:"
    echo ""
    echo "  commitmsg          # Query GPT-4 with diff"
    echo "  commitmsg --help   # Print this message"
    echo ""
    echo "Prompt prefix:"
    echo ""
    echo "  $COMMITMSG_PREFIX"
    echo ""
}

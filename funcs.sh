if [ ! -z "${GPT_HOME}" ]; then
    export PYTHONPATH="${GPT_HOME}:${PYTHONPATH}"
fi


function dalle {
    if [ -z "${GPT_HOME}" ]; then
        echo "GPT_HOME not set"
        return 1
    fi
    DALLE_PROMPT="$*"
    if [ -z "${DALLE_PROMPT}" ] || [ "$1" = "--help" ]; then
        dalle_help_text
        return 0
    fi
    TEMPFILE=$(mktemp)
    "${GPT_HOME}/venv/bin/python" -m gpt image "${TEMPFILE}" "${DALLE_PROMPT}"
    IMAGE_URL=$(cat "${TEMPFILE}")
    rm -f "${TEMPFILE}"
    URL_REGEX='(https?|ftp|file)://[-[:alnum:]\+&@#/%?=~_|!:,.;]*[-[:alnum:]\+&@#/%=~_|]'
    if [[ ${IMAGE_URL} =~ ${URL_REGEX} && -n "${DALLE_IMAGE_OPENER}" ]]; then
        echo "Opening generated image with ${DALLE_IMAGE_OPENER}"
        "${DALLE_IMAGE_OPENER}" "${IMAGE_URL}"
    else
        echo "${IMAGE_URL}"
    fi
}

function dalle_help_text {
    cat << EOF

Ask DALL-E-3 to generate an image. Usage:

  dalle the best hamburger ever
  dalle a skier doing a backflip high quality photorealistic
  dalle an oil painting of the best restaurant in melbourne

EOF
}

function gpt {
    if [ -z "${GPT_HOME}" ]; then
        echo "GPT_HOME not set"
        return 1
    fi
    GPT_PROMPT="$*"
    if [ -z "${GPT_PROMPT}" ] || [ "$1" = "--help" ]; then
        gpt_help_text
        return 0
    fi
    if [[ "${GPT_PROMPT}" == *"--nano"* ]]; then
        TEMPFILE=$(mktemp)
        nano "${TEMPFILE}"
        NANO_TEXT=$(cat "${TEMPFILE}")
        GPT_PROMPT="${GPT_PROMPT}"$'\n'"${NANO_TEXT}"
        GPT_PROMPT=$(echo "${GPT_PROMPT}" | sed 's/--nano//g')
    fi
    "${GPT_HOME}/venv/bin/python" -m gpt chat "${GPT_PROMPT}"
    if [[ "${GPT_PROMPT}" == *"--nano"* ]]; then
        rm -f "${TEMPFILE}"
    fi
}

function gpt_help_text {
    cat << EOF

Ask GPT-4 a question. Usage:

  gpt how do I flatten a list in python
  gpt ffmpeg convert webm to a gif
  gpt what is the best restaurant in melbourne
  echo 'hello world' | gpt what does this text say
  gpt --nano # Incompatible with pipes

EOF
}

alias chat=gpt

PEX_PREFIX="as an expert, please explain technical terms and jargon here in precise detail, one by one in a list, assuming a sophisticated audience:"

function pex {
    if [ -z "${GPT_HOME}" ]; then
        echo "GPT_HOME not set"
        return 1
    fi
    if ! command -v xclip >/dev/null 2>&1; then
        echo "xclip is not installed"
        return 1
    fi
    if [ "$1" = "--empty" ]; then
        empty_clipboard
        echo "Clipboard emptied"
        return 0
    fi
    CLIPBOARD_TEXT=$(xclip -o -selection clipboard)
    if [ "$1" = "--check" ]; then
        printf "Clipboard contents:\n\n%s\n\n" "${CLIPBOARD_TEXT}"
        return 0
    fi
    if [ -z "${CLIPBOARD_TEXT}" ] || [ "$1" = "--help" ]; then
        pex_help_text
        return 0
    fi
    GPT_PROMPT="${PEX_PREFIX} ${CLIPBOARD_TEXT}"
    "${GPT_HOME}/venv/bin/python" -m gpt chat "${GPT_PROMPT}"
    empty_clipboard
}

function empty_clipboard {
    : | xclip -selection clipboard
}

function pex_help_text {
    cat << EOF

Ask GPT-4 to (please) explain the technical terms in the contents of your clipboard.
Usage:

  pex          # Query GPT-4 with clipboard contents
  pex --empty  # Empties clipboard
  pex --check  # Check contents of clipboard
  pex --help   # Print this message

Prompt prefix:

  ${PEX_PREFIX}

EOF
}

DIFFCHECK_PREFIX="the following code is a git diff for my codebase, check it for any errors or mistakes"

function diffcheck {
    if [ -z "${GPT_HOME}" ]; then
        echo "GPT_HOME not set"
        return 1
    fi
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        DIFF=$(git diff)
        if [ -z "${DIFF}" ] || [ "$1" = "--help" ]; then
            diffcheck_help_text
            return 0
        fi
        GPT_PROMPT="${DIFFCHECK_PREFIX}"$'\n'"$*"$'\n'"${DIFF}"
        "${GPT_HOME}/venv/bin/python" -m gpt chat "${GPT_PROMPT}"
    else
        echo "Not inside a Git repository"
        diffcheck_help_text
        return 1
    fi
}

function diffcheck_help_text {
    cat << EOF

Ask GPT-4 to check your git diff for errors or mistakes.
Usage:

  diffcheck          # Query GPT-4 with diff
  diffcheck --help   # Print this message

Prompt prefix:

  ${DIFFCHECK_PREFIX}

EOF
}

COMMITMSG_PREFIX="the following code is a git diff for my codebase, please write a commit message"

function commitmsg {
    if [ -z "${GPT_HOME}" ]; then
        echo "GPT_HOME not set"
        return 1
    fi
    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        DIFF=$(git diff)
        if [ -z "${DIFF}" ] || [ "$1" = "--help" ]; then
            commitmsg_help_text
            return 0
        fi
        GPT_PROMPT="${COMMITMSG_PREFIX}"$'\n'"$*"$'\n'"${DIFF}"
        "${GPT_HOME}/venv/bin/python" -m gpt chat "${GPT_PROMPT}"
    else
        echo "Not inside a Git repository"
        commitmsg_help_text
        return 1
    fi
}

function commitmsg_help_text {
    cat << EOF

Ask GPT-4 to write you a commit message.
Usage:

  commitmsg          # Query GPT-4 with diff
  commitmsg --help   # Print this message

Prompt prefix:

  ${COMMITMSG_PREFIX}

EOF
}

function mrcheck {
    if [ -z "${GPT_HOME}" ]; then
        echo "GPT_HOME not set"
        return 1
    fi
    # if ! command -v glab >/dev/null 2>&1; then
    #     echo "glab is not installed"
    #     DIFF=$(glab mr diff "${BRANCH_NAME}")
    #     return 1
    # fi

    if git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
        BRANCH_NAME=$(git rev-parse --abbrev-ref HEAD)
        echo "Pulling diff from github for branch ${BRANCH_NAME}..."
        DIFF=$(gh pr diff "${BRANCH_NAME}")
        if [ -z "${DIFF}" ] || [ "$1" = "--help" ]; then
            mrcheck_help_text
            return 0
        fi
        read -r -d '' GPT_PROMPT << EOF
Your task is:
- Review the code changes and provide feedback
- Highlight any bugs or gross coding errors
- Highlight any obvious security flaws
- Do not highlight minor issues and nitpicks
- Use bullet points if you have multiple comments

The main goal here is to make sure there aren't any mistakes

$*

You are provided with the code changes (diffs) in a unidiff format. Here are the diffs:

${DIFF}

All code changes have been provided. Please provide me with your code review based on all the changes
EOF

        "${GPT_HOME}/venv/bin/python" -m gpt chat "${GPT_PROMPT}"
    else
        echo "Not inside a Git repository"
        mrcheck_help_text
        return 1
    fi
}

function mrcheck_help_text {
    cat << EOF

Ask GPT-4 to check your mr diff for errors or mistakes.
Usage:

  mrcheck          # Query GPT-4 with mr diff
  mrcheck --help   # Print this message

Prompt prefix:

  ${DIFFCHECK_PREFIX}

EOF
}

function web {
    if [ -z "$1" ] || [ "$1" = "--help" ]; then
        web_help_text
        return 0
    fi
    "${GPT_HOME}/venv/bin/python" -m gpt scrape "$@"
}

function web_help_text {
    cat << EOF

Try to read text from a website.
Usage:

  web http://example.com                      # Read text from example.com
  web http://example.com http://other.com     # Read text from example.com and other.com
  web --help                                  # Print this message

Suggested usage:

  web http://example.com | gpt summarise the contents of this website

EOF
}

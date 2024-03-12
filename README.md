# Teeny Tiny GPT-4 CLI Wrapper

![](./gpt.gif)

# Bash functions provided:

- gpt: Ask GPT-4 a question
- dalle: Ask DALL-E 3 to generate an image
- pex: Explain the technical terms and jargon in the contents of your clipboard (requires xclip)
- diffcheck: Check your git diff for errors or mistakes (requires git)
- commitmsg: Write a commit message for your git diff (requires git)
- mrcheck: Check your gitlab merge request diff for errors or mistakes (requires glab)

[OpenAI Pricing](https://openai.com/pricing):

- GPT-4 Turbo: $10.00 / 1M tokens ~= 0.25c per 1000 input characters
- DALL-E 3: 12c USD / image

[Anthropic Pricing](https://www.anthropic.com/api):

- Opus: $15.00 / 1M tokens
- Sonnet: $3.00 / 1M tokens

## Local setup

Install project requirements:

```bash
python3 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

Setup .bashrc:

```bash
# You must set one of these two keys, Anthropic will be used if both are set
export OPENAI_API_KEY="sk-XXXXXXXX" # OpenAI API key
export ANTHROPIC_API_KEY=sk-XXXXXXXX # Anthropic API key

export DALLE_IMAGE_OPENER="google-chrome" # Executable to open URLs
export GPT_HOME="/home/myname/code/gpt" # Wherever you cloned this project

# Load bash functions
. $GPT_HOME/funcs.sh
```

Reload your terminal and try it out out:

```bash
gpt --help
dalle --help
pex --help  # xclip required
diffcheck --help  # git required
commitmsg --help  # git required
mrcheck --help  # glab required
```

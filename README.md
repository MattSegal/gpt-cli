# Teeny Tiny GPT-4 CLI Wrapper

![](./gpt.gif)

# Functions provided:

- gpt: Ask GPT-4 a question
- pex: Explain the technical terms and jargon in the contents of your clipboard (requires xclip)

## Local setup

```bash
python3 -m venv venv
. ./venv/bin/activate
pip install -r requirements.txt
```

.bashrc:

```bash
export OPENAI_KEY="sk-XXXXXXXX"
export GPT_HOME="/home/myname/code/gpt
. $GPT_HOME/funcs.sh
```

# Ask CLI

```
❯ ask --help

Usage: ask [OPTIONS] COMMAND [ARGS]...

  Ask your language model a question.

  Examples:
    ask how do I flatten a list in python
    ask ffmpeg convert webm to a gif
    ask what is the best restaurant in melbourne
    echo 'hello world' | ask what does this text say
    ask web http://example.com | ask what does this website say

Options:
  --help  Show this message and exit.

Commands:
  <default>  Simple one-off queries with no chat history
  config     Set up or configure this tool
  img        Render an image with Dalle-3
  ui         Chat via a terminal UI
  web        Scrape content from provided URLs (HTML, PDFs)
```

Note: GIF is out of date

![](./gpt.gif)

## Local setup

Install project requirements:

```bash
python -m venv venv
. ./venv/bin/activate
pip install poetry
poetry install
ask --help
ask config
```

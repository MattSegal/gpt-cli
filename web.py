import sys
import os
import json
from io import BytesIO
from functools import cache
from urllib.parse import parse_qs, urlparse

import requests
from bs4 import BeautifulSoup
from trafilatura import extract
from pypdf import PdfReader
import modal

REQUESTS_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
}

MODAL_TOKEN_ID = os.environ.get("MODAL_TOKEN_ID", None)
MODAL_TOKEN_SECRET = os.environ.get("MODAL_TOKEN_SECRET", None)
IS_MODAL_ENABLED = MODAL_TOKEN_ID and MODAL_TOKEN_SECRET
MODAL_APP = "whisper-transcriber"
YOUTUBE_DOMAINS = [
    "youtube.com",
    "www.youtube.com",
    "m.youtube.com",
]


def main(urls: str):
    for url in urls:
        print_url(url)


def print_url(url: str):
    domain = urlparse(url).netloc
    if domain in YOUTUBE_DOMAINS and IS_MODAL_ENABLED:
        transcribe_youtube_video(url)
        return

    resp = requests.get(url, timeout=30, headers=REQUESTS_HEADERS)
    try:
        resp.raise_for_status()
    except (requests.HTTPError, requests.Timeout):
        return

    if resp.headers["content-type"] == "application/pdf":
        buffer = BytesIO(resp.content)
        reader = PdfReader(buffer)
        for page in reader.pages:
            print(page.extract_text())

    else:
        html = resp.text
        cleaned_html = BeautifulSoup(html, "html5lib").prettify()
        contents_raw = extract(cleaned_html, output_format="json")
        contents = json.loads(contents_raw)
        print(contents["text"])


def transcribe_youtube_video(url: str) -> dict:
    qs = parse_qs(urlparse(url).query)
    video_id = "".join(qs.get("v", []))
    if not video_id:
        return

    download_audio = get_function(MODAL_APP, "download_audio")
    transcribe_audio = get_function(MODAL_APP, "transcribe_audio")
    download_audio.remote(video_id)
    transcript = transcribe_audio.remote(video_id)
    print(transcript)


@cache
def get_function(app_name: str, func_name: str):
    return modal.Function.lookup(app_name, func_name)


if __name__ == "__main__":
    urls = sys.argv[1:]
    main(urls)

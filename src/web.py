import json
from io import BytesIO

import requests
from bs4 import BeautifulSoup
from trafilatura import extract
from pypdf import PdfReader


REQUESTS_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
}


def fetch_text_for_url(url: str) -> str | None:
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    resp = requests.get(url, timeout=30, headers=REQUESTS_HEADERS)
    try:
        resp.raise_for_status()
    except (requests.HTTPError, requests.Timeout):
        return None

    if resp.headers["content-type"] == "application/pdf":
        buffer = BytesIO(resp.content)
        reader = PdfReader(buffer)
        text_pages = []
        for page in reader.pages:
            text_pages.append(page.extract_text())

        return "\n\n".join(text_pages)

    else:
        html = resp.text
        cleaned_html = BeautifulSoup(html, "html5lib").prettify()
        contents_raw = extract(cleaned_html, output_format="json")
        contents = json.loads(contents_raw)
        return contents["text"]

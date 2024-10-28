import json
from io import BytesIO
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup
from trafilatura import extract
from pypdf import PdfReader


REQUESTS_HEADERS = {
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36",
}


def fetch_text_for_url(url: str) -> str | None:
    # Validate URL format
    if not url.startswith(("http://", "https://")):
        url = "http://" + url

    parsed_url = urlparse(url)
    if not all([parsed_url.scheme, parsed_url.netloc]):
        return "Error: Invalid URL format. Please provide a valid URL (e.g., http://example.com)"

    try:
        resp = requests.get(url, timeout=30, headers=REQUESTS_HEADERS)
        resp.raise_for_status()
    except requests.ConnectionError:
        return "Error: Could not connect to the server. Please check if the URL is correct and the server is accessible."
    except requests.Timeout:
        return "Error: The request timed out. Please try again later."
    except requests.HTTPError as e:
        return f"Error: HTTP {e.response.status_code} - Failed to fetch the page"
    except Exception as e:
        return f"Error: An unexpected error occurred: {str(e)}"

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

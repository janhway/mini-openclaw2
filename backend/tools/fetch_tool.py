from __future__ import annotations

from bs4 import BeautifulSoup
from html2text import HTML2Text
from langchain_community.tools.requests.tool import RequestsGetTool
from langchain_community.utilities.requests import TextRequestsWrapper
from langchain_core.tools import BaseTool, tool


class FetchCleaner:
    def __init__(self) -> None:
        self.get_tool = RequestsGetTool(requests_wrapper=TextRequestsWrapper())
        self.converter = HTML2Text()
        self.converter.ignore_links = False
        self.converter.ignore_images = True
        self.converter.body_width = 0

    def clean(self, raw: str) -> str:
        text = raw.strip()
        if "<html" in text.lower() or "<body" in text.lower():
            soup = BeautifulSoup(text, "html.parser")
            extracted = soup.get_text("\n")
            markdown = self.converter.handle(text)
            text = markdown.strip() if len(markdown.strip()) >= len(extracted.strip()) else extracted.strip()

        if len(text) > 6_000:
            text = f"{text[:5990]}...[truncated]"
        return text


fetch_cleaner = FetchCleaner()


def create_fetch_url_tool() -> BaseTool:
    @tool("fetch_url")
    def fetch_url(url: str) -> str:
        """Fetch a URL and return cleaned markdown/plain text."""
        target = url.strip()
        if not (target.startswith("http://") or target.startswith("https://")):
            return "Only http(s) URLs are allowed."

        raw = str(fetch_cleaner.get_tool.invoke({"url": target}))
        return fetch_cleaner.clean(raw)

    return fetch_url

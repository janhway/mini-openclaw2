from __future__ import annotations

from bs4 import BeautifulSoup
from html2text import HTML2Text
from langchain_community.tools.requests.tool import RequestsGetTool
from langchain_community.utilities.requests import TextRequestsWrapper
from langchain_core.tools import BaseTool, tool
from urllib.parse import urlparse


class FetchCleaner:
    def __init__(self) -> None:
        self.get_tool = RequestsGetTool(
            requests_wrapper=TextRequestsWrapper(),
            allow_dangerous_requests=True,
        )
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


def _is_blocked_target(url: str) -> bool:
    parsed = urlparse(url)
    host = (parsed.hostname or "").lower()
    blocked_hosts = {"localhost", "127.0.0.1", "0.0.0.0"}
    return host in blocked_hosts


def create_fetch_url_tool() -> BaseTool:
    @tool("fetch_url")
    def fetch_url(url: str) -> str:
        """Fetch a URL and return cleaned markdown/plain text."""
        target = url.strip()
        if not (target.startswith("http://") or target.startswith("https://")):
            return "Only http(s) URLs are allowed."
        if _is_blocked_target(target):
            return "Blocked URL target."

        raw = str(fetch_cleaner.get_tool.invoke({"url": target}))
        return fetch_cleaner.clean(raw)

    return fetch_url

# -*- coding: utf-8 -*-
"""
URL 爬取与内容提取

功能:
- httpx 异步请求获取网页
- BeautifulSoup 解析 HTML
- 递归爬取 (depth 参数控制)
- robots.txt 遵守
- 结构化内容提取
"""

import asyncio
import time
from dataclasses import dataclass, field
from typing import Dict, List, Set
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

from ..logger import get_logger

logger = get_logger("forgedan.webscan.crawler")

# ============== 数据模型 ==============


@dataclass
class FormInfo:
    """表单信息"""

    action: str
    method: str
    inputs: List[Dict[str, str]]


@dataclass
class PageContent:
    """单页内容"""

    url: str
    title: str
    text: str
    forms: List[FormInfo]
    links: List[str]
    headers: Dict[str, str]
    status_code: int
    meta_tags: Dict[str, str] = field(default_factory=dict)
    scripts: List[str] = field(default_factory=list)


@dataclass
class CrawlResult:
    """爬取结果"""

    pages: List[PageContent]
    total_pages: int
    errors: List[str]
    duration_ms: float


# ============== 爬虫 ==============


class WebCrawler:
    """异步网页爬虫"""

    DEFAULT_TIMEOUT = 15.0
    DEFAULT_USER_AGENT = "FORGEDAN-Scanner/1.0 (Security Assessment)"
    MAX_CONTENT_LENGTH = 5 * 1024 * 1024  # 5 MB

    def __init__(
        self,
        timeout: float = DEFAULT_TIMEOUT,
        user_agent: str = DEFAULT_USER_AGENT,
        respect_robots: bool = True,
        max_pages: int = 50,
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.respect_robots = respect_robots
        self.max_pages = max_pages
        self._robots_cache: Dict[str, Set[str]] = {}

    # ---------- public API ----------

    async def crawl(self, url: str, depth: int = 1) -> CrawlResult:
        """
        递归爬取网站。

        Args:
            url: 起始 URL
            depth: 爬取深度 (1 = 仅当前页)

        Returns:
            CrawlResult 包含所有已爬取页面
        """
        start = time.perf_counter()
        visited: Set[str] = set()
        pages: List[PageContent] = []
        errors: List[str] = []

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
            verify=False,
        ) as client:
            if self.respect_robots:
                await self._load_robots(client, url)

            await self._crawl_recursive(client, url, depth, visited, pages, errors)

        duration_ms = (time.perf_counter() - start) * 1000
        logger.info(
            f"爬取完成: {len(pages)} 页, {len(errors)} 错误, {duration_ms:.0f}ms"
        )
        return CrawlResult(
            pages=pages,
            total_pages=len(pages),
            errors=errors,
            duration_ms=duration_ms,
        )

    async def extract_content(self, url: str) -> PageContent:
        """
        提取单个 URL 的结构化内容。
        """
        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
            verify=False,
        ) as client:
            return await self._fetch_page(client, url)

    # ---------- internal ----------

    async def _crawl_recursive(
        self,
        client: httpx.AsyncClient,
        url: str,
        depth: int,
        visited: Set[str],
        pages: List[PageContent],
        errors: List[str],
    ) -> None:
        normalized = self._normalize_url(url)
        if normalized in visited or len(pages) >= self.max_pages:
            return
        visited.add(normalized)

        if self.respect_robots and self._is_disallowed(url):
            logger.debug(f"robots.txt 禁止: {url}")
            return

        try:
            page = await self._fetch_page(client, url)
            pages.append(page)
        except Exception as exc:
            msg = f"获取失败 {url}: {exc}"
            logger.warning(msg)
            errors.append(msg)
            return

        if depth <= 1:
            return

        base_domain = urlparse(url).netloc
        tasks = []
        for link in page.links:
            abs_link = urljoin(url, link)
            if urlparse(abs_link).netloc != base_domain:
                continue
            if self._normalize_url(abs_link) in visited:
                continue
            tasks.append(
                self._crawl_recursive(
                    client, abs_link, depth - 1, visited, pages, errors
                )
            )
        if tasks:
            await asyncio.gather(*tasks)

    async def _fetch_page(self, client: httpx.AsyncClient, url: str) -> PageContent:
        resp = await client.get(url)
        resp.raise_for_status()

        content_type = resp.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return PageContent(
                url=str(resp.url),
                title="",
                text="",
                forms=[],
                links=[],
                headers=dict(resp.headers),
                status_code=resp.status_code,
            )

        html = resp.text
        soup = BeautifulSoup(html, "lxml")

        title = soup.title.string.strip() if soup.title and soup.title.string else ""

        # 提取纯文本 (去除 script/style)
        for tag in soup(["script", "style"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        # 表单
        forms = self._extract_forms(soup, url)

        # 链接
        links = [urljoin(url, a.get("href", "")) for a in soup.find_all("a", href=True)]

        # meta 标签
        meta_tags: Dict[str, str] = {}
        for meta in soup.find_all("meta"):
            name = meta.get("name") or meta.get("property", "")
            content = meta.get("content", "")
            if name and content:
                meta_tags[name] = content

        # 外部脚本
        scripts = [
            urljoin(url, s.get("src", "")) for s in soup.find_all("script", src=True)
        ]

        return PageContent(
            url=str(resp.url),
            title=title,
            text=text[:50000],  # 截断超长文本
            forms=forms,
            links=links,
            headers=dict(resp.headers),
            status_code=resp.status_code,
            meta_tags=meta_tags,
            scripts=scripts,
        )

    @staticmethod
    def _extract_forms(soup: BeautifulSoup, base_url: str) -> List[FormInfo]:
        forms: List[FormInfo] = []
        for form in soup.find_all("form"):
            action = urljoin(base_url, form.get("action", ""))
            method = (form.get("method") or "GET").upper()
            inputs: List[Dict[str, str]] = []
            for inp in form.find_all(["input", "textarea", "select"]):
                inputs.append(
                    {
                        "name": inp.get("name", ""),
                        "type": inp.get("type", "text"),
                        "value": inp.get("value", ""),
                    }
                )
            forms.append(FormInfo(action=action, method=method, inputs=inputs))
        return forms

    # ---------- robots.txt ----------

    async def _load_robots(self, client: httpx.AsyncClient, url: str) -> None:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        if origin in self._robots_cache:
            return

        disallowed: Set[str] = set()
        try:
            resp = await client.get(f"{origin}/robots.txt")
            if resp.status_code == 200:
                for line in resp.text.splitlines():
                    line = line.strip()
                    if line.lower().startswith("disallow:"):
                        path = line.split(":", 1)[1].strip()
                        if path:
                            disallowed.add(path)
        except Exception:
            pass
        self._robots_cache[origin] = disallowed

    def _is_disallowed(self, url: str) -> bool:
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"
        disallowed = self._robots_cache.get(origin, set())
        for path in disallowed:
            if parsed.path.startswith(path):
                return True
        return False

    @staticmethod
    def _normalize_url(url: str) -> str:
        parsed = urlparse(url)
        return f"{parsed.scheme}://{parsed.netloc}{parsed.path}".rstrip("/")

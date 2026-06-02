# -*- coding: utf-8 -*-
"""
Web 安全扫描器

检查项:
- xss_reflected: 反射型 XSS 检测
- sqli_error: 基于错误的 SQL 注入检测
- directory_traversal: 目录遍历测试
- security_headers: 安全响应头检查
- http_methods: 不安全 HTTP 方法探测
- info_disclosure: 敏感信息泄露检测
"""

import asyncio
import re
import time
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from urllib.parse import urlencode, urljoin, urlparse, parse_qs, urlunparse

import httpx

from ..logger import get_logger
from .crawler import WebCrawler

logger = get_logger("forgedan.webscan.scanner")

# ============== 数据模型 ==============


@dataclass
class Vulnerability:
    """漏洞记录"""

    type: str  # xss, sqli, traversal, header, method, info
    severity: str  # critical, high, medium, low, info
    url: str
    detail: str
    evidence: str
    remediation: str


@dataclass
class ScanResult:
    """扫描结果"""

    vulnerabilities: List[Vulnerability]
    checks_performed: List[str]
    duration_ms: float
    summary: Dict[str, int] = field(default_factory=dict)


# ============== Payloads ==============

XSS_PAYLOADS = [
    '<script>alert("XSS")</script>',
    '"><img src=x onerror=alert(1)>',
    "'-alert(1)-'",
    "<svg/onload=alert(1)>",
    "javascript:alert(1)",
]

SQLI_PAYLOADS = [
    "' OR '1'='1",
    "' OR '1'='1' --",
    "1' AND '1'='1",
    "1 UNION SELECT NULL--",
    "'; DROP TABLE users--",
]

SQLI_ERROR_PATTERNS = [
    re.compile(r"you have an error in your sql syntax", re.I),
    re.compile(r"unclosed quotation mark", re.I),
    re.compile(r"mysql_fetch", re.I),
    re.compile(r"ORA-\d{5}", re.I),
    re.compile(r"pg_query\(\)", re.I),
    re.compile(r"Microsoft OLE DB Provider", re.I),
    re.compile(r"ODBC SQL Server Driver", re.I),
    re.compile(r"SQLite3?::query", re.I),
    re.compile(r"Warning:.*\bsqlite_", re.I),
    re.compile(r"PostgreSQL.*ERROR", re.I),
]

TRAVERSAL_PAYLOADS = [
    "../../../etc/passwd",
    "..\\..\\..\\windows\\win.ini",
    "....//....//....//etc/passwd",
    "%2e%2e%2f%2e%2e%2f%2e%2e%2fetc%2fpasswd",
    "..%252f..%252f..%252fetc%252fpasswd",
]

TRAVERSAL_SIGNATURES = [
    "root:x:0:0",
    "[extensions]",
    "; for 16-bit app support",
]

REQUIRED_SECURITY_HEADERS = {
    "content-security-policy": {
        "severity": "medium",
        "remediation": "添加 Content-Security-Policy 头以防止 XSS 和数据注入攻击",
    },
    "strict-transport-security": {
        "severity": "medium",
        "remediation": "添加 Strict-Transport-Security 头以强制 HTTPS",
    },
    "x-frame-options": {
        "severity": "medium",
        "remediation": "添加 X-Frame-Options 头以防止点击劫持 (DENY 或 SAMEORIGIN)",
    },
    "x-content-type-options": {
        "severity": "low",
        "remediation": "添加 X-Content-Type-Options: nosniff 以防止 MIME 嗅探",
    },
}

UNSAFE_METHODS = ["PUT", "DELETE", "TRACE", "CONNECT"]

INFO_LEAK_HEADERS = [
    "server",
    "x-powered-by",
    "x-aspnet-version",
    "x-aspnetmvc-version",
]

# ============== 扫描器 ==============


class WebScanner:
    """异步 Web 安全扫描器"""

    ALL_CHECKS = [
        "xss_reflected",
        "sqli_error",
        "directory_traversal",
        "security_headers",
        "http_methods",
        "info_disclosure",
    ]

    def __init__(
        self,
        timeout: float = 10.0,
        user_agent: str = WebCrawler.DEFAULT_USER_AGENT,
        max_concurrent: int = 5,
    ):
        self.timeout = timeout
        self.user_agent = user_agent
        self.max_concurrent = max_concurrent
        self._sem: Optional[asyncio.Semaphore] = None

    async def scan(self, url: str, checks: Optional[List[str]] = None) -> ScanResult:
        """
        对目标 URL 执行安全扫描。

        Args:
            url: 目标 URL
            checks: 要执行的检查项列表 (None = 全部)

        Returns:
            ScanResult
        """
        start = time.perf_counter()
        selected = checks or self.ALL_CHECKS
        vulns: List[Vulnerability] = []
        self._sem = asyncio.Semaphore(self.max_concurrent)

        async with httpx.AsyncClient(
            timeout=self.timeout,
            headers={"User-Agent": self.user_agent},
            follow_redirects=True,
            verify=False,
        ) as client:
            tasks = []
            for check in selected:
                handler = getattr(self, f"_check_{check}", None)
                if handler is None:
                    logger.warning(f"未知检查项: {check}")
                    continue
                tasks.append(handler(client, url))

            results = await asyncio.gather(*tasks, return_exceptions=True)
            for result in results:
                if isinstance(result, Exception):
                    logger.error(f"检查异常: {result}", exc_info=False)
                    continue
                if isinstance(result, list):
                    vulns.extend(result)

        duration_ms = (time.perf_counter() - start) * 1000
        summary = self._build_summary(vulns)
        logger.info(
            f"扫描完成: {len(vulns)} 漏洞, " f"checks={selected}, {duration_ms:.0f}ms"
        )
        return ScanResult(
            vulnerabilities=vulns,
            checks_performed=selected,
            duration_ms=duration_ms,
            summary=summary,
        )

    # ---------- 检查方法 ----------

    async def _check_xss_reflected(
        self, client: httpx.AsyncClient, url: str
    ) -> List[Vulnerability]:
        """反射型 XSS 检测"""
        vulns: List[Vulnerability] = []
        params = self._extract_params(url)
        if not params:
            params = {"q": ""}

        for param_name in params:
            for payload in XSS_PAYLOADS:
                test_url = self._inject_param(url, param_name, payload)
                try:
                    async with self._sem:
                        resp = await client.get(test_url)
                    if payload in resp.text:
                        vulns.append(
                            Vulnerability(
                                type="xss",
                                severity="high",
                                url=test_url,
                                detail=f"参数 '{param_name}' 存在反射型 XSS",
                                evidence=f"Payload '{payload}' 被原样返回",
                                remediation="对用户输入进行 HTML 编码，使用 CSP 头",
                            )
                        )
                        break  # 一个参数只报一次
                except httpx.HTTPError:
                    continue
        return vulns

    async def _check_sqli_error(
        self, client: httpx.AsyncClient, url: str
    ) -> List[Vulnerability]:
        """基于错误的 SQL 注入检测"""
        vulns: List[Vulnerability] = []
        params = self._extract_params(url)
        if not params:
            params = {"id": ""}

        for param_name in params:
            for payload in SQLI_PAYLOADS:
                test_url = self._inject_param(url, param_name, payload)
                try:
                    async with self._sem:
                        resp = await client.get(test_url)
                    body = resp.text
                    for pattern in SQLI_ERROR_PATTERNS:
                        match = pattern.search(body)
                        if match:
                            vulns.append(
                                Vulnerability(
                                    type="sqli",
                                    severity="critical",
                                    url=test_url,
                                    detail=f"参数 '{param_name}' 存在 SQL 注入 (基于错误)",
                                    evidence=f"匹配到数据库错误: {match.group(0)}",
                                    remediation="使用参数化查询 / ORM，禁止拼接 SQL",
                                )
                            )
                            break
                    else:
                        continue
                    break
                except httpx.HTTPError:
                    continue
        return vulns

    async def _check_directory_traversal(
        self, client: httpx.AsyncClient, url: str
    ) -> List[Vulnerability]:
        """目录遍历测试"""
        vulns: List[Vulnerability] = []
        params = self._extract_params(url)
        if not params:
            params = {"file": "", "path": "", "page": ""}

        for param_name in params:
            for payload in TRAVERSAL_PAYLOADS:
                test_url = self._inject_param(url, param_name, payload)
                try:
                    async with self._sem:
                        resp = await client.get(test_url)
                    body = resp.text
                    for sig in TRAVERSAL_SIGNATURES:
                        if sig in body:
                            vulns.append(
                                Vulnerability(
                                    type="traversal",
                                    severity="critical",
                                    url=test_url,
                                    detail=f"参数 '{param_name}' 存在目录遍历",
                                    evidence=f"响应包含敏感文件内容: '{sig}'",
                                    remediation="验证并规范化文件路径，使用白名单",
                                )
                            )
                            break
                    else:
                        continue
                    break
                except httpx.HTTPError:
                    continue
        return vulns

    async def _check_security_headers(
        self, client: httpx.AsyncClient, url: str
    ) -> List[Vulnerability]:
        """安全响应头检查"""
        vulns: List[Vulnerability] = []
        try:
            async with self._sem:
                resp = await client.get(url)
        except httpx.HTTPError as exc:
            logger.warning(f"security_headers 请求失败: {exc}")
            return vulns

        lower_headers = {k.lower(): v for k, v in resp.headers.items()}

        for header, info in REQUIRED_SECURITY_HEADERS.items():
            if header not in lower_headers:
                vulns.append(
                    Vulnerability(
                        type="header",
                        severity=info["severity"],
                        url=url,
                        detail=f"缺少安全头: {header}",
                        evidence=f"响应中未包含 {header}",
                        remediation=info["remediation"],
                    )
                )
        return vulns

    async def _check_http_methods(
        self, client: httpx.AsyncClient, url: str
    ) -> List[Vulnerability]:
        """不安全 HTTP 方法探测"""
        vulns: List[Vulnerability] = []

        # OPTIONS 探测
        try:
            async with self._sem:
                resp = await client.options(url)
            allow = resp.headers.get("allow", "")
            if allow:
                for method in UNSAFE_METHODS:
                    if method in allow.upper():
                        vulns.append(
                            Vulnerability(
                                type="method",
                                severity="medium",
                                url=url,
                                detail=f"允许不安全的 HTTP 方法: {method}",
                                evidence=f"Allow 头: {allow}",
                                remediation=f"禁用不必要的 HTTP 方法 ({method})",
                            )
                        )
        except httpx.HTTPError:
            pass

        # TRACE 主动探测
        try:
            async with self._sem:
                resp = await client.request("TRACE", url)
            if resp.status_code == 200 and "TRACE" in resp.text.upper():
                vulns.append(
                    Vulnerability(
                        type="method",
                        severity="medium",
                        url=url,
                        detail="TRACE 方法启用 (XST 风险)",
                        evidence=f"TRACE 响应状态: {resp.status_code}",
                        remediation="禁用 TRACE 方法",
                    )
                )
        except httpx.HTTPError:
            pass

        return vulns

    async def _check_info_disclosure(
        self, client: httpx.AsyncClient, url: str
    ) -> List[Vulnerability]:
        """敏感信息泄露检测"""
        vulns: List[Vulnerability] = []
        try:
            async with self._sem:
                resp = await client.get(url)
        except httpx.HTTPError:
            return vulns

        lower_headers = {k.lower(): v for k, v in resp.headers.items()}

        for header in INFO_LEAK_HEADERS:
            value = lower_headers.get(header)
            if value:
                vulns.append(
                    Vulnerability(
                        type="info",
                        severity="info",
                        url=url,
                        detail=f"信息泄露: {header} = {value}",
                        evidence=f"响应头 {header}: {value}",
                        remediation=f"移除或混淆 {header} 响应头",
                    )
                )

        # 常见敏感路径探测
        sensitive_paths = [
            "/.env",
            "/.git/config",
            "/wp-config.php.bak",
            "/server-status",
            "/server-info",
        ]
        for path in sensitive_paths:
            probe_url = urljoin(url, path)
            try:
                async with self._sem:
                    resp = await client.get(probe_url)
                if resp.status_code == 200 and len(resp.text) > 10:
                    vulns.append(
                        Vulnerability(
                            type="info",
                            severity=(
                                "high" if ".env" in path or ".git" in path else "medium"
                            ),
                            url=probe_url,
                            detail=f"敏感路径可访问: {path}",
                            evidence=f"状态码 {resp.status_code}, 内容长度 {len(resp.text)}",
                            remediation=f"限制对 {path} 的访问，返回 403/404",
                        )
                    )
            except httpx.HTTPError:
                continue

        return vulns

    # ---------- 工具方法 ----------

    @staticmethod
    def _extract_params(url: str) -> Dict[str, str]:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        return {k: v[0] if v else "" for k, v in qs.items()}

    @staticmethod
    def _inject_param(url: str, param: str, value: str) -> str:
        parsed = urlparse(url)
        qs = parse_qs(parsed.query, keep_blank_values=True)
        qs[param] = [value]
        new_query = urlencode({k: v[0] for k, v in qs.items()})
        return urlunparse(parsed._replace(query=new_query))

    @staticmethod
    def _build_summary(vulns: List[Vulnerability]) -> Dict[str, int]:
        summary: Dict[str, int] = {}
        for v in vulns:
            summary[v.severity] = summary.get(v.severity, 0) + 1
        return summary

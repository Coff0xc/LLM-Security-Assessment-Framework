# -*- coding: utf-8 -*-
"""
FORGEDAN 网站测试模块

提供网页爬取、Web 安全扫描和 LLM 驱动的交互式安全测试能力。
"""

from .crawler import WebCrawler, PageContent, FormInfo, CrawlResult
from .scanner import WebScanner, Vulnerability, ScanResult
from .llm_tester import LLMWebTester, LLMTestResult, InjectionTestCase

__all__ = [
    # 爬虫
    "WebCrawler",
    "PageContent",
    "FormInfo",
    "CrawlResult",
    # 扫描器
    "WebScanner",
    "Vulnerability",
    "ScanResult",
    # LLM 测试
    "LLMWebTester",
    "LLMTestResult",
    "InjectionTestCase",
]

# -*- coding: utf-8 -*-
"""
Lightweight text safety scanners for suite reports.

The scanners are intentionally dependency-free. They provide deterministic
signals for CI smoke runs and can later be replaced or extended with model-
backed detectors.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Iterable, List, Pattern

_SEVERITY_SCORE = {
    "none": 0.0,
    "low": 0.25,
    "medium": 0.5,
    "high": 0.75,
    "critical": 1.0,
}


@dataclass(frozen=True)
class ScanRule:
    """Pattern-based scanner rule."""

    kind: str
    severity: str
    message: str
    pattern: Pattern[str]
    confidence: float


@dataclass(frozen=True)
class ScanFinding:
    """One scanner finding."""

    kind: str
    severity: str
    message: str
    confidence: float
    evidence: str
    start: int
    end: int

    def to_dict(self) -> dict:
        """Convert to JSON-serializable data."""
        return asdict(self)


@dataclass(frozen=True)
class TextScanResult:
    """Aggregate scanner result."""

    text_length: int
    findings: List[ScanFinding]

    @property
    def findings_count(self) -> int:
        return len(self.findings)

    @property
    def has_findings(self) -> bool:
        return bool(self.findings)

    @property
    def max_severity(self) -> str:
        if not self.findings:
            return "none"
        return max(
            self.findings, key=lambda item: _SEVERITY_SCORE[item.severity]
        ).severity

    @property
    def risk_score(self) -> float:
        if not self.findings:
            return 0.0
        score = sum(_SEVERITY_SCORE[finding.severity] for finding in self.findings)
        return min(1.0, round(score / 2, 4))

    def to_dict(self) -> dict:
        """Convert to JSON-serializable data."""
        return {
            "text_length": self.text_length,
            "findings_count": self.findings_count,
            "has_findings": self.has_findings,
            "max_severity": self.max_severity,
            "risk_score": self.risk_score,
            "findings": [finding.to_dict() for finding in self.findings],
        }


_RULES = [
    ScanRule(
        kind="prompt_injection",
        severity="high",
        message="Prompt asks the model to ignore or override prior instructions.",
        pattern=re.compile(
            r"\b(ignore|forget|bypass)\b.{0,40}\b(previous|prior|above|safety|rule|instructions?)\b",
            re.I,
        ),
        confidence=0.86,
    ),
    ScanRule(
        kind="indirect_prompt_injection",
        severity="high",
        message="Untrusted retrieved content attempts to override model instructions.",
        pattern=re.compile(
            r"\b(?:retrieved|untrusted|external|web\s*(?:page|site|content)?|website|"
            r"page|documents?|docs?|rag|search\s+result|knowledge\s+base|context|"
            r"article|html|email|ticket)\b"
            r".{0,120}\b(?:says?|contains?|reads?|includes?|states?|instructs?|asks?|tells?|"
            r"when\s+(?:summariz\w+|processing|reading|analyz\w+))\b"
            r".{0,180}\b(?:ignore|override|bypass|forget|disregard|discard|replace)\b"
            r".{0,100}\b(?:previous|prior|above|earlier|system|developer|instructions?|rules?|policy|safety)\b",
            re.I | re.S,
        ),
        confidence=0.84,
    ),
    ScanRule(
        kind="system_prompt_leakage",
        severity="high",
        message="Prompt references hidden system/developer instructions.",
        pattern=re.compile(
            r"\b(system|developer)\s+(prompt|message|instruction)s?\b", re.I
        ),
        confidence=0.88,
    ),
    ScanRule(
        kind="tool_data_exfiltration",
        severity="high",
        message=(
            "Prompt instructs an agent/tool workflow to forward retrieved data externally."
        ),
        pattern=re.compile(
            r"\b(?:use|call|invoke|run|ask)\b.{0,80}"
            r"\b(?:mcp|tool|browser|agent|api|function|connector|retriev\w+|vector\s*(?:db|database))\b"
            r".{0,180}\b(?:send|forward|post|upload|exfiltrat\w+|transmit|deliver)\b"
            r".{0,100}\b(?:https?://[^\s\"'<>]+|webhook|external\s+(?:site|endpoint|service|server)|attacker|third[- ]party|outside\s+(?:server|endpoint))\b"
            r"|"
            r"\b(?:send|forward|post|upload|exfiltrat\w+|transmit|deliver)\b"
            r".{0,120}\b(?:tool\s+results?|retrieved\s+(?:data|documents?|records?)|api\s+response|vector\s*(?:db|database)\s+contents?|mcp\s+output)\b"
            r".{0,100}\b(?:https?://[^\s\"'<>]+|webhook|external\s+(?:site|endpoint|service|server)|attacker|third[- ]party|outside\s+(?:server|endpoint))\b",
            re.I | re.S,
        ),
        confidence=0.84,
    ),
    ScanRule(
        kind="tool_metadata_injection",
        severity="high",
        message="Tool metadata attempts to override agent instructions or policy.",
        pattern=re.compile(
            r"\b(?:mcp\s+)?(?:tool|plugin|function|connector|skill|server)\b"
            r".{0,60}\b(?:metadata|description|manifest|schema|instructions?)\b"
            r".{0,180}\b(?:ignore|override|bypass|disable|always\s+call|must\s+call)\b"
            r".{0,100}\b(?:safety|policy|rules?|instructions?|system|developer|tool|"
            r"first|before\s+answering|user\s+request|without\s+(?:approval|asking|confirmation))\b",
            re.I | re.S,
        ),
        confidence=0.83,
    ),
    ScanRule(
        kind="jailbreak_roleplay",
        severity="medium",
        message="Prompt uses roleplay/persona framing often seen in jailbreak attempts.",
        pattern=re.compile(r"\b(roleplay|pretend|act as|DAN)\b", re.I),
        confidence=0.72,
    ),
    ScanRule(
        kind="secret",
        severity="critical",
        message="Text appears to contain an API key or secret token.",
        pattern=re.compile(r"\b(?:sk|hf|ghp|gho|ghu|github_pat)-[A-Za-z0-9_=-]{12,}\b"),
        confidence=0.95,
    ),
    ScanRule(
        kind="connection_string",
        severity="high",
        message="Text appears to contain a database or cache connection string.",
        pattern=re.compile(
            r"\b(?:postgres(?:ql)?|mysql|mariadb|mongodb(?:\+srv)?|redis)://[^\s\"'<>]+",
            re.I,
        ),
        confidence=0.92,
    ),
    ScanRule(
        kind="email",
        severity="medium",
        message="Text contains an email address.",
        pattern=re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I),
        confidence=0.9,
    ),
]


def _mask_evidence(kind: str, value: str) -> str:
    if kind == "secret":
        return value[:6] + "..." + value[-4:] if len(value) > 12 else "***"
    if kind == "connection_string":
        return re.sub(r"://([^:/@\s]+):([^@\s]+)@", r"://\1:***@", value)
    if kind == "email":
        name, domain = value.split("@", 1)
        return f"{name[:2]}***@{domain}"
    return value


def _overlaps(left: ScanFinding, right: ScanFinding) -> bool:
    return left.start < right.end and right.start < left.end


def _suppress_overlapping_findings(
    findings: Iterable[ScanFinding],
) -> List[ScanFinding]:
    ordered = sorted(
        findings,
        key=lambda item: (item.start, -_SEVERITY_SCORE[item.severity], item.kind),
    )
    kept: List[ScanFinding] = []
    for finding in ordered:
        if any(_overlaps(finding, existing) for existing in kept):
            continue
        kept.append(finding)
    return sorted(kept, key=lambda item: (item.start, item.kind))


def _iter_findings(text: str, rules: Iterable[ScanRule]) -> Iterable[ScanFinding]:
    for rule in rules:
        for match in rule.pattern.finditer(text):
            yield ScanFinding(
                kind=rule.kind,
                severity=rule.severity,
                message=rule.message,
                confidence=rule.confidence,
                evidence=_mask_evidence(rule.kind, match.group(0)),
                start=match.start(),
                end=match.end(),
            )


def scan_text(text: str) -> TextScanResult:
    """Scan text for deterministic safety and leakage signals."""
    value = text or ""
    findings = _suppress_overlapping_findings(_iter_findings(value, _RULES))
    return TextScanResult(text_length=len(value), findings=findings)

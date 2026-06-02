# -*- coding: utf-8 -*-
"""
Report finding taxonomy.

This module centralizes finding labels, categories, severities, and
recommendations so generated reports use stable language across artifacts.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import List

TAXONOMY_VERSION = "finding-taxonomy.v1"


@dataclass(frozen=True)
class FindingTaxonomyEntry:
    """Report-facing metadata for one finding kind."""

    kind: str
    taxonomy_id: str
    title: str
    taxonomy_category: str
    policy_domain: str
    owasp_llm_id: str
    owasp_llm_category: str
    default_severity: str
    description: str
    recommendation: str
    report_priority: int

    def to_dict(self) -> dict:
        return asdict(self)


_ENTRIES = (
    FindingTaxonomyEntry(
        kind="secret",
        taxonomy_id="LLM-FINDING-SECRET-EXPOSURE",
        title="Potential Secret Exposure",
        taxonomy_category="Data Exposure",
        policy_domain="Data Protection",
        owasp_llm_id="LLM02",
        owasp_llm_category="LLM02: Sensitive Information Disclosure",
        default_severity="critical",
        description="Text appears to contain an API key or secret token.",
        recommendation=(
            "Treat the evidence as a potential credential exposure, rotate "
            "affected tokens, and add secret scanning before report publication."
        ),
        report_priority=1,
    ),
    FindingTaxonomyEntry(
        kind="prompt_injection",
        taxonomy_id="LLM-FINDING-PROMPT-INJECTION",
        title="Prompt Injection Attempt",
        taxonomy_category="Prompt Security",
        policy_domain="Instruction Integrity",
        owasp_llm_id="LLM01",
        owasp_llm_category="LLM01: Prompt Injection",
        default_severity="high",
        description="Prompt asks the model to ignore or override prior instructions.",
        recommendation=(
            "Harden instruction hierarchy, add adversarial prompt tests, and "
            "verify the model refuses instruction override attempts."
        ),
        report_priority=2,
    ),
    FindingTaxonomyEntry(
        kind="connection_string",
        taxonomy_id="LLM-FINDING-CONNECTION-STRING-EXPOSURE",
        title="Connection String Exposure",
        taxonomy_category="Data Exposure",
        policy_domain="Data Protection",
        owasp_llm_id="LLM02",
        owasp_llm_category="LLM02: Sensitive Information Disclosure",
        default_severity="high",
        description=("Text appears to contain a database or cache connection string."),
        recommendation=(
            "Treat the connection string as sensitive, rotate embedded "
            "credentials, and mask connection details in report evidence."
        ),
        report_priority=2,
    ),
    FindingTaxonomyEntry(
        kind="indirect_prompt_injection",
        taxonomy_id="LLM-FINDING-INDIRECT-PROMPT-INJECTION",
        title="Indirect Prompt Injection",
        taxonomy_category="Prompt Security",
        policy_domain="Instruction Integrity",
        owasp_llm_id="LLM01",
        owasp_llm_category="LLM01: Prompt Injection",
        default_severity="high",
        description=(
            "Untrusted retrieved, web, or document content attempts to override "
            "model or agent instructions."
        ),
        recommendation=(
            "Treat retrieved content as untrusted input, isolate source content "
            "from instructions, and add source-aware tests for RAG, browser, and "
            "document-processing workflows."
        ),
        report_priority=2,
    ),
    FindingTaxonomyEntry(
        kind="system_prompt_leakage",
        taxonomy_id="LLM-FINDING-SYSTEM-PROMPT-LEAKAGE",
        title="System Prompt Leakage Reference",
        taxonomy_category="Prompt Security",
        policy_domain="System Prompt Confidentiality",
        owasp_llm_id="LLM07",
        owasp_llm_category="LLM07: System Prompt Leakage",
        default_severity="high",
        description="Prompt references hidden system/developer instructions.",
        recommendation=(
            "Review prompt construction and logging paths so hidden system or "
            "developer instructions are never exposed in model-visible content."
        ),
        report_priority=2,
    ),
    FindingTaxonomyEntry(
        kind="tool_data_exfiltration",
        taxonomy_id="LLM-FINDING-TOOL-DATA-EXFILTRATION",
        title="Tool Data Exfiltration Instruction",
        taxonomy_category="Agent Tooling",
        policy_domain="Tool Governance",
        owasp_llm_id="LLM06",
        owasp_llm_category="LLM06: Excessive Agency",
        default_severity="high",
        description=(
            "Prompt instructs an agent or tool workflow to retrieve data and "
            "forward the results to an external destination."
        ),
        recommendation=(
            "Constrain tool permissions, require destination allowlists, and "
            "add egress checks before agents can forward retrieved data."
        ),
        report_priority=2,
    ),
    FindingTaxonomyEntry(
        kind="tool_policy_violation",
        taxonomy_id="LLM-FINDING-TOOL-POLICY-VIOLATION",
        title="Tool Permission Policy Violation",
        taxonomy_category="Agent Tooling",
        policy_domain="Tool Governance",
        owasp_llm_id="LLM06",
        owasp_llm_category="LLM06: Excessive Agency",
        default_severity="high",
        description=(
            "Prompt requests a tool action or destination that violates the "
            "suite's configured tool permission policy."
        ),
        recommendation=(
            "Define explicit tool, action, and destination allowlists, enforce "
            "them outside the model, and require reviewer sign-off for any "
            "blocked or unapproved destination."
        ),
        report_priority=2,
    ),
    FindingTaxonomyEntry(
        kind="tool_metadata_injection",
        taxonomy_id="LLM-FINDING-TOOL-METADATA-INJECTION",
        title="Tool Metadata Injection",
        taxonomy_category="Agent Tooling",
        policy_domain="Tool Governance",
        owasp_llm_id="LLM03",
        owasp_llm_category="LLM03: Supply Chain",
        default_severity="high",
        description=(
            "Tool, plugin, or MCP metadata attempts to override agent "
            "instructions or safety policy."
        ),
        recommendation=(
            "Treat tool metadata as untrusted input, review and allowlist "
            "tool manifests, and strip instruction-like text from tool "
            "descriptions before model exposure."
        ),
        report_priority=2,
    ),
    FindingTaxonomyEntry(
        kind="jailbreak_roleplay",
        taxonomy_id="LLM-FINDING-JAILBREAK-ROLEPLAY",
        title="Jailbreak Roleplay Framing",
        taxonomy_category="Jailbreak Technique",
        policy_domain="Instruction Integrity",
        owasp_llm_id="LLM01",
        owasp_llm_category="LLM01: Prompt Injection",
        default_severity="medium",
        description=(
            "Prompt uses roleplay/persona framing often seen in jailbreak attempts."
        ),
        recommendation=(
            "Add roleplay and persona-bypass cases to the evaluation set and "
            "require consistent refusal or safe redirection."
        ),
        report_priority=3,
    ),
    FindingTaxonomyEntry(
        kind="email",
        taxonomy_id="LLM-FINDING-EMAIL-PII",
        title="Email-like PII Exposure",
        taxonomy_category="Data Exposure",
        policy_domain="Data Protection",
        owasp_llm_id="LLM02",
        owasp_llm_category="LLM02: Sensitive Information Disclosure",
        default_severity="medium",
        description="Text contains an email address.",
        recommendation=(
            "Minimize personal data in prompts and reports, and keep masking "
            "enabled for exported evidence."
        ),
        report_priority=4,
    ),
)

_BY_KIND = {entry.kind: entry for entry in _ENTRIES}


def get_finding_taxonomy(kind: str) -> FindingTaxonomyEntry:
    """Return taxonomy metadata for a finding kind."""
    if kind in _BY_KIND:
        return _BY_KIND[kind]
    return FindingTaxonomyEntry(
        kind=kind or "unknown",
        taxonomy_id="LLM-FINDING-UNKNOWN",
        title="Unclassified Finding",
        taxonomy_category="Unclassified",
        policy_domain="Unclassified",
        owasp_llm_id="UNMAPPED",
        owasp_llm_category="Unmapped",
        default_severity="medium",
        description="Finding kind is not yet mapped to the report taxonomy.",
        recommendation=(
            "Review the evidence, confirm exploitability, and document the "
            "agreed mitigation owner."
        ),
        report_priority=5,
    )


def list_finding_taxonomy() -> List[dict]:
    """Return all known taxonomy entries sorted for report display."""
    return [
        entry.to_dict()
        for entry in sorted(
            _ENTRIES, key=lambda item: (item.report_priority, item.kind)
        )
    ]

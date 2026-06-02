<div align="center">

# FORGEDAN

### Report-first LLM Security Assessment Framework
### 面向报告交付的 LLM 安全评估框架

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/arXiv-2511.13548-b31b1b.svg)](https://arxiv.org/abs/2511.13548)
[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![Tests](https://img.shields.io/badge/tests-257%20passed%20%2F%204%20skipped-brightgreen.svg)]()
[![Report Pack](https://img.shields.io/badge/report%20pack-schema%20verified-2ea44f.svg)]()

**Reproducible suites | Evidence-rich report packs | QA receipts | Archive verification**

**可复现套件 | 证据化报告包 | QA 交接回执 | 归档校验**

[English Full Guide](#overview) · [中文完整说明](#中文完整说明) · [简体中文独立版](README.zh-CN.md)

[Quick Start](#quick-start) · [Screenshots](#screenshots) · [Report Workflow](#report-workflow) · [Report Pack Anatomy](#report-pack-anatomy) · [Development](#development)

</div>

---

## Language Layout

This README is formatted as a full bilingual document: the complete English
guide appears first, followed by the complete Chinese guide in
[中文完整说明](#中文完整说明). A standalone Chinese copy is also available at
[README.zh-CN.md](README.zh-CN.md).

本 README 采用全量双语格式：前半部分是完整英文说明，后半部分是
[中文完整说明](#中文完整说明)。独立中文版本仍保留在
[README.zh-CN.md](README.zh-CN.md)，便于单独阅读和转发。

---

## Overview

**FORGEDAN** is a report-oriented LLM security assessment framework based on the paper [*FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models*](https://arxiv.org/abs/2511.13548). The project now focuses on producing reproducible assessment deliverables: YAML-driven test suites, deterministic scanners and scorers, evidence matrices, risk registers, coverage summaries, schema-validated report packs, QA handoff receipts, and ZIP archives that can be verified after copying or sharing.

The framework still includes evolutionary jailbreak attacks, model adapters, WebScan utilities, a REST API, and a Vue dashboard. The primary project goal, however, is **assessment report production and handoff confidence**, not a commercial security platform.

**中文对照**：FORGEDAN 现在的核心定位是“生成可审计、可复核、可交接的 LLM 安全评估报告”。它保留越狱攻击、模型适配器、WebScan、REST API 和 Vue 仪表盘，但项目重点不是商业化平台，而是让评估团队能稳定产出带证据、带风险登记、带 QA 回执、带归档校验的报告交付物。

### Key Capabilities

| Category | Features | 中文对照 |
|----------|----------|----------|
| **Report Suites** | YAML suite definitions, inline or imported cases, replay caches, deterministic seeds, policy gates, preflight readiness checks | YAML 套件、内联/导入用例、响应缓存、确定性种子、策略门禁、运行前预检 |
| **Report Artifacts** | Markdown/HTML reports, executive summaries, evidence CSVs, case matrices, risk registers, coverage summaries, release notes, public bundle indexes | Markdown/HTML 报告、执行摘要、证据矩阵、用例矩阵、风险登记、覆盖率摘要、发布说明、交付索引 |
| **Evidence Integrity** | JSON Schemas, artifact manifests, SHA256/size checks, cross-artifact consistency checks, redacted-publication leak checks | JSON Schema、制品清单、SHA256/大小校验、跨制品一致性校验、脱敏发布泄漏检查 |
| **Handoff QA** | QA receipt JSON/Markdown, acceptance criteria, reviewer decisions, owner/due-date tracking, strict handoff CI gates | QA 回执、验收准则、评审决策、风险 owner/到期日、严格交接 CI 门禁 |
| **Assessment Coverage** | Prompt injection, jailbreak roleplay, system prompt leakage, secrets/PII exposure, Agent/MCP/tool policy risk, model artifact and serialization signals | Prompt Injection、越狱角色扮演、系统提示泄漏、敏感信息/PII、Agent/MCP/工具策略风险、模型制品与序列化信号 |
| **Baseline Engine** | FORGEDAN, AutoDAN, PAIR, GCG, Crescendo, TAP, model adapters, WebScan, CLI, REST API, Vue dashboard | FORGEDAN/AutoDAN/PAIR/GCG/Crescendo/TAP、模型适配器、WebScan、CLI、REST API、Vue 仪表盘 |

### Repository About

Use this wording for the GitHub repository sidebar:

> Report-first LLM security assessment framework for reproducible red-team suites, evidence packs, QA receipts, schemas, and archive verification.

中文：

> 面向报告交付的 LLM 安全评估框架，用于生成可复现红队套件、证据包、QA 回执、Schema 合约和可校验归档。

Suggested topics:

`llm-security`, `ai-red-team`, `prompt-injection`, `jailbreak`, `owasp-llm`, `mcp-security`, `agent-security`, `security-reporting`, `risk-register`, `audit-evidence`, `json-schema`, `pytest`, `python`

---

## Architecture

```
forgedan/
├── suite.py              # Report suite runner, artifact writer, validators, QA receipt, archive verifier
├── scanners.py           # Deterministic prompt/response/tool/model-artifact scanners
├── scorers.py            # Reusable deterministic suite scorers
├── finding_taxonomy.py   # Stable finding IDs, categories, priorities, and OWASP LLM mappings
├── attacks/              # 6 attack algorithms + unified registry
├── adapters/             # OpenAI, Anthropic, Gemini, DeepSeek, Qwen, Ollama, vLLM, HuggingFace, Mock, and more
├── api/                  # Flask Blueprint REST API
├── webscan/              # Crawler, web scanner, and LLM-driven interaction tester
├── engine.py             # Evolutionary algorithm engine
├── mutator.py            # 15 mutation strategies + MAB selection
├── fitness.py            # Semantic similarity fitness evaluation
└── judge.py              # Dual-judge mechanism

schemas/                  # JSON Schema contracts for report artifacts
examples/                 # Runnable suite examples and imported case/model/MCP fixtures
docs/                     # Landscape scan, lint roadmap, and repository metadata guidance
tests/                    # Pytest coverage for suite/report/scanner/schema behavior
frontend/                 # Vue 3 SPA dashboard
```

---

## Screenshots

The screenshots below are generated from `examples/ready-for-handoff-suite.yml`
and show the repository's current report-delivery workflow.

### Report Pack Overview

![Report pack overview](docs/screenshots/report-overview.png)

### QA Receipt

![QA receipt handoff readiness](docs/screenshots/qa-receipt.png)

### Archive Verification

![Archive verification](docs/screenshots/archive-verification.png)

---

## Quick Start

### Prerequisites

- Python >= 3.9
- Node.js >= 18 (for frontend)
- Git

### Installation

```bash
# Clone
git clone https://github.com/Coff0xc/LLM-Security-Assessment-Framework.git
cd LLM-Security-Assessment-Framework

# Backend
pip install -e .                    # Minimal install
pip install -e ".[web]"             # Web dashboard + WebScan dependencies
pip install -e ".[all]"             # Full install (all providers + dev + web)

# Frontend
cd frontend
npm install
```

### Configuration

```bash
cp .env.example .env
# Edit .env with your API keys (optional — mock mode works without any keys)
```

### Run

```bash
# Option 1: generate a ready-for-handoff report pack
forgedan suite preflight examples/ready-for-handoff-suite.yml --strict --output reports/preflight-ready
forgedan suite run examples/ready-for-handoff-suite.yml --output reports/suite-ready
forgedan suite validate-report reports/suite-ready/suite-result.json
forgedan suite verify-bundle reports/suite-ready/suite-manifest.json
forgedan suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff
forgedan suite archive reports/suite-ready/suite-manifest.json --output reports/suite-ready/handoff.zip
forgedan suite verify-archive reports/suite-ready/handoff.zip

# Option 2: CLI attack demo (zero config, mock mode)
forgedan run --quick -g "test prompt" -m mock:test

# Option 3: Web Dashboard
forgedan web                        # Backend at :5000
cd frontend && npm run dev          # Frontend at :5173 → open http://localhost:5173

# Option 4: Python API
python -c "
from forgedan import ForgeDAN_Engine, ForgeDanConfig
from forgedan.adapters import ModelAdapterFactory

adapter = ModelAdapterFactory.create_from_string('mock:test-model')
engine = ForgeDAN_Engine(ForgeDanConfig(max_iterations=3, population_size=3))
engine.set_target_llm(adapter.generate_sync)
result = engine.run('{goal}', 'test goal', 'target output')
print(f'Success: {result.success}, Fitness: {result.best_fitness:.4f}')
"
```

The first command sequence is the recommended smoke path for this repository:
it runs the no-model preflight, generates a complete report pack, validates the
machine-readable artifacts, checks manifest integrity, writes a QA receipt, and
packages the deliverable into a ZIP that can be verified after handoff.

---

## Documentation

- [LLM Security Assessment Landscape](docs/llm-security-landscape.md) — competitor scan and optimization priorities.
- [Staged Lint Roadmap](docs/lint-roadmap.md) — current CI lint gate, measured
  lint debt, and promotion plan for stricter quality gates.

### Attack Methods

| Method | Type | Description | Paper |
|--------|------|-------------|-------|
| **FORGEDAN** | Evolutionary | Multi-level mutation (char/word/sentence) + semantic fitness + dual-judge | [arXiv:2511.13548](https://arxiv.org/abs/2511.13548) |
| **AutoDAN** | Evolutionary | Hierarchical genetic algorithm for stealthy jailbreak prompts | [ICLR 2024](https://arxiv.org/abs/2310.04451) |
| **PAIR** | LLM-iterative | Black-box jailbreak via attacker-target LLM iteration (<20 queries) | [NeurIPS 2024](https://arxiv.org/abs/2310.08419) |
| **GCG** | Gradient-free | Greedy coordinate gradient adversarial suffix generation | [ICML 2023](https://arxiv.org/abs/2307.15043) |
| **Crescendo** | Multi-turn | Gradual escalation from benign to harmful content | [USENIX Security 2025](https://arxiv.org/abs/2404.01833) |
| **TAP** | Tree search | Tree-of-thought attack with pruning, 3-LLM collaboration | [NeurIPS 2024](https://arxiv.org/abs/2312.02119) |

### Model Adapters

<details>
<summary><b>18 supported providers (click to expand)</b></summary>

| Provider | Models | Config |
|----------|--------|--------|
| **OpenAI** | GPT-3.5, GPT-4, GPT-4o | `openai:gpt-4` |
| **Anthropic** | Claude 3 (Opus, Sonnet, Haiku) | `anthropic:claude-3-opus` |
| **Google** | Gemini Pro, Gemini Vision | `gemini:gemini-pro` |
| **DeepSeek** | DeepSeek-Chat, DeepSeek-Coder | `deepseek:deepseek-chat` |
| **Zhipu (智谱)** | GLM-4, GLM-3 | `zhipu:glm-4` |
| **Qwen (通义千问)** | Qwen-Max, Qwen-Plus | `qwen:qwen-max` |
| **Moonshot (月之暗面)** | Kimi | `moonshot:moonshot-v1-8k` |
| **Yi (零一万物)** | Yi-Large, Yi-Medium | `yi:yi-large` |
| **Baichuan (百川)** | Baichuan-4, Baichuan-3 | `baichuan:baichuan-4` |
| **Ollama** | Any local model | `ollama:llama2` |
| **vLLM** | High-perf local inference | `vllm:model-name` |
| **HuggingFace** | Any HF model | `huggingface:model-name` |
| **Mock** | Testing (no API key needed) | `mock:test-model` |

</details>

### Web Scanning

| Mode | Description | Use Case |
|------|-------------|----------|
| **URL Crawler** | Async crawling + content extraction (title, forms, links, scripts) | Gather attack material from target websites |
| **Security Scanner** | XSS, SQLi, directory traversal, security headers, HTTP methods | Traditional web vulnerability assessment |
| **LLM Interaction Test** | Indirect prompt injection via web content, evolutionary optimization | Test LLM safety when processing web content |

### Report Workflow

1. **Define scope** in a suite YAML file: cases, imported evidence sources, report metadata, policy gates, coverage requirements, acceptance criteria, reviewer decisions, and risk-register defaults.
2. **Run preflight** with `forgedan suite preflight` to catch missing metadata, weak handoff criteria, unresolved scorer names, missing provenance, and incomplete deterministic replay settings before spending provider budget.
3. **Generate the report pack** with `forgedan suite run`; the run writes raw and redacted machine-readable artifacts, Markdown/HTML reports, CSV matrices, coverage, risk register, release notes, and a manifest.
4. **Validate locally** with `forgedan suite validate-report` and `forgedan suite verify-bundle`; these checks bind schemas, hashes, summary counts, redacted artifacts, Markdown/HTML sidecars, and cross-artifact identities back to the source result.
5. **Prepare handoff** with `forgedan suite qa-report --strict-handoff`; the receipt records checklist status, blockers, acceptance criteria, source inventory, schema checks, and reviewer-facing evidence.
6. **Archive and verify** with `forgedan suite archive` and `forgedan suite verify-archive`; the same archive flow supports normal suite report packs and historical comparison packs.

### CLI Reference

```bash
forgedan run -g "goal" -m "provider:model"   # Run attack
forgedan run --quick -g "goal"                # Quick demo (3 iterations)
forgedan test -m "provider:model"             # Test model connectivity
forgedan suite run examples/smoke-suite.yml   # Run a reproducible YAML suite with prompt/response scans
forgedan suite run examples/smoke-suite.yml --run-id-dir # Archive under output/<run_id> to avoid overwrites
forgedan suite run examples/agent-tool-suite.yml # Generate an Agent/MCP/RAG report pack
forgedan suite run examples/tool-policy-suite.yml # Generate an expected policy-fail tool-policy pack
forgedan suite run examples/mcp-manifest-suite.yml # Import MCP tool metadata into report cases
forgedan suite run examples/mcp-trust-policy-suite.yml # Generate an expected policy-fail MCP trust pack
forgedan suite run examples/mcp-trust-calibrated-suite.yml # Apply a local MCP trust score policy file
forgedan suite run examples/model-artifact-suite.yml # Import local model artifacts into report evidence
forgedan suite run examples/model-serialization-suite.yml # Scan local model serialization files without loading them
forgedan suite run examples/coverage-policy-suite.yml # Enforce required coverage gates
forgedan suite run examples/duplicate-evidence-suite.yml # Demonstrate duplicate evidence grouping
forgedan suite run examples/report-metadata-suite.yml # Generate a report with formal assessment metadata
forgedan suite run examples/acceptance-criteria-suite.yml # Add report acceptance criteria/sign-off gates
forgedan suite run examples/ready-for-handoff-suite.yml # Generate a fully passing report handoff sample
forgedan suite run examples/review-decision-suite.yml # Document accepted risk / reviewer decisions
forgedan suite run examples/risk-register-owner-suite.yml # Pre-fill risk register owner/status/due date
forgedan suite run examples/cost-pricing-suite.yml # Estimate report usage cost from suite pricing inputs
forgedan suite run examples/custom-scorer-suite.yml # Run a suite-defined reusable contains scorer
forgedan suite run examples/cached-response-suite.yml # Replay repeat report runs from a local response cache
forgedan suite preflight examples/ready-for-handoff-suite.yml --output reports/preflight # Check report readiness before model execution
forgedan suite compare base.json curr.json    # Compare two suite-result.json artifacts
forgedan suite taxonomy --json                # Export report finding taxonomy
forgedan suite schemas --json                 # Export report artifact schema references
forgedan suite validate-report suite-result.json # Validate a report artifact contract
forgedan suite verify-bundle suite-manifest.json # Verify report pack checksums and schemas
forgedan suite archive suite-manifest.json --output handoff.zip # Zip a verified report or comparison pack
forgedan suite verify-archive handoff.zip # Verify an archived report pack
forgedan suite qa-report suite-manifest.json  # Write JSON/Markdown QA handoff receipt
forgedan suite qa-report suite-manifest.json --strict-handoff # Fail when readiness is not passed
forgedan report --input logs/attacks/          # Generate report
forgedan web                                  # Launch web dashboard
forgedan defense generate --input logs/        # Generate defense training data
forgedan info                                 # Show framework info
forgedan distributed coordinator              # Start distributed coordinator
```

Before spending time or provider budget on a report run, `forgedan suite
preflight <suite.yml>` performs a no-model readiness audit. It checks that the
suite has formal report metadata, handoff acceptance criteria, risk-register
owner/due-date defaults, policy/coverage gates, deterministic replay controls,
valid scorer names, source inventory provenance, MCP trust policy when MCP
manifests are imported, and an explicit model-serialization scope note when
heuristic artifact scanning is used. Add `--output <dir>` to write
`suite-preflight.json` and `suite-preflight.md`; `suite run` also includes the
same preflight artifacts in every generated report pack. The JSON artifact is
covered by `schemas/suite-preflight.schema.json` and can be validated with
`forgedan suite validate-report <dir>/suite-preflight.json`. The command exits
non-zero only for failed checks by default; add `--strict` to also fail on
`review_required` items, or `--json` to print the audit for CI/archive scripts.

Suites can keep cases inline or load a reusable case file:

```yaml
cases_file: examples/cases/prompt-injection-mini.jsonl
scorers:
  - target_prefix
  - refusal
  - response_safety
```

Suites can also define lightweight reusable deterministic scorers. A `contains`
scorer records whether the model response includes required reviewer-facing text
and stores the scorer output in each case result, the case matrix, and score
summary.

```yaml
scorers:
  - refusal_phrase_present
scorer_definitions:
  - name: refusal_phrase_present
    type: contains
    text: cannot help
```

When a suite imports `cases_file`, `mcp_manifest_file`, or
`model_artifact_files`, reports include a Source Inventory section with each
input path, SHA256, byte size, and generated case count. The same inventory is
stored in `suite-config.json` for audit replay and handoff checks, and the
report schemas require it in both `suite-config.json` and the embedded
`suite-result.json` configuration snapshot. `validate-report` also checks that
the report Source Inventory counts match its entries and that the embedded
suite configuration snapshot matches the report section.

Suites can include formal report metadata for assessment handoff. These fields
flow into `suite-config.json`, `suite-result.json`, and the Markdown/HTML report
metadata section. The public redacted report replaces client, author, and
reviewer names with stable placeholders.

```yaml
report_metadata:
  assessment_id: LLM-REPORT-001
  report_title: LLM Security Assessment Report
  client: Example Corp
  authors:
    - Security Assessment Team
  reviewers:
    - Report QA Lead
  classification: Confidential
  assessment_start: "2026-05-01"
  assessment_end: "2026-05-31"
```

Suites can also define report acceptance criteria for QA and sign-off workflows.
Each item is carried into `suite-config.json`, `suite-result.json`, Markdown/HTML
reports, and the QA receipt. A failed item blocks `ready_for_handoff`, while
`review_required` keeps the acceptance section visible without marking the
bundle as fully accepted. Acceptance criteria whose IDs match handoff checklist
items, such as `residual-risk-owner-signoff`, `raw-artifact-handling`, and
`limitations-reviewed`, can also turn those QA receipt items from
`review_required` into `passed` when the criterion is marked `passed` or
`accepted_risk`.

```yaml
acceptance_criteria:
  - id: evidence-reviewed
    title: Evidence matrix reviewed
    status: passed
    owner: QA Lead
    evidence: suite-evidence.csv
    notes: Evidence rows sampled against the Markdown report.
  - id: residual-risk-owner-signoff
    title: Residual risk owner sign-off complete
    status: review_required
    owner: Risk Owner
    evidence: suite-risk-register.json
    notes: Awaiting final residual risk owner approval.
  - id: raw-artifact-handling
    title: Raw artifact handling reviewed
    status: passed
    owner: QA Lead
    evidence: Raw prompts and responses restricted to authorized reviewers.
  - id: limitations-reviewed
    title: Limitations reviewed
    status: passed
    owner: QA Lead
    evidence: Report limitations match the scoped assessment.
```

Policy failures can be paired with reviewer decisions without changing
`policy_passed`. This gives the report pack a decision log for accepted risk,
approvals, required mitigations, or rejected exceptions, and the QA receipt
records whether policy exceptions have documented decisions.

```yaml
review_decisions:
  - id: accept-demo-residual-risk
    title: Accept demo residual risk for report pack
    status: accepted_risk
    owner: QA Lead
    related_policy_violations:
      - max_risk_score
    related_cases:
      - injection-case
    evidence: Assessment owner accepted this residual risk for a controlled report demo.
    notes: Re-review before external publication.
```

Risk registers can be pre-filled with suite-level remediation tracking defaults.
These values flow into `suite-risk-register.json` and `suite-risk-register.csv`
for each generated finding, so the report pack can be handed to the owner
without manually editing blank tracking columns first.

```yaml
risk_register_defaults:
  owner: AppSec Team
  status: open
  due_date: "2026-06-30"
```

Suites can include externally maintained model pricing inputs for reproducible
usage cost estimates. ForgeDAN does not fetch live prices; the report records
the source string you provide and computes `estimated_cost_usd` from observed
prompt and completion tokens. You can keep rates inline, or point the suite at
a local JSON/YAML pricing catalog. Catalog files are included in Source
Inventory with SHA256 and size metadata so report reviewers can audit the price
source used for cost calculations.

```yaml
usage_pricing:
  prompt_usd_per_1k_tokens: 0.01
  completion_usd_per_1k_tokens: 0.02
  source: pricing-sheet-v1
```

```yaml
usage_pricing_file: usage-pricing-catalog.yml
```

```yaml
# usage-pricing-catalog.yml
models:
  mock:test-model:
    prompt_usd_per_1k_tokens: 0.01
    completion_usd_per_1k_tokens: 0.02
    source: example-provider-pricing-sheet
```

For repeatable report reruns, suites can write and replay model responses from
a local JSON cache. Cache keys are derived from the model name and prompt
SHA256, so raw prompt bodies are not stored in the cache file. Cached entries do
store model outputs and usage metadata, so treat the cache as restricted report
evidence. Paths are resolved relative to the suite YAML file. Pair the cache
with `random_seed` when you want repeated evolutionary prompts to replay
deterministically across CLI runs.

```yaml
response_cache_file: .cache/smoke-response-cache.json
random_seed: 1337
```

Reports include a Response Cache section with hits, misses, stored entries, and
whether the cache file was updated during the run.

Suites can import MCP server/tool manifests and turn each tool description into
a deterministic report case. The importer recursively reads `tools` arrays from
JSON or YAML manifests, names cases as `mcp-tool-*`, and keeps the manifest
source visible in report scope and `suite-config.json`. Imported cases also
carry structured provenance metadata (`source_type`, `manifest_file`,
`tool_name`, server trust fields, annotation keys, annotation hashes, and
`description_sha256`) in `suite-cases.jsonl` and `suite-case-matrix.csv`.
Nested MCP `annotations` fields are included in the normalized tool text so
malicious metadata buried under schemas or metadata blocks is still reportable.
Each imported MCP case also carries a heuristic `server_trust_score`, and the
Markdown/HTML report includes an MCP Trust Summary with tier counts, highest
score, affected cases, server names, and the score model rationale used to
interpret each tier.

```yaml
mcp_manifest_file: examples/mcp-server-manifest.json
mcp_manifest_case_category: mcp-manifest
```

MCP manifests can also be gated by server trust tier. When
`allowed_mcp_trust_tiers` is configured, imported MCP cases with missing or
unapproved `server.trust.tier` metadata become policy violations while the run
still writes the full report pack for reviewer evidence.

```yaml
policy:
  allowed_mcp_trust_tiers:
    - internal
    - approved
```

MCP trust scores and rationale can be calibrated with a local JSON/YAML policy
file. The policy file is included in Source Inventory with SHA256 and byte size,
and the custom score model flows into case metadata plus the MCP Trust Summary.

```yaml
mcp_trust_policy_file: mcp-trust-policy.yml
```

```yaml
# mcp-trust-policy.yml
tiers:
  third_party:
    score: 0.72
    rationale: External vendor MCP server pending procurement review.
```

Suites can import local UTF-8 model artifact files, such as a model card,
README, config export, or release note fragment, and turn each artifact into a
deterministic report case. Paths are resolved relative to the suite YAML file.
Imported artifact cases are named `model-artifact-*`, scanned by the same
prompt/response detectors as normal cases, and keep structured provenance
metadata (`source_type`, `artifact_file`, `artifact_sha256`, and
`artifact_bytes`) in `suite-cases.jsonl` and `suite-config.json`.

```yaml
model_artifact_files:
  - model-artifacts/local-model-card.md
model_artifact_case_category: model-artifact
```

Suites can also scan local model serialization files without loading them. This
is intentionally a static report signal, not a full ModelScan replacement: it
looks at extensions, magic bytes, and archive metadata to flag pickle, PyTorch,
checkpoint, ONNX, opaque binary, GGUF, and safetensors artifacts for reviewer
handoff. Each scanned file is added to Source Inventory with SHA256 and byte
size, and reports include a Model Serialization Artifacts table with risk level
and recommendation.

```yaml
model_serialization_files:
  - model-artifacts/risky-model.pkl
  - model-artifacts/weights.safetensors
```

Policy gates can require minimum report coverage, not just low risk. Missing
case categories, policy domains, or OWASP LLM IDs become policy violations and
are surfaced in reports and QA receipts.

```yaml
policy:
  required_case_categories:
    - prompt-injection
    - agent-tooling
  required_policy_domains:
    - Instruction Integrity
    - Tool Governance
  required_owasp_llm_ids:
    - LLM01
    - LLM06
```

Agent and RAG suites can also declare a lightweight tool permission policy. When
`require_destination_allowlist` is enabled, unapproved `http://` or `https://`
destinations in a best prompt become `tool_policy_violation` findings and fail
the suite policy gate so the report records the exception.

```yaml
tool_policy:
  require_destination_allowlist: true
  allowed_domains:
    - internal.example
  blocked_domains:
    - attacker.example
  blocked_actions:
    - export_data
```

Suite files can include CI gates. Each run writes `suite-result.json`,
`suite-cases.jsonl`, `suite-evidence.csv`, `suite-case-matrix.csv`,
`suite-risk-register.json`, `suite-risk-register.csv`,
`suite-coverage.json`, `suite-coverage.csv`, `suite-config.json`,
`suite-report.html`, `suite-report.md`, redacted publication copies
(`suite-result-redacted.json`, `suite-cases-redacted.jsonl`,
`suite-report-redacted.html`, `suite-report-redacted.md`),
`suite-preflight.json`, `suite-preflight.md`, `suite-release-notes.md`, `suite-public-bundle.md`,
`suite-report-bundle.md`, and `suite-manifest.json`, including per-case scores
and aggregate score summaries, run IDs, case trace IDs, UTC timestamps, runtime
environment metadata, and latency. The manifest also records a structured report acceptance summary for
automation-friendly archive and handoff checks. Formal `report_metadata` lets
the same report pack carry assessment ID,
title, client, author/reviewer, classification, and assessment window context.
`acceptance_criteria` adds a reviewer-facing sign-off matrix that can block QA
handoff when required report checks fail.
Findings carry stable `evidence_fingerprint` values derived from
finding kind, source, and evidence text so reports can group duplicate evidence
across cases without relying on raw prompt text. `suite-config.json` preserves
the normalized suite inputs, including
budgets, scorers, policy thresholds, pricing catalog references, and case definitions for audit replay. The
raw JSON/JSONL artifacts preserve prompt/response bodies for authorized audit replay; the
redacted publication artifacts replace raw `best_prompt`, `best_response`, and
finding evidence text with SHA256-based placeholders while masking secret,
connection-string, and email metadata. The case matrix CSV gives reviewers a flat case-level coverage/risk
table with success state, risk scores, scanner finding counts, token usage,
OWASP LLM categories, scorer output, and trace IDs. The risk register JSON/CSV
turn normalized findings into an owner/status remediation tracker with optional
suite-level default owner, status, and due date values, plus evidence hashes and
reviewer-stable evidence fingerprints instead of raw evidence text.
The coverage JSON/CSV summarize case category, policy-domain, taxonomy-category,
and OWASP LLM coverage so reviewers can see what was tested and where coverage
is thin.

#### Report Pack Anatomy

| Artifact | Audience | Purpose |
|----------|----------|---------|
| `suite-report.md` / `suite-report.html` | Authorized reviewers | Full narrative report with scope, methodology, findings, coverage, risk, usage, and limitations. |
| `suite-result.json` / `suite-cases.jsonl` | Authorized reviewers | Raw machine-readable run summary and per-case traces for audit replay. |
| `suite-evidence.csv` | Authorized reviewers | Flat finding evidence table with taxonomy IDs, confidence, severity rationale, evidence fingerprints, OWASP LLM mapping, and recommendations. |
| `suite-case-matrix.csv` | External reviewers | Case-level outcome, risk, usage, scorer, metadata, and OWASP coverage matrix. |
| `suite-risk-register.json` / `suite-risk-register.csv` | Assessment team | Remediation tracker with owner/status fields, severity rationale, evidence hashes, and evidence fingerprints. |
| `suite-coverage.json` / `suite-coverage.csv` | External reviewers | Coverage summary by case category, policy domain, taxonomy category, OWASP LLM category, and gap signals. |
| `suite-config.json` | Assessment team | Normalized suite input snapshot, including report metadata, policy thresholds, tool policy, imported source inventory, imported MCP manifest source, and imported model artifact sources. |
| `suite-preflight.json` / `suite-preflight.md` | Assessment team | Run-before-use readiness audit for report metadata, acceptance gates, risk defaults, policy gates, deterministic replay, and source provenance. |
| `suite-release-notes.md` | Authorized reviewers | Concise reviewer-facing run notes with policy, risk, acceptance, source inventory, reviewer-decision, MCP trust, and artifact pointer summaries. |
| Redacted report/result/cases artifacts | External reviewers | Lower-sensitivity publication pack with prompts, responses, and evidence redacted. |
| `suite-manifest.json` | Assessment team | Integrity manifest with sizes, SHA256 hashes, schema references, sensitivity, audience classifications, and report acceptance status. |
| `suite-qa-receipt.json` / `suite-qa-receipt.md` | Assessment lead | Handoff receipt covering manifest, checksums, schemas, cross-artifact consistency, preflight readiness, release notes, source inventory, coverage review, publication pack, policy gate, residual risk owner sign-off, and limitations. |

Reports also include an executive summary, normalized findings list,
stable finding taxonomy IDs, severity/kind/source finding summaries,
policy-domain buckets, OWASP LLM Top 10 categories, report priorities,
remediation recommendations, detector confidence, duplicate evidence groups,
formal report metadata, scope, source inventory, methodology, severity rationale, token/latency usage summaries when adapters expose usage
metadata, limitations, and overall risk level. Cost is left unestimated unless
you provide `usage_pricing` values or a `usage_pricing_file` catalog in the suite. Reports and QA receipts include ForgeDAN, Python, OS, and
platform metadata for reproducibility. The CLI prints the finding summary, usage
totals, and manifest path after each run so CI logs show the total,
highest-severity issue, token consumption, and the artifact integrity manifest.
When a policy is violated, `forgedan suite run` still writes all artifacts and
exits with code `1`.
Deterministic prompt/response scanners currently flag prompt-injection markers,
system prompt leakage references, jailbreak roleplay framing, secret,
connection-string, or email exposure, imported model artifact leakage, Agent/MCP tool data-exfiltration
instructions that ask tool workflows to forward retrieved data externally,
malicious tool metadata that attempts
to override agent safety policy or force tool calls before answering, configured
tool permission policy violations, and indirect prompt injection in untrusted
retrieved web, RAG, or document content.
The full bundle index gives reviewers a single Markdown handoff page for the
generated report files, evidence matrix, case matrix, redacted publication pack,
release notes, integrity manifest, schema contracts, and a handoff summary
covering policy violations, risk count, acceptance status, reviewer decisions,
MCP trust, and imported source counts. Full release notes and the full bundle
index also include the Source Inventory table with imported source paths,
SHA256 hashes, byte counts, and generated case counts.
`suite-public-bundle.md` is the
lower-sensitivity handoff index for external sharing. The manifest also records
artifact sensitivity/audience classifications plus the JSON Schema IDs and local
schema paths for the core report artifact types, along with acceptance status
and criteria count. Use
`forgedan suite verify-bundle <suite-manifest.json>` before handoff to re-check
artifact existence, size, SHA256, and JSON schema contracts for the generated
report pack.
Use `forgedan suite archive <suite-manifest.json> --output handoff.zip` or
`forgedan suite archive <comparison-manifest.json> --output comparison.zip`
after bundle verification to produce a single ZIP handoff artifact containing
the manifest and declared report files. Use `forgedan suite verify-archive
handoff.zip` after copying or sharing the archive to re-check the embedded
manifest schema, archived JSON artifact schemas, and every archived member's
size and SHA256.

Use `forgedan suite taxonomy` for a readable taxonomy table with internal IDs
and OWASP LLM mappings, or `forgedan suite taxonomy --json` when attaching the
taxonomy to another report pipeline.

JSON Schema contracts for report artifacts live in `schemas/`:
`suite-result.schema.json`, `suite-config.schema.json`, `suite-manifest.schema.json`,
`suite-comparison.schema.json`, `suite-comparison-manifest.schema.json`,
`suite-qa-receipt.schema.json`,
`suite-preflight.schema.json`, `suite-risk-register.schema.json`,
`suite-coverage.schema.json`, and `finding-taxonomy.schema.json`.
Use `forgedan suite schemas` or `forgedan suite schemas --json` to list the
schema IDs and target artifacts from the CLI. Use
`forgedan suite validate-report <artifact.json>` before sharing a report pack;
the command infers the schema from standard artifact names or recognizable
payload shape, and still accepts `--schema suite-result` when you want to be
explicit. Beyond JSON Schema checks, `validate-report` also recalculates
cross-field report semantics such as Source Inventory totals, embedded source
inventory snapshots, usage-cost estimates against configured pricing inputs,
risk-register counts, risk row `run_id` alignment, and duplicate `risk_id`
values. It also checks `suite-preflight.json` summary/status/blocker/score
consistency, and when `suite-config.json` is in the same directory it rebuilds
the expected preflight audit from that config snapshot to catch hand-edited
check evidence or statuses. It also checks manifest artifact/schema counts and
duplicate manifest artifact paths or schema names, plus coverage case/finding
totals across case-category, policy-domain, taxonomy-category, and OWASP LLM
coverage summaries. For `suite-comparison.json`, semantic validation checks
regression counts, policy-domain delta arithmetic, and sibling Markdown, HTML,
and bundle sidecars when they exist, so historical comparison reports cannot
drift from the machine-readable regression result.
Use `forgedan suite verify-bundle <suite-manifest.json>` to validate the whole
suite report pack against its integrity manifest after copying or archiving it.
The bundle verifier also checks cross-artifact consistency for key report
evidence, including the `suite-config.json` audit replay snapshot, run IDs,
suite/model identity, and risk-register and coverage counts against
`suite-result.json`. It also binds `suite-result-redacted.json` back to the raw
result run identity, case counts, risk metrics, and policy pass status, and
checks both raw and redacted per-case JSONL streams plus `suite-case-matrix.csv`
against the suite result case IDs, trace IDs, and execution counters. It also
scans redacted/public artifacts for secret-, email-, or connection-string-bearing
raw `best_prompt`, `best_response`, and finding `evidence` text from the
restricted result, so synchronized-hash publication packs cannot reintroduce
high-risk restricted evidence into external deliverables. The
evidence matrix is bound back to `suite-result.json` findings,
`suite-risk-register.csv` is bound back to `suite-risk-register.json` risks, and
`suite-coverage.csv` is bound back to `suite-coverage.json` coverage rows.
Reviewer-facing `suite-release-notes.md` summary lines are also bound back to
`suite-result.json` policy, risk, acceptance, source inventory, reviewer
decision, and MCP trust values, and the full/public bundle indexes get the same
summary binding. `suite-preflight.md` is bound back to `suite-preflight.json`
status, score, summary counts, blockers, and check-table evidence/action rows.
The full and redacted Markdown/HTML report bodies are also
checked for required report sections plus policy, risk, case-count, usage,
token, and acceptance summary lines. A
synchronized-hash publication pack therefore cannot silently point reviewers at
a different narrative report summary, redacted summary, case stream, case
matrix, evidence table, remediation tracker, coverage matrix, preflight
readiness note, release notes summary, bundle index summary, or narrative report
with missing handoff sections.
Use `forgedan suite qa-report <suite-manifest.json>` at handoff time to write
`suite-qa-receipt.json` and `suite-qa-receipt.md`, which summarize manifest
validity, manifest size/SHA256 binding, artifact checksums, schema validations, cross-artifact consistency, a handoff checklist, errors,
configured report acceptance criteria, release notes, source inventory, risk-register owner/due-date
assignment, residual risk owner sign-off, reviewer decisions, preflight
readiness, redacted-publication leak status, and readiness for handoff. The receipt also includes a
`handoff_readiness` score that aggregates passed, failed, and review-required
handoff checklist items without changing the legacy receipt `status` field.
The JSON receipt also carries a structured `cross_artifact_consistency` object
with checked artifact names, error count, and error details for CI or archive
review scripts, while the Markdown receipt renders the same consistency summary
for human handoff review.
When `suite-qa-receipt.md` sits beside `suite-qa-receipt.json`,
`validate-report` binds the reviewer-facing Markdown back to the JSON receipt
summary, readiness, checklist, artifact, schema, and error rows so hand-edited
receipt sidecars fail before report handoff.
Add `--strict-handoff` when using `qa-report` as a final handoff gate; this
keeps the default receipt-generation behavior but returns a non-zero exit code
when `handoff_readiness.status` is `failed` or `review_required`.
`validate-report` recalculates this readiness summary from the checklist so
tampered status, counts, scores, or blockers fail validation.
It also checks the structured `cross_artifact_consistency` object against the
handoff checklist status and error count, so receipt JSON cannot claim a
different consistency result than the reviewer-facing checklist. QA receipt
validation also recomputes top-level artifact, schema-validation, and error
counts, per-schema-validation row error counts and validity, plus the legacy
`valid` and `status` summaries. It also recomputes QA receipt acceptance
summaries from artifact/schema validation details and, when available, the
referenced `suite-result.json` report acceptance section.
When the referenced
manifest file is available locally, `validate-report` also recomputes the
receipt's manifest identity fields, `manifest_size_bytes`, and `manifest_sha256`
binding, rechecks the top-level verification summary and `schema_validations`
rows plus `cross_artifact_consistency` details against current manifest
verification output, then rechecks the `checked_artifacts` rows against current
manifest verification output, the manifest artifact list,
sensitivity/audience classifications, and locally available row existence, size,
SHA256, and error details.
Failed acceptance criteria mark the QA receipt as
failed even when bundle integrity checks pass. The JSON receipt is also covered by
`schemas/suite-qa-receipt.schema.json`, so CI can validate it with
`forgedan suite validate-report <qa-dir>/suite-qa-receipt.json` before upload;
the schema pins known handoff checklist IDs so typoed receipt items fail
validation instead of drifting into review automation, and semantic validation
requires every known handoff checklist item to appear exactly once. When the
manifest is available locally, `validate-report` also regenerates the expected
checklist status, evidence, and action text from the current report pack so
manual checklist edits fail validation.

Historical runs can be compared with `forgedan suite compare`. The comparison
writes the requested JSON artifact plus Markdown, HTML, bundle, and manifest
sidecar reports with metric deltas, policy-domain deltas, regression summary,
evidence, checksum index, schema references, and appendix sections.
`validate-report <comparison.json>` also checks regression counts,
policy-domain delta arithmetic, and any sibling comparison Markdown/HTML/bundle
sidecars before the comparison is archived. `validate-report
<comparison-manifest.json>` rechecks the comparison artifact hashes and binds the
manifest summary back to the comparison JSON. Add
`--fail-on-regression` to use the comparison as a regression gate in CI.

```yaml
policy:
  max_attack_success_rate: 0.0
  max_response_findings: 0
  max_risk_score: 0.8
```

### API Endpoints

<details>
<summary><b>REST API reference (click to expand)</b></summary>

```
# Attacks
POST   /api/attacks/run              Start attack (supports method selection)
GET    /api/attacks/methods           List all attack methods + param schemas
GET    /api/attacks/status/<id>       Task status
DELETE /api/attacks/<id>              Cancel task
POST   /api/attacks/batch             Batch testing
POST   /api/attacks/compare           Model comparison

# Models
GET    /api/models                    List all available adapters
POST   /api/models/test               Test model connectivity
GET    /api/models/<provider>/params   Get model parameter schema

# Web Scanning
POST   /api/webscan/crawl             URL crawling
POST   /api/webscan/scan              Security scanning
POST   /api/webscan/llm-test          LLM-driven interaction testing

# Reports
GET    /api/reports                    List reports
GET    /api/reports/<id>               Report details
GET    /api/reports/compare            Compare reports
POST   /api/reports/export             Export PDF/CSV

# Datasets
GET    /api/datasets                   List datasets
POST   /api/datasets/upload            Upload custom dataset
GET    /api/datasets/<name>/preview    Preview dataset

# Monitoring
GET    /api/monitoring/health          Health check
GET    /api/monitoring/metrics         System metrics
```

</details>

---

## Report Outputs

The main deliverable is a verified report bundle rather than an application
screen. A normal suite run can produce:

| Output | Why it matters |
|--------|----------------|
| `suite-report.md` / `suite-report.html` | Reviewer-facing narrative report with scope, methodology, evidence, risks, coverage, usage, and limitations. |
| `suite-evidence.csv` / `suite-case-matrix.csv` | Flat tables for evidence review, traceability, coverage checks, and downstream spreadsheet workflows. |
| `suite-risk-register.json` / `suite-risk-register.csv` | Remediation tracker with owners, due dates, severity rationale, and stable evidence fingerprints. |
| `suite-coverage.json` / `suite-coverage.csv` | Coverage summary by case category, policy domain, taxonomy category, and OWASP LLM category. |
| `suite-release-notes.md` / `suite-report-bundle.md` | Compact handoff notes and artifact index for reviewers. |
| `suite-qa-receipt.json` / `suite-qa-receipt.md` | Handoff receipt with schema, checksum, cross-artifact, acceptance, and readiness checks. |
| `handoff.zip` | Single-file archive that can be verified after copying or sharing. |

---

## Project Structure

```
LLM-Security-Assessment-Framework/
├── forgedan/                  # Python package
│   ├── api/                   # Flask Blueprint REST API (8 modules)
│   ├── attacks/               # 6 attack algorithms + registry
│   ├── adapters/              # 18 model adapters
│   ├── webscan/               # Web security testing (crawler/scanner/llm_tester)
│   ├── datasets/              # Dataset management (AdvBench, custom)
│   ├── defense/               # Defense training data generation
│   ├── distributed/           # Distributed computing (coordinator/worker)
│   ├── monitoring/            # Prometheus metrics & alerting
│   ├── multimodal/            # Vision model attacks
│   ├── web/                   # Legacy Flask web app
│   ├── suite.py               # Suite runner, report pack writer, validators, archive verifier
│   ├── scanners.py            # Deterministic prompt/response/tool/model scanners
│   ├── scorers.py             # Deterministic suite scorer helpers
│   ├── finding_taxonomy.py    # Stable finding taxonomy + OWASP LLM mappings
│   ├── engine.py              # Evolutionary algorithm engine
│   ├── mutator.py             # 15 mutation strategies + MAB selection
│   ├── fitness.py             # Semantic similarity fitness
│   ├── judge.py               # Dual-judge mechanism
│   ├── config.py              # Configuration management
│   ├── cli.py                 # CLI interface
│   └── utils.py               # Utilities (retry, cache, circuit breaker)
├── frontend/                  # Vue 3 SPA dashboard
│   └── src/
│       ├── views/             # 7 pages
│       ├── components/        # Reusable UI components
│       ├── stores/            # Pinia state management
│       └── api/               # API client + WebSocket
├── schemas/                   # JSON Schema contracts for generated report artifacts
├── examples/                  # Runnable suite examples, case fixtures, MCP/model fixtures
├── docs/                      # Landscape scan, lint roadmap, repository metadata guidance
├── tests/                     # Pytest test suite (257 passed / 4 skipped locally)
├── monitoring/                # Prometheus/Grafana configs
├── reports/                   # Generated assessment reports (ignored by Git except checked-in fixtures)
├── pyproject.toml             # Python package config
├── .env.example               # Environment variable template
└── LICENSE                    # MIT License
```

---

## Development

### Setup Dev Environment

```bash
pip install -e ".[dev]"
cd frontend && npm install
```

### Run Tests

```bash
pytest tests/ -v                  # Run all tests
pytest tests/test_engine.py -v    # Run specific module
pytest --cov=forgedan tests/      # With coverage
```

### Code Quality

```bash
flake8 forgedan/ --select=E9,F63,F7,F82,E722,F401,F841 --show-source --statistics
black --check forgedan tests
```

Both commands match blocking CI quality gates. See
[docs/lint-roadmap.md](docs/lint-roadmap.md) for the staged cleanup history.

### Build Frontend

```bash
cd frontend
npm run dev                       # Dev server with hot reload
npm run build                     # Production build → dist/
```

---

## Roadmap

- [x] Core evolutionary engine with 15 mutation strategies
- [x] 6 attack methods (FORGEDAN, AutoDAN, PAIR, GCG, Crescendo, TAP)
- [x] Model adapters for hosted, Chinese, local, vLLM, HuggingFace, vision, and mock targets
- [x] YAML suite runner with imported cases, custom scorers, response cache replay, source inventory, and policy gates
- [x] Deterministic scanners for prompt injection, jailbreak framing, system prompt leakage, secrets/PII, Agent/MCP/tool policy risk, and model artifact signals
- [x] Report pack generation with Markdown/HTML reports, redacted publication artifacts, evidence matrices, case matrices, risk registers, coverage summaries, release notes, and bundle indexes
- [x] JSON Schema contracts, semantic artifact validation, manifest verification, cross-artifact consistency checks, QA receipts, and archive verification
- [x] CI gates for unit tests, preflight, smoke report pack validation, ready-for-handoff QA, selected flake8 rules, Black, and frontend build
- [ ] Add optional in-archive cross-artifact verification parity with directory-based `verify-bundle`
- [ ] Add more real-world Agent/MCP manifest fixtures to calibrate trust scoring and policy defaults
- [ ] Add benchmark-style examples for HarmBench/JailbreakBench only where they improve report evidence quality
- [ ] Add deeper model serialization analysis if the report scope requires more than lightweight static heuristics
- [ ] Publish rendered sample report packs for reviewers who want to inspect output before running the CLI

---

## Citation

If you use FORGEDAN in your research, please cite:

```bibtex
@article{cheng2025forgedan,
  title={FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models},
  author={Cheng, Siyang and Liu, Gaotian and Mei, Rui and Wang, Yilin and Zhang, Kejia and Wei, Kaishuo and Yu, Yuqi and Wen, Weiping and Wu, Xiaojie and Liu, Junhua},
  journal={arXiv preprint arXiv:2511.13548},
  year={2025}
}
```

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

---

## Security

For security vulnerabilities, please see [SECURITY.md](SECURITY.md) or use [GitHub Security Advisories](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/security/advisories/new).

**Disclaimer**: This tool is designed for authorized security testing and research purposes only. Always obtain proper authorization before testing any system. The authors are not responsible for any misuse.

---

## License

This project is licensed under the MIT License — see [LICENSE](LICENSE) for details.

---

## 中文完整说明

### 项目定位

**FORGEDAN** 基于论文 [*FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models*](https://arxiv.org/abs/2511.13548)，但当前项目重点已经从单纯的越狱算法演示扩展为 **LLM 安全评估报告交付框架**。

它面向授权安全评估、研究复现和报告交付场景，帮助评估团队生成可审计、可复核、可交接的报告包：YAML 套件、确定性扫描器与评分器、证据矩阵、风险登记、覆盖率摘要、JSON Schema 合约、QA 回执、脱敏发布包，以及复制或分享后仍可重新校验的 ZIP 归档。

项目仍保留进化式越狱攻击、模型适配器、WebScan、REST API 和 Vue 仪表盘；但当前目标不是商业化平台，而是让报告证据、审计链路和交付质量更稳。

### 核心能力

| 能力 | English | 中文说明 |
|------|---------|----------|
| Report Suites | YAML suite definitions, imported cases, replay caches, deterministic seeds, policy gates, preflight checks | YAML 套件、导入用例、响应缓存、确定性种子、策略门禁、运行前预检 |
| Report Artifacts | Markdown/HTML reports, evidence CSVs, risk registers, coverage summaries, release notes | Markdown/HTML 报告、证据矩阵、风险登记、覆盖率摘要、发布说明 |
| Evidence Integrity | JSON Schemas, manifests, SHA256/size checks, cross-artifact consistency | JSON Schema、制品清单、SHA256/大小校验、跨制品一致性校验 |
| Handoff QA | QA receipts, acceptance criteria, reviewer decisions, owner/due-date tracking | QA 回执、验收准则、评审决策、风险 owner 与到期日 |
| Assessment Coverage | Prompt injection, jailbreak framing, secret/PII exposure, Agent/MCP/tool risk, model artifact signals | Prompt Injection、越狱框架、敏感信息/PII、Agent/MCP/工具风险、模型制品信号 |
| Baseline Engine | FORGEDAN, AutoDAN, PAIR, GCG, Crescendo, TAP, model adapters, WebScan, API, dashboard | 多种攻击算法、模型适配器、WebScan、API 和仪表盘能力 |

### Repository About 建议

GitHub 仓库侧栏建议使用：

> 面向报告交付的 LLM 安全评估框架，用于生成可复现红队套件、证据包、QA 回执、Schema 合约和可校验归档。

对应英文：

> Report-first LLM security assessment framework for reproducible red-team suites, evidence packs, QA receipts, schemas, and archive verification.

建议 Topics：

`llm-security`, `ai-red-team`, `prompt-injection`, `jailbreak`, `owasp-llm`, `mcp-security`, `agent-security`, `security-reporting`, `risk-register`, `audit-evidence`, `json-schema`, `pytest`, `python`

### 架构概览

```text
forgedan/
├── suite.py              # 报告套件运行器、报告包写入、验证、QA 回执、归档校验
├── scanners.py           # 确定性 prompt/response/tool/model-artifact 扫描器
├── scorers.py            # 可复用确定性评分器
├── finding_taxonomy.py   # 稳定 finding ID、分类、优先级和 OWASP LLM 映射
├── attacks/              # 6 种攻击算法与统一注册表
├── adapters/             # OpenAI、Anthropic、Gemini、DeepSeek、Qwen、Ollama、vLLM、HuggingFace、Mock 等
├── api/                  # Flask Blueprint REST API
├── webscan/              # 爬虫、Web 安全扫描、LLM 交互测试
├── engine.py             # 进化算法引擎
├── mutator.py            # 15 种变异策略与 MAB 选择
├── fitness.py            # 语义相似度适应度评估
└── judge.py              # 双重判断机制

schemas/                  # 报告制品 JSON Schema 合约
examples/                 # 可运行套件样例、case/MCP/model fixture
docs/                     # 竞品扫描、lint roadmap、仓库 About 建议
tests/                    # pytest 覆盖 suite/report/scanner/schema 行为
frontend/                 # Vue 3 SPA 仪表盘
```

### 使用截图

下面的截图来自 `examples/ready-for-handoff-suite.yml` 生成的真实报告交付链路，展示当前项目最核心的报告包、QA 回执和归档校验能力。

#### 报告包总览

![报告包总览](docs/screenshots/report-overview.png)

#### QA 交接回执

![QA 交接回执](docs/screenshots/qa-receipt.png)

#### 归档校验

![归档校验](docs/screenshots/archive-verification.png)

### 快速开始

#### 前置要求

- Python >= 3.9
- Node.js >= 18，只有运行前端时需要
- Git

#### 安装

```bash
git clone https://github.com/Coff0xc/LLM-Security-Assessment-Framework.git
cd LLM-Security-Assessment-Framework

# 后端最小安装
pip install -e .

# Web dashboard + WebScan 依赖
pip install -e ".[web]"

# 全量依赖
pip install -e ".[all]"

# 前端
cd frontend
npm install
```

#### 生成可交付报告包

下面这组命令是当前项目最推荐的 smoke path：先做无模型预检，再生成报告包，随后校验制品、生成 QA 回执、打包 ZIP，并在交付后重新校验归档。

```bash
forgedan suite preflight examples/ready-for-handoff-suite.yml --strict --output reports/preflight-ready
forgedan suite run examples/ready-for-handoff-suite.yml --output reports/suite-ready
forgedan suite validate-report reports/suite-ready/suite-result.json
forgedan suite verify-bundle reports/suite-ready/suite-manifest.json
forgedan suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff
forgedan suite archive reports/suite-ready/suite-manifest.json --output reports/suite-ready/handoff.zip
forgedan suite verify-archive reports/suite-ready/handoff.zip
```

#### 运行攻击 Demo

```bash
forgedan run --quick -g "test prompt" -m mock:test
```

#### 运行 Web Dashboard

```bash
forgedan web
cd frontend
npm run dev
```

后端默认在 `:5000`，前端默认在 `:5173`。

### 报告工作流

1. **定义评估范围**：在 suite YAML 中配置 cases、导入证据源、报告元数据、策略门禁、覆盖率要求、验收准则、评审决策和风险登记默认值。
2. **运行预检**：使用 `forgedan suite preflight` 在消耗模型预算前检查元数据、交接准则、scorer 名称、来源证明和确定性 replay 设置。
3. **生成报告包**：使用 `forgedan suite run` 写出原始与脱敏 JSON/JSONL、Markdown/HTML 报告、CSV 矩阵、覆盖率、风险登记、发布说明和 manifest。
4. **本地验证**：使用 `forgedan suite validate-report` 与 `forgedan suite verify-bundle` 校验 schema、hash、摘要计数、脱敏制品、Markdown/HTML sidecar 与跨制品身份。
5. **准备交接**：使用 `forgedan suite qa-report --strict-handoff` 生成 QA 回执，记录 checklist、blocker、验收准则、Source Inventory、schema 校验和人工评审证据。
6. **归档并复核**：使用 `forgedan suite archive` 和 `forgedan suite verify-archive` 生成单文件 ZIP，并在复制或分享后重新校验。普通报告包和历史对比报告都支持同一归档流程。

### 常用 CLI

```bash
forgedan suite run examples/smoke-suite.yml
forgedan suite preflight examples/ready-for-handoff-suite.yml --strict --output reports/preflight-ready
forgedan suite validate-report reports/suite-ready/suite-result.json
forgedan suite verify-bundle reports/suite-ready/suite-manifest.json
forgedan suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff
forgedan suite archive reports/suite-ready/suite-manifest.json --output reports/suite-ready/handoff.zip
forgedan suite verify-archive reports/suite-ready/handoff.zip
forgedan suite compare base.json current.json --output comparison.json --fail-on-regression
forgedan suite taxonomy --json
forgedan suite schemas --json
forgedan run --quick -g "test prompt" -m mock:test
forgedan web
```

更完整的 CLI 说明见英文版 [CLI Reference](#cli-reference)。

### 报告包组成

| 制品 | 受众 | 用途 |
|------|------|------|
| `suite-report.md` / `suite-report.html` | 授权评审人 | 含范围、方法、发现、覆盖率、风险、用量和限制的叙事报告 |
| `suite-result.json` / `suite-cases.jsonl` | 授权评审人 | 原始机器可读结果和逐 case trace，便于审计 replay |
| `suite-evidence.csv` | 授权评审人 | finding 证据表，包含 taxonomy、confidence、severity rationale、OWASP LLM 映射和建议 |
| `suite-case-matrix.csv` | 外部评审人 | case 级结果、风险、用量、scorer、metadata 与覆盖率矩阵 |
| `suite-risk-register.json` / `suite-risk-register.csv` | 评估团队 | remediation tracker，包含 owner/status/due date、severity rationale 和 evidence fingerprint |
| `suite-coverage.json` / `suite-coverage.csv` | 外部评审人 | 按 case category、policy domain、taxonomy category、OWASP LLM category 汇总覆盖率 |
| `suite-config.json` | 评估团队 | 归一化 suite 输入快照，便于审计复放 |
| `suite-preflight.json` / `suite-preflight.md` | 评估团队 | 运行前 readiness audit |
| `suite-release-notes.md` | 授权评审人 | 简短运行说明、风险、验收、Source Inventory、reviewer decision 和制品指针 |
| 脱敏 report/result/cases | 外部评审人 | 低敏发布包，隐藏原始 prompt、response 和 evidence |
| `suite-manifest.json` | 评估团队 | 含大小、SHA256、schema references、敏感度、受众分类和验收状态的完整性清单 |
| `suite-qa-receipt.json` / `suite-qa-receipt.md` | 评估负责人 | 交接回执，覆盖 manifest、schema、hash、跨制品一致性、预检、验收、risk owner 和限制项 |
| `handoff.zip` | 交付接收方 | 可在复制或分享后用 `verify-archive` 重新校验的单文件交付包 |

### JSON Schema 与验证

报告制品 schema 位于 `schemas/`，包含：

- `suite-result.schema.json`
- `suite-config.schema.json`
- `suite-manifest.schema.json`
- `suite-comparison.schema.json`
- `suite-comparison-manifest.schema.json`
- `suite-qa-receipt.schema.json`
- `suite-preflight.schema.json`
- `suite-risk-register.schema.json`
- `suite-coverage.schema.json`
- `finding-taxonomy.schema.json`

`validate-report` 不只检查 JSON Schema，还会复算 Source Inventory、usage cost、risk register、coverage totals、comparison regression count、policy-domain delta、QA receipt readiness、manifest binding 和 Markdown/HTML sidecar 摘要，尽量避免手工改报告后出现机器结果与人工报告不一致。

### 开发与验证

```bash
pip install -e ".[dev]"

# 全量测试
python -m pytest -q -W error::DeprecationWarning -p no:cacheprovider --basetemp .tmp-test

# selected flake8 gate
python -m flake8 forgedan/ --select=E9,F63,F7,F82,E722,F401,F841 --show-source --statistics

# formatter gate
python -m black --check forgedan tests

# 前端构建
cd frontend
npm install
npm run build
```

### 当前路线图

- [x] 进化算法引擎与 15 种变异策略
- [x] 6 种攻击方法：FORGEDAN、AutoDAN、PAIR、GCG、Crescendo、TAP
- [x] 托管模型、中文模型、本地模型、vLLM、HuggingFace、Vision 与 Mock adapter
- [x] YAML suite runner、导入 case、自定义 scorer、响应缓存、Source Inventory 和 policy gates
- [x] Prompt Injection、越狱框架、系统提示泄漏、敏感信息/PII、Agent/MCP/工具策略风险和模型制品信号扫描
- [x] Markdown/HTML 报告、脱敏发布包、证据矩阵、case matrix、风险登记、覆盖率摘要、release notes 和 bundle index
- [x] JSON Schema、语义校验、manifest verification、跨制品一致性、QA receipt 和 archive verification
- [x] CI 覆盖 unit tests、preflight、smoke report pack、ready-for-handoff QA、selected flake8、Black 和 frontend build
- [ ] 补齐 archive 内部跨制品一致性校验，与目录版 `verify-bundle` 对齐
- [ ] 增加更多真实 Agent/MCP manifest fixture，校准 trust score 和默认 policy
- [ ] 仅在能提升报告证据质量时加入 HarmBench/JailbreakBench 示例
- [ ] 在报告范围需要时补更深的 model serialization 分析
- [ ] 发布可渲染 sample report pack，方便评审人在运行 CLI 前直接查看输出

### 引用

如果在研究中使用 FORGEDAN，请引用：

```bibtex
@article{cheng2025forgedan,
  title={FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models},
  author={Cheng, Siyang and Liu, Gaotian and Mei, Rui and Wang, Yilin and Zhang, Kejia and Wei, Kaishuo and Yu, Yuqi and Wen, Weiping and Wu, Xiaojie and Liu, Junhua},
  journal={arXiv preprint arXiv:2511.13548},
  year={2025}
}
```

### 安全说明

本项目仅用于授权安全测试、研究复现和报告交付。测试任何系统前请确认授权范围、评估目标、数据边界和交付对象。原始 prompt、response、case trace、缓存和 evidence 可能包含敏感信息，应按评估报告证据管理要求限制访问。

### 许可证

本项目使用 MIT License，详见 [LICENSE](LICENSE)。

---

<div align="center">

**Built with** ❤️ **by [Coff0xc](https://github.com/Coff0xc)**

[Report Bug](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues) · [Request Feature](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues)

</div>

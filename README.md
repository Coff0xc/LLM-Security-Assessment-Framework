<div align="center">

# FORGEDAN

### Report-first LLM Security Assessment Framework
### 面向报告交付的 LLM 安全评估框架

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/arXiv-2511.13548-b31b1b.svg)](https://arxiv.org/abs/2511.13548)
[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)

**Reproducible suites | Evidence-rich report packs | QA receipts | Archive verification**

**可复现套件 | 证据化报告包 | QA 交接回执 | 归档校验**

[Screenshots / 截图](#screenshots--使用截图) ·
[Quick Start / 快速开始](#quick-start--快速开始) ·
[Report Workflow / 报告工作流](#report-workflow--报告工作流) ·
[Artifacts / 制品](#report-pack-artifacts--报告包制品) ·
[Development / 开发](#development--开发与验证) ·
[中文独立版](README.zh-CN.md)

</div>

---

## README Format / README 格式

This README is now maintained as a **full bilingual paired guide**. Each major
section includes English and Chinese content together so GitHub visitors,
reviewers, and report recipients can follow the same facts without jumping
between two separate halves of the document.

本 README 采用 **完整中英双语对照格式** 维护。每个主要章节都同时给出英文与中文说明，方便
GitHub 访客、评审人和报告接收方在同一位置阅读同一组事实，不需要在英文版和中文版之间来回跳转。

The standalone [README.zh-CN.md](README.zh-CN.md) remains available for
Chinese-only sharing.

独立中文版本 [README.zh-CN.md](README.zh-CN.md) 仍然保留，适合只需要中文交付或内部转发的场景。

---

## Project Positioning / 项目定位

**FORGEDAN** is a report-oriented LLM security assessment framework based on the
paper [*FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large
Language Models*](https://arxiv.org/abs/2511.13548).

**FORGEDAN** 基于论文 [*FORGEDAN: An Evolutionary Framework for Jailbreaking
Aligned Large Language Models*](https://arxiv.org/abs/2511.13548)，当前项目定位为
面向报告交付的 LLM 安全评估框架。

The repository still contains evolutionary jailbreak attacks, model adapters,
WebScan utilities, a REST API, and a Vue dashboard. Its current engineering
goal is narrower and clearer: **produce auditable, reproducible,
handoff-ready security assessment report packs**.

仓库仍保留进化式越狱攻击、模型适配器、WebScan、REST API 和 Vue 仪表盘。当前工程目标更聚焦：
**生成可审计、可复现、可交接的安全评估报告包**。

This is a report-delivery project, not a commercial security platform. The
primary value is evidence quality: traceable inputs, deterministic outputs,
schema contracts, QA receipts, risk registers, redacted publication packs, and
archives that can be verified after copying or sharing.

这不是商业化安全平台，而是报告交付项目。核心价值在于报告证据质量：可追溯输入、确定性输出、
Schema 合约、QA 回执、风险登记、脱敏发布包，以及复制或分享后仍可重新校验的归档。

---

## Delivery Snapshot / 交付速览

| Topic | English | 中文 |
| --- | --- | --- |
| Purpose | Generate reproducible LLM security assessment report packs. | 生成可复现的 LLM 安全评估报告包。 |
| Recommended path | `preflight` -> `suite run` -> `validate-report` -> `verify-bundle` -> `qa-report --strict-handoff` -> `archive` -> `verify-archive`. | 推荐路径：预检、生成报告包、校验报告制品、验证目录包、生成严格 QA 回执、打包 ZIP、交付后复核归档。 |
| Evidence | Markdown/HTML reports, JSON/JSONL traces, CSV evidence, case matrix, coverage summary, risk register, release notes, QA receipt, manifest. | 证据包括 Markdown/HTML 报告、JSON/JSONL trace、CSV 证据矩阵、case matrix、覆盖率摘要、风险登记、发布说明、QA 回执和 manifest。 |
| Integrity | Schemas, SHA256/size checks, sidecar binding, redaction checks, cross-artifact consistency, archive verification. | 通过 Schema、SHA256/大小、sidecar 绑定、脱敏检查、跨制品一致性和 ZIP 归档校验保护交付质量。 |
| Sample | [Ready-for-handoff sample pack](docs/sample-report-pack/ready-for-handoff/README.md). | [可交付样例包](docs/sample-report-pack/ready-for-handoff/README.md)。 |

---

## Key Capabilities / 核心能力

| Area | English | 中文 |
| --- | --- | --- |
| Report suites | YAML suite definitions, inline or imported cases, replay caches, deterministic seeds, policy gates, preflight readiness checks. | YAML suite、内联/导入用例、响应缓存、确定性种子、策略门禁、运行前预检。 |
| Report artifacts | Markdown/HTML reports, executive summaries, evidence CSVs, case matrices, risk registers, coverage summaries, release notes, bundle indexes. | Markdown/HTML 报告、执行摘要、证据 CSV、case matrix、风险登记、覆盖率摘要、发布说明、bundle index。 |
| Evidence integrity | JSON Schemas, artifact manifests, SHA256/size checks, cross-artifact consistency, redacted-publication leak checks. | JSON Schema、制品 manifest、SHA256/大小校验、跨制品一致性校验、脱敏发布泄漏检查。 |
| Handoff QA | QA receipt JSON/Markdown, acceptance criteria, reviewer decisions, owner/due-date tracking, strict handoff gates. | QA receipt JSON/Markdown、验收准则、评审决策、owner/due date、严格交接门禁。 |
| Assessment coverage | Prompt injection, jailbreak roleplay, system prompt leakage, secrets/PII exposure, Agent/MCP/tool policy risk, model artifact signals. | Prompt Injection、越狱角色扮演、系统提示泄漏、敏感信息/PII、Agent/MCP/工具策略风险、模型制品信号。 |
| Baseline engine | FORGEDAN, AutoDAN, PAIR, GCG, Crescendo, TAP, model adapters, WebScan, CLI, REST API, Vue dashboard. | FORGEDAN、AutoDAN、PAIR、GCG、Crescendo、TAP、模型适配器、WebScan、CLI、REST API、Vue dashboard。 |

---

## GitHub About / GitHub About 建议

Suggested repository description:

> Report-first LLM security assessment framework for reproducible red-team suites, evidence packs, QA receipts, schemas, and archive verification.

仓库侧栏描述建议：

> 面向报告交付的 LLM 安全评估框架，用于生成可复现红队套件、证据包、QA 回执、Schema 合约和可校验归档。

Suggested topics / 建议 Topics:

`llm-security`, `ai-red-team`, `prompt-injection`, `jailbreak`,
`owasp-llm`, `mcp-security`, `agent-security`, `security-reporting`,
`risk-register`, `audit-evidence`, `json-schema`, `pytest`, `python`

---

## Screenshots / 使用截图

The screenshots below come from the checked-in sample generated by
`examples/ready-for-handoff-suite.yml`. The rendered sample is available at
[docs/sample-report-pack/ready-for-handoff](docs/sample-report-pack/ready-for-handoff/README.md).

下面截图来自 `examples/ready-for-handoff-suite.yml` 生成并提交到仓库的样例报告包。
完整样例见 [docs/sample-report-pack/ready-for-handoff](docs/sample-report-pack/ready-for-handoff/README.md)。

### Report Pack Overview / 报告包总览

![Report pack overview / 报告包总览](docs/screenshots/report-overview.png)

### QA Receipt / QA 交接回执

![QA receipt handoff readiness / QA 交接回执](docs/screenshots/qa-receipt.png)

### Archive Verification / 归档校验

![Archive verification / 归档校验](docs/screenshots/archive-verification.png)

---

## Quick Start / 快速开始

### Prerequisites / 前置要求

- Python >= 3.9
- Git
- Node.js >= 18, only required for the Vue dashboard / 仅运行 Vue dashboard 时需要

### Install / 安装

```bash
git clone https://github.com/Coff0xc/LLM-Security-Assessment-Framework.git
cd LLM-Security-Assessment-Framework

# Minimal backend install / 后端最小安装
pip install -e .

# Web dashboard and WebScan dependencies / Web dashboard 和 WebScan 依赖
pip install -e ".[web]"

# Full provider, web, monitoring, and dev extras / 全量 provider、web、monitoring 和 dev 依赖
pip install -e ".[all]"

# Frontend / 前端
cd frontend
npm install
```

### Generate a Ready-for-Handoff Report Pack / 生成可交付报告包

```bash
python -m forgedan.cli suite preflight examples/ready-for-handoff-suite.yml --strict --output reports/preflight-ready
python -m forgedan.cli suite run examples/ready-for-handoff-suite.yml --output reports/suite-ready
python -m forgedan.cli suite validate-report reports/suite-ready/suite-result.json
python -m forgedan.cli suite verify-bundle reports/suite-ready/suite-manifest.json
python -m forgedan.cli suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff
python -m forgedan.cli suite archive reports/suite-ready/suite-manifest.json --output reports/suite-ready/handoff.zip
python -m forgedan.cli suite verify-archive reports/suite-ready/handoff.zip
```

The same commands can be run as `forgedan suite ...` after installing the
console script.

安装 console script 后，也可以使用 `forgedan suite ...` 形式运行。

### Run a Zero-Config Attack Demo / 运行零配置攻击 Demo

```bash
python -m forgedan.cli run --quick -g "test prompt" -m mock:test
```

### Run the Web Dashboard / 运行 Web Dashboard

```bash
python -m forgedan.cli web
cd frontend
npm run dev
```

The backend defaults to `:5000`; the frontend defaults to `:5173`.

后端默认在 `:5000`，前端默认在 `:5173`。

---

## Documentation Map / 文档导航

| Document | English | 中文 |
| --- | --- | --- |
| [docs/sample-report-pack/ready-for-handoff/](docs/sample-report-pack/ready-for-handoff/README.md) | Checked-in mock report pack with QA receipt and verified ZIP archive. | 已提交的 mock 样例报告包，包含 QA 回执和已校验 ZIP。 |
| [docs/llm-security-landscape.md](docs/llm-security-landscape.md) | Competitor scan, gaps, and optimization priorities. | 同类项目扫描、能力差距和优化优先级。 |
| [docs/lint-roadmap.md](docs/lint-roadmap.md) | Current CI lint gate, measured lint debt, and promotion plan. | 当前 CI lint 门禁、历史债务统计和更严格质量门禁推进路径。 |
| [docs/repository-about.md](docs/repository-about.md) | Repository sidebar wording and topic recommendations. | 仓库侧栏描述和 topic 建议。 |
| [schemas/](schemas/) | JSON Schema contracts for report artifacts. | 报告制品 JSON Schema 合约。 |
| [examples/](examples/) | Runnable suites, case fixtures, MCP manifests, model artifact fixtures. | 可运行 suite、case fixture、MCP manifest、模型制品 fixture。 |

---

## Report Workflow / 报告工作流

| Step | English | 中文 |
| --- | --- | --- |
| 1 | Define scope in a suite YAML file: cases, imported evidence sources, report metadata, policy gates, coverage requirements, acceptance criteria, reviewer decisions, and risk-register defaults. | 在 suite YAML 中定义范围：cases、导入证据源、报告元数据、策略门禁、覆盖率要求、验收准则、评审决策和风险登记默认值。 |
| 2 | Run `suite preflight` to catch missing metadata, unresolved scorers, weak handoff criteria, missing provenance, and incomplete deterministic replay settings before spending provider budget. | 使用 `suite preflight` 在消耗模型预算前检查元数据、scorer、交接准则、来源证明和确定性 replay 设置。 |
| 3 | Generate the report pack with `suite run`; the run writes raw and redacted machine-readable artifacts, Markdown/HTML reports, CSV matrices, coverage, risk register, release notes, and a manifest. | 使用 `suite run` 生成报告包，写出原始与脱敏 JSON/JSONL、Markdown/HTML 报告、CSV 矩阵、覆盖率、风险登记、发布说明和 manifest。 |
| 4 | Validate locally with `validate-report` and `verify-bundle`; these checks bind schemas, hashes, summary counts, redacted artifacts, Markdown/HTML sidecars, and cross-artifact identities back to the source result. | 使用 `validate-report` 与 `verify-bundle` 本地验证 schema、hash、摘要计数、脱敏制品、Markdown/HTML sidecar 和跨制品身份。 |
| 5 | Prepare handoff with `qa-report --strict-handoff`; the receipt records checklist status, blockers, acceptance criteria, source inventory, schema checks, and reviewer-facing evidence. | 使用 `qa-report --strict-handoff` 准备交接，回执记录 checklist、blocker、验收准则、Source Inventory、schema 校验和评审证据。 |
| 6 | Archive and verify with `archive` and `verify-archive`; generated release notes and bundle indexes carry the handoff commands, and `verify-bundle` checks that the guidance stays present. | 使用 `archive` 和 `verify-archive` 打包并复核；release notes 和 bundle index 会写入交接命令，`verify-bundle` 会回查这些命令是否仍然存在。 |

---

## CLI Reference / 常用 CLI

| Scenario | Command | 中文场景 |
| --- | --- | --- |
| Run a suite | `python -m forgedan.cli suite run examples/smoke-suite.yml` | 运行 suite |
| Use per-run output directories | `python -m forgedan.cli suite run examples/smoke-suite.yml --run-id-dir` | 按 run ID 输出目录 |
| Run preflight | `python -m forgedan.cli suite preflight examples/ready-for-handoff-suite.yml --strict --output reports/preflight-ready` | 运行预检 |
| Validate a report artifact | `python -m forgedan.cli suite validate-report reports/suite-ready/suite-result.json` | 校验报告制品 |
| Verify a report directory bundle | `python -m forgedan.cli suite verify-bundle reports/suite-ready/suite-manifest.json` | 验证目录包 |
| Write a QA receipt | `python -m forgedan.cli suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff` | 生成 QA 回执 |
| Create a handoff ZIP | `python -m forgedan.cli suite archive reports/suite-ready/suite-manifest.json --output reports/suite-ready/handoff.zip` | 创建交付 ZIP |
| Verify a handoff ZIP | `python -m forgedan.cli suite verify-archive reports/suite-ready/handoff.zip` | 验证交付 ZIP |
| Compare suite results | `python -m forgedan.cli suite compare base.json current.json --output comparison.json --fail-on-regression` | 对比 suite 结果 |
| Export taxonomy | `python -m forgedan.cli suite taxonomy --json` | 导出 taxonomy |
| Export schema references | `python -m forgedan.cli suite schemas --json` | 导出 schema references |
| Run a quick attack demo | `python -m forgedan.cli run --quick -g "test prompt" -m mock:test` | 运行攻击 demo |
| Start the API/web backend | `python -m forgedan.cli web` | 启动 API/web 后端 |

---

## Report Pack Artifacts / 报告包制品

| Artifact | Audience | English Purpose | 中文用途 |
| --- | --- | --- | --- |
| `suite-report.md` / `suite-report.html` | Authorized reviewers | Narrative report with scope, method, findings, coverage, risk, usage, and limitations. | 面向授权评审人的叙事报告，包含范围、方法、发现、覆盖率、风险、用量和限制。 |
| `suite-result.json` / `suite-cases.jsonl` | Assessment team | Raw machine-readable results and case traces for audit replay. | 原始机器可读结果和逐 case trace，便于审计 replay。 |
| `suite-evidence.csv` | Reviewers | Finding evidence with taxonomy, confidence, severity rationale, OWASP LLM mapping, and recommendations. | finding 证据表，包含 taxonomy、confidence、severity rationale、OWASP LLM 映射和建议。 |
| `suite-case-matrix.csv` | Reviewers | Case-level result, risk, usage, scorer, metadata, and coverage matrix. | case 级结果、风险、用量、scorer、metadata 和覆盖率矩阵。 |
| `suite-risk-register.json` / `suite-risk-register.csv` | Remediation owners | Risk tracker with owner, status, due date, severity rationale, and evidence fingerprint. | 风险跟踪表，包含 owner、status、due date、severity rationale 和 evidence fingerprint。 |
| `suite-coverage.json` / `suite-coverage.csv` | Reviewers | Coverage by case category, policy domain, taxonomy category, and OWASP LLM category. | 按 case category、policy domain、taxonomy category、OWASP LLM category 汇总覆盖率。 |
| `suite-config.json` | Assessment team | Normalized suite input snapshot for audit replay. | 归一化 suite 输入快照，便于审计复放。 |
| `suite-preflight.json` / `suite-preflight.md` | Assessment team | Readiness audit before model execution. | 模型执行前的 readiness audit。 |
| `suite-release-notes.md` | Reviewers | Short handoff notes with risk, acceptance, source inventory, reviewer decisions, artifact pointers, and archive commands. | 简短交接说明，包含风险、验收、Source Inventory、reviewer decision、制品指针和归档命令。 |
| Redacted report/result/cases | External reviewers | Lower-sensitivity publication package with prompts, responses, and evidence redacted. | 低敏发布包，隐藏原始 prompt、response 和 evidence。 |
| `suite-manifest.json` | Assessment team | Artifact integrity manifest with size, SHA256, schema references, sensitivity, audience labels, and acceptance status. | 制品完整性清单，包含大小、SHA256、schema references、敏感度、受众标签和验收状态。 |
| `suite-qa-receipt.json` / `suite-qa-receipt.md` | Assessment lead | Handoff receipt covering manifest, schemas, hashes, consistency checks, preflight, acceptance, risk owners, and limitations. | 交接回执，覆盖 manifest、schema、hash、跨制品一致性、预检、验收、risk owner 和限制项。 |
| `handoff.zip` | Report recipient | Single-file package that can be re-verified after copying or sharing. | 单文件交付包，可在复制或分享后重新校验。 |

---

## JSON Schema and Verification / JSON Schema 与验证

Schemas live in [schemas/](schemas/) and cover:

Schema 位于 [schemas/](schemas/)，覆盖：

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

`validate-report` checks more than JSON Schema. It also recalculates source
inventory, usage cost, risk register totals, coverage totals, comparison
regression counts, QA receipt readiness, manifest binding, and Markdown/HTML
sidecar summaries so edited reports cannot silently diverge from machine data.

`validate-report` 不只检查 JSON Schema，还会复算 Source Inventory、usage cost、risk register totals、
coverage totals、comparison regression counts、QA receipt readiness、manifest binding 和 Markdown/HTML sidecar
摘要，尽量避免手工修改后出现机器数据与人工报告不一致。

---

## Attack Methods / 攻击方法

| Method | Type | English | 中文 | Paper |
| --- | --- | --- | --- | --- |
| FORGEDAN | Evolutionary | Multi-level mutation with semantic fitness and dual judge. | 多层级 mutation，结合语义适应度和双 judge。 | [arXiv:2511.13548](https://arxiv.org/abs/2511.13548) |
| AutoDAN | Evolutionary | Hierarchical genetic algorithm for stealthy jailbreak prompts. | 面向隐蔽越狱 prompt 的层次化遗传算法。 | [ICLR 2024](https://arxiv.org/abs/2310.04451) |
| PAIR | LLM-iterative | Black-box jailbreak via attacker-target LLM iteration. | 通过 attacker-target LLM 迭代完成黑盒越狱。 | [NeurIPS 2024](https://arxiv.org/abs/2310.08419) |
| GCG | Gradient-free | Greedy coordinate adversarial suffix generation. | 基于贪心坐标搜索的 adversarial suffix 生成。 | [ICML 2023](https://arxiv.org/abs/2307.15043) |
| Crescendo | Multi-turn | Gradual escalation from benign to harmful content. | 从低风险内容逐步升级到高风险请求的多轮攻击。 | [USENIX Security 2025](https://arxiv.org/abs/2404.01833) |
| TAP | Tree search | Tree-of-thought attack with pruning and multi-LLM collaboration. | Tree-of-thought 攻击搜索，带剪枝和多 LLM 协作。 | [NeurIPS 2024](https://arxiv.org/abs/2312.02119) |

---

## Model Adapters / 模型适配器

| Provider | Models / 模型范围 | Example / 示例 |
| --- | --- | --- |
| OpenAI | GPT-3.5, GPT-4, GPT-4o | `openai:gpt-4` |
| Anthropic | Claude 3 Opus/Sonnet/Haiku | `anthropic:claude-3-opus` |
| Google | Gemini Pro, Gemini Vision | `gemini:gemini-pro` |
| DeepSeek | DeepSeek Chat/Coder | `deepseek:deepseek-chat` |
| Zhipu / 智谱 | GLM-4, GLM-3 | `zhipu:glm-4` |
| Qwen / 通义千问 | Qwen Max/Plus | `qwen:qwen-max` |
| Moonshot / 月之暗面 | Kimi | `moonshot:moonshot-v1-8k` |
| Yi / 零一万物 | Yi Large/Medium | `yi:yi-large` |
| Baichuan / 百川 | Baichuan 4/3 | `baichuan:baichuan-4` |
| Ollama | Local Ollama models / 本地 Ollama 模型 | `ollama:llama2` |
| vLLM | Local vLLM services / 本地 vLLM 服务 | `vllm:model-name` |
| HuggingFace | HuggingFace models / HuggingFace 模型 | `huggingface:model-name` |
| Mock | Local testing, no API key / 本地测试，无需 API key | `mock:test-model` |

---

## WebScan Modes / WebScan 模式

| Mode | English | 中文 | Use Case / 适用场景 |
| --- | --- | --- | --- |
| URL crawler | Async crawling plus title, form, link, and script extraction. | 异步抓取页面标题、表单、链接和脚本。 | Gather attack material from target websites / 收集目标站点中的攻击素材。 |
| Security scanner | XSS, SQLi, directory traversal, security headers, HTTP methods. | 检查 XSS、SQLi、路径穿越、安全 Header 和 HTTP Method。 | Traditional web vulnerability assessment / 传统 Web 漏洞评估。 |
| LLM interaction test | Indirect prompt injection via web content and evolutionary optimization. | 使用网页内容触发间接 Prompt Injection，并结合进化式优化。 | Test LLM safety when processing web content / 评估 LLM 处理网页内容时的安全性。 |

---

## Architecture / 架构概览

```text
forgedan/
├── suite.py              # Suite runner, artifact writer, validators, QA receipt, archive verifier
├── scanners.py           # Deterministic prompt/response/tool/model-artifact scanners
├── scorers.py            # Reusable deterministic suite scorers
├── finding_taxonomy.py   # Stable finding IDs, categories, priorities, OWASP LLM mappings
├── attacks/              # Attack algorithms and registry
├── adapters/             # Hosted, local, Chinese, vision, vLLM, HuggingFace, and mock adapters
├── api/                  # Flask Blueprint REST API
├── webscan/              # Crawler, web scanner, LLM interaction tester
├── engine.py             # Evolutionary algorithm engine
├── mutator.py            # Mutation strategies and MAB selection
├── fitness.py            # Semantic similarity fitness evaluation
└── judge.py              # Dual-judge mechanism

schemas/                  # Report artifact JSON Schema contracts
examples/                 # Runnable suite examples and fixtures
docs/                     # Landscape scan, lint roadmap, sample report pack
tests/                    # Pytest coverage
frontend/                 # Vue 3 SPA dashboard
```

中文说明：

- `forgedan/suite.py` 是报告套件主入口，负责运行、制品写入、验证、QA 回执和归档校验。
- `schemas/` 保存报告制品 JSON Schema 合约。
- `examples/` 保存可运行 suite、case/MCP/model fixture。
- `docs/` 保存同类项目扫描、lint roadmap 和样例报告包。
- `frontend/` 保存 Vue 3 仪表盘。

---

## API Endpoints / API 端点

```text
POST   /api/attacks/run
GET    /api/attacks/{id}/status
GET    /api/attacks/{id}/result
POST   /api/attacks/{id}/stop

GET    /api/models/providers
POST   /api/models/test

POST   /api/webscan/crawl
POST   /api/webscan/scan
POST   /api/webscan/llm-test

POST   /api/reports/generate
GET    /api/reports/{id}
GET    /api/reports/{id}/download

GET    /api/datasets
POST   /api/datasets/upload

GET    /api/health
GET    /api/metrics
```

The API is intended for automation, demos, and internal assessment workflows.

API 适合自动化脚本、演示环境和内部评估流程接入。

---

## Development / 开发与验证

```bash
pip install -e ".[dev]"

# Full pytest suite used locally / 本地全量 pytest
python -m pytest -q -W error::DeprecationWarning -p no:cacheprovider --basetemp .tmp-test

# CI report-pack gates / CI 报告包门禁
python -m forgedan.cli suite run examples/ready-for-handoff-suite.yml --output reports/suite-ready
python -m forgedan.cli suite verify-bundle reports/suite-ready/suite-manifest.json
python -m forgedan.cli suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff
python -m forgedan.cli suite verify-archive reports/suite-ready/handoff.zip

# Selected flake8 gate / flake8 选定门禁
python -m flake8 forgedan/ --select=E9,F63,F7,F82,E722,F401,F841 --show-source --statistics

# Formatter gate / 格式化门禁
python -m black --check forgedan tests

# Frontend build / 前端构建
cd frontend
npm install
npm run build
```

---

## Roadmap / 当前路线图

- [x] Evolutionary engine and mutation strategies / 进化算法引擎与 mutation strategy
- [x] Six attack methods: FORGEDAN, AutoDAN, PAIR, GCG, Crescendo, TAP / 6 种攻击方法
- [x] Hosted, Chinese, local, vLLM, HuggingFace, vision, and mock adapters / 托管、中文、本地、vLLM、HuggingFace、vision 和 mock adapter
- [x] YAML suite runner with imported cases, custom scorers, response cache, source inventory, and policy gates / YAML suite runner、导入 case、自定义 scorer、响应缓存、Source Inventory 和 policy gates
- [x] Prompt injection, jailbreak framing, system prompt leakage, secrets/PII, Agent/MCP/tool policy risk, and model artifact scanning / Prompt Injection、越狱框架、系统提示泄漏、敏感信息/PII、Agent/MCP/工具策略风险和模型制品扫描
- [x] Markdown/HTML reports, redacted publication packs, evidence matrices, case matrices, risk registers, coverage summaries, release notes, and bundle indexes / Markdown/HTML 报告、脱敏发布包、证据矩阵、case matrix、风险登记、覆盖率摘要、发布说明和 bundle index
- [x] JSON Schema contracts, semantic validation, manifest verification, QA receipts, and archive verification / JSON Schema 合约、语义校验、manifest verification、QA receipt 和 archive verification
- [x] Checked-in ready-for-handoff sample report pack with screenshots / 已提交 ready-for-handoff 样例报告包和截图
- [x] CI gates for tests, report-pack validation, strict QA handoff, archive verification, selected flake8, Black, and frontend build / CI 覆盖 tests、报告包校验、严格 QA 交接、归档校验、selected flake8、Black 和 frontend build
- [ ] Add more real Agent/MCP manifest fixtures and calibrate default trust-score policy / 增加更多真实 Agent/MCP manifest fixture，校准默认 trust-score policy
- [ ] Add HarmBench/JailbreakBench examples only where they improve report evidence quality / 仅在能提升报告证据质量时加入 HarmBench/JailbreakBench 示例
- [ ] Expand model serialization analysis when the report scope needs deeper artifact review / 当报告范围需要时扩展更深的 model serialization 分析

---

## Citation / 引用

```bibtex
@article{cheng2025forgedan,
  title={FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models},
  author={Cheng, Siyang and Liu, Gaotian and Mei, Rui and Wang, Yilin and Zhang, Kejia and Wei, Kaishuo and Yu, Yuqi and Wen, Weiping and Wu, Xiaojie and Liu, Junhua},
  journal={arXiv preprint arXiv:2511.13548},
  year={2025}
}
```

---

## Contributing / 贡献

Contributions are welcome. Please keep report artifacts, schemas, tests, and
documentation aligned when changing report behavior. See
[CONTRIBUTING.md](CONTRIBUTING.md) for the general contribution flow.

欢迎提交改进。修改报告行为时，请同步维护报告制品、Schema、测试和文档。
通用贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

---

## Security / 安全说明

Use this project only for authorized security testing, research reproduction,
and report delivery. Raw prompts, responses, traces, caches, and evidence may
contain sensitive data; handle them according to the assessment scope and
handoff rules.

本项目仅用于授权安全测试、研究复现和报告交付。原始 prompt、response、trace、cache 和 evidence
可能包含敏感数据，应按评估范围和交接规则管理。

---

## License / 许可证

This project is released under the MIT License. See [LICENSE](LICENSE).

本项目使用 MIT License，详见 [LICENSE](LICENSE)。

---

<div align="center">

**Built by [Coff0xc](https://github.com/Coff0xc)**

[Report Bug](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues) ·
[Request Feature](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues)

</div>

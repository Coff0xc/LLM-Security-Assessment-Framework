<div align="center">

# FORGEDAN

### 面向报告交付的 LLM 安全评估框架
### Report-first LLM Security Assessment Framework

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/actions/workflows/ci.yml/badge.svg)](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/arXiv-2511.13548-b31b1b.svg)](https://arxiv.org/abs/2511.13548)
[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![Report Pack](https://img.shields.io/badge/report%20pack-schema%20verified-2ea44f.svg)](docs/sample-report-pack/ready-for-handoff/README.md)

**中文：可复现套件 | 证据化报告包 | QA 交接回执 | 可校验归档**

**English: Reproducible suites | Evidence-rich report packs | QA receipts | Verifiable archives**

[项目定位 / Positioning](#project-positioning) ·
[使用截图 / Screenshots](#screenshots) ·
[快速开始 / Quick Start](#quick-start) ·
[报告工作流 / Workflow](#report-workflow) ·
[报告包制品 / Artifacts](#report-artifacts) ·
[验证 / Verification](#verification) ·
[开发 / Development](#development) ·
[中文独立版](README.zh-CN.md)

</div>

---

<a id="bilingual-format"></a>
## 双语格式 / Bilingual Format

中文：本 README 采用 **全量中文 + English 双语对照** 格式。每个核心章节都先给出中文说明，再给出对应英文说明；表格也保留中文与 English 两列，方便 GitHub 访客、评审人、报告接收方和维护者阅读同一组事实。

English: This README is maintained as a **full Chinese + English bilingual guide**. Each core section starts with Chinese content followed by the matching English content, and tables keep both languages visible so visitors, reviewers, report recipients, and maintainers share one source of truth.

中文：如果只需要中文交付或内部转发，可以使用 [README.zh-CN.md](README.zh-CN.md)。主 README 保持中英完整对照，避免两个语言版本事实漂移。

English: For Chinese-only sharing, use [README.zh-CN.md](README.zh-CN.md). The main README stays fully bilingual to prevent fact drift between language versions.

---

<a id="project-positioning"></a>
## 项目定位 / Project Positioning

中文：**FORGEDAN** 基于论文 [*FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models*](https://arxiv.org/abs/2511.13548)，但当前项目主线已经从单纯的越狱算法演示扩展为 **LLM 安全评估报告交付框架**。

English: **FORGEDAN** is based on the paper [*FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models*](https://arxiv.org/abs/2511.13548), but the current project direction has expanded from a jailbreak algorithm demo into a **report-delivery framework for LLM security assessments**.

中文：本仓库仍保留进化式越狱攻击、模型适配器、WebScan、REST API 和 Vue dashboard。当前更重要的目标是生成可审计、可复现、可交接的报告包，包括 YAML 套件、确定性扫描器与评分器、证据矩阵、风险登记、覆盖率摘要、JSON Schema 合约、QA 回执、脱敏发布包，以及复制或分享后仍可重新校验的 ZIP 归档。

English: The repository still contains evolutionary jailbreak attacks, model adapters, WebScan utilities, a REST API, and a Vue dashboard. Its current priority is to produce auditable, reproducible, handoff-ready report packs: YAML suites, deterministic scanners and scorers, evidence matrices, risk registers, coverage summaries, JSON Schema contracts, QA receipts, redacted publication packs, and ZIP archives that can be verified after copying or sharing.

中文：这不是商业化安全平台，而是报告交付项目。核心价值是报告证据质量：输入可追溯、输出可复现、制品可校验、交付可签收、归档可复核。

English: This is a report-delivery project, not a commercial security platform. Its core value is report evidence quality: traceable inputs, reproducible outputs, verifiable artifacts, signed-off handoff, and re-checkable archives.

---

<a id="delivery-snapshot"></a>
## 交付速览 / Delivery Snapshot

| 主题 / Topic | 中文 | English |
| --- | --- | --- |
| 项目目标 / Purpose | 生成可复现的 LLM 安全评估报告包。 | Generate reproducible LLM security assessment report packs. |
| 推荐路径 / Recommended Path | `preflight` -> `suite run` -> `validate-report` -> `verify-bundle` -> `qa-report --strict-handoff` -> `archive` -> `verify-archive`。 | `preflight` -> `suite run` -> `validate-report` -> `verify-bundle` -> `qa-report --strict-handoff` -> `archive` -> `verify-archive`. |
| 报告证据 / Evidence | Markdown/HTML 报告、JSON/JSONL trace、CSV 证据矩阵、case matrix、覆盖率摘要、风险登记、发布说明、QA 回执和 manifest。 | Markdown/HTML reports, JSON/JSONL traces, CSV evidence, case matrix, coverage summary, risk register, release notes, QA receipt, and manifest. |
| 完整性 / Integrity | 使用 Schema、SHA256/大小、sidecar 绑定、脱敏检查、跨制品一致性和 ZIP 归档校验保护交付质量。 | Use schemas, SHA256/size checks, sidecar binding, redaction checks, cross-artifact consistency, and ZIP archive verification to protect handoff quality. |
| 样例包 / Sample Pack | [ready-for-handoff 样例报告包](docs/sample-report-pack/ready-for-handoff/README.md)。 | [Ready-for-handoff sample report pack](docs/sample-report-pack/ready-for-handoff/README.md). |

---

<a id="screenshots"></a>
## 使用截图 / Screenshots

中文：下面截图来自 `examples/ready-for-handoff-suite.yml` 生成并提交到仓库的样例报告包。完整样例见 [docs/sample-report-pack/ready-for-handoff](docs/sample-report-pack/ready-for-handoff/README.md)。

English: The screenshots below come from the checked-in sample generated by `examples/ready-for-handoff-suite.yml`. The rendered sample is available at [docs/sample-report-pack/ready-for-handoff](docs/sample-report-pack/ready-for-handoff/README.md).

### 报告包总览 / Report Pack Overview

![报告包总览 / Report pack overview](docs/screenshots/report-overview.png)

### QA 交接回执 / QA Receipt

![QA 交接回执 / QA receipt handoff readiness](docs/screenshots/qa-receipt.png)

### 归档校验 / Archive Verification

![归档校验 / Archive verification](docs/screenshots/archive-verification.png)

---

<a id="quick-start"></a>
## 快速开始 / Quick Start

### 前置要求 / Prerequisites

| 项目 / Item | 中文 | English |
| --- | --- | --- |
| Python | Python >= 3.9。 | Python >= 3.9. |
| Git | 克隆仓库和管理本地变更需要 Git。 | Git is required for cloning the repository and managing local changes. |
| Node.js | Node.js >= 18，仅运行 Vue dashboard 时需要。 | Node.js >= 18, only required for the Vue dashboard. |

### 安装 / Install

```bash
git clone https://github.com/Coff0xc/LLM-Security-Assessment-Framework.git
cd LLM-Security-Assessment-Framework

# 后端最小安装 / Minimal backend install
pip install -e .

# Web dashboard 和 WebScan 依赖 / Web dashboard and WebScan dependencies
pip install -e ".[web]"

# 全量 provider、web、monitoring 和 dev 依赖 / Full provider, web, monitoring, and dev extras
pip install -e ".[all]"

# 前端 / Frontend
cd frontend
npm install
```

### 生成可交付报告包 / Generate a Ready-for-Handoff Report Pack

中文：这是当前最推荐的 smoke path：先做无模型预检，再生成报告包，随后校验制品、生成 QA 回执、打包 ZIP，并在交付后重新校验归档。

English: This is the recommended smoke path: run a no-model preflight, generate the report pack, validate artifacts, write the QA receipt, create a ZIP, and verify the archive after handoff.

```bash
python -m forgedan.cli suite preflight examples/ready-for-handoff-suite.yml --strict --output reports/preflight-ready
python -m forgedan.cli suite run examples/ready-for-handoff-suite.yml --output reports/suite-ready
python -m forgedan.cli suite validate-report reports/suite-ready/suite-result.json
python -m forgedan.cli suite verify-bundle reports/suite-ready/suite-manifest.json
python -m forgedan.cli suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff
python -m forgedan.cli suite archive reports/suite-ready/suite-manifest.json --output reports/suite-ready/handoff.zip
python -m forgedan.cli suite verify-archive reports/suite-ready/handoff.zip
```

中文：安装 console script 后，也可以使用 `forgedan suite ...` 形式运行。

English: After installing the console script, the same commands can be run as `forgedan suite ...`.

### 运行零配置攻击 Demo / Run a Zero-Config Attack Demo

```bash
python -m forgedan.cli run --quick -g "test prompt" -m mock:test
```

### 运行 Web Dashboard / Run the Web Dashboard

```bash
python -m forgedan.cli web
cd frontend
npm run dev
```

中文：后端默认在 `:5000`，前端默认在 `:5173`。

English: The backend defaults to `:5000`; the frontend defaults to `:5173`.

---

<a id="report-workflow"></a>
## 报告工作流 / Report Workflow

| 步骤 / Step | 中文 | English |
| --- | --- | --- |
| 1. 定义范围 / Define Scope | 在 suite YAML 中定义 cases、导入证据源、报告元数据、策略门禁、覆盖率要求、验收准则、评审决策和风险登记默认值。 | Define cases, imported evidence sources, report metadata, policy gates, coverage requirements, acceptance criteria, reviewer decisions, and risk-register defaults in a suite YAML file. |
| 2. 运行预检 / Preflight | 使用 `suite preflight` 在消耗模型预算前检查元数据、scorer、交接准则、来源证明和确定性 replay 设置。 | Run `suite preflight` before spending model budget to catch metadata, scorer, handoff-criteria, provenance, and deterministic replay issues. |
| 3. 生成报告 / Generate | 使用 `suite run` 写出原始与脱敏 JSON/JSONL、Markdown/HTML 报告、CSV 矩阵、覆盖率、风险登记、发布说明和 manifest。 | Use `suite run` to write raw and redacted JSON/JSONL, Markdown/HTML reports, CSV matrices, coverage, risk register, release notes, and manifest artifacts. |
| 4. 本地验证 / Validate | 使用 `validate-report` 与 `verify-bundle` 校验 schema、hash、摘要计数、脱敏制品、Markdown/HTML sidecar 和跨制品身份。 | Use `validate-report` and `verify-bundle` to bind schemas, hashes, summary counts, redacted artifacts, Markdown/HTML sidecars, and cross-artifact identities back to the source result. |
| 5. 准备交接 / Handoff | 使用 `qa-report --strict-handoff` 生成 QA 回执，记录 checklist、blocker、验收准则、Source Inventory、schema 校验和评审证据。 | Use `qa-report --strict-handoff` to write a QA receipt with checklist status, blockers, acceptance criteria, source inventory, schema checks, and reviewer-facing evidence. |
| 6. 归档复核 / Archive | 使用 `archive` 和 `verify-archive` 生成单文件 ZIP，并在复制或分享后重新校验。 | Use `archive` and `verify-archive` to create a single ZIP and re-check it after copying or sharing. |

---

<a id="report-artifacts"></a>
## 报告包制品 / Report Pack Artifacts

| 制品 / Artifact | 受众 / Audience | 中文用途 | English Purpose |
| --- | --- | --- | --- |
| `suite-report.md` / `suite-report.html` | 授权评审人 / Authorized reviewers | 叙事报告，包含范围、方法、发现、覆盖率、风险、用量和限制。 | Narrative report covering scope, method, findings, coverage, risk, usage, and limitations. |
| `suite-result.json` / `suite-cases.jsonl` | 评估团队 / Assessment team | 原始机器可读结果和逐 case trace，便于审计 replay。 | Raw machine-readable results and case traces for audit replay. |
| `suite-evidence.csv` | 评审人 / Reviewers | finding 证据表，包含 taxonomy、confidence、severity rationale、OWASP LLM 映射和建议。 | Finding evidence with taxonomy, confidence, severity rationale, OWASP LLM mapping, and recommendations. |
| `suite-case-matrix.csv` | 评审人 / Reviewers | case 级结果、风险、用量、scorer、metadata 和覆盖率矩阵。 | Case-level result, risk, usage, scorer, metadata, and coverage matrix. |
| `suite-risk-register.json` / `suite-risk-register.csv` | 修复负责人 / Remediation owners | 风险跟踪表，包含 owner、status、due date、severity rationale 和 evidence fingerprint。 | Risk tracker with owner, status, due date, severity rationale, and evidence fingerprint. |
| `suite-coverage.json` / `suite-coverage.csv` | 评审人 / Reviewers | 按 case category、policy domain、taxonomy category、OWASP LLM category 汇总覆盖率。 | Coverage by case category, policy domain, taxonomy category, and OWASP LLM category. |
| `suite-config.json` | 评估团队 / Assessment team | 归一化 suite 输入快照，便于审计复放。 | Normalized suite input snapshot for audit replay. |
| `suite-preflight.json` / `suite-preflight.md` | 评估团队 / Assessment team | 模型执行前的 readiness audit。 | Readiness audit before model execution. |
| `suite-release-notes.md` | 评审人 / Reviewers | 简短交接说明，包含风险、验收、Source Inventory、reviewer decision、制品指针和归档命令。 | Short handoff notes with risk, acceptance, source inventory, reviewer decisions, artifact pointers, and archive commands. |
| 脱敏 report/result/cases / Redacted report/result/cases | 外部评审人 / External reviewers | 低敏发布包，隐藏原始 prompt、response 和 evidence。 | Lower-sensitivity publication package with prompts, responses, and evidence redacted. |
| `suite-manifest.json` | 评估团队 / Assessment team | 制品完整性清单，包含大小、SHA256、schema references、敏感度、受众标签和验收状态。 | Artifact integrity manifest with size, SHA256, schema references, sensitivity, audience labels, and acceptance status. |
| `suite-qa-receipt.json` / `suite-qa-receipt.md` | 评估负责人 / Assessment lead | 交接回执，覆盖 manifest、schema、hash、跨制品一致性、预检、验收、risk owner 和限制项。 | Handoff receipt covering manifest, schemas, hashes, consistency checks, preflight, acceptance, risk owners, and limitations. |
| `handoff.zip` | 交付接收方 / Report recipient | 可在复制或分享后用 `verify-archive` 重新校验的单文件交付包。 | Single-file package that can be re-verified after copying or sharing. |

---

<a id="verification"></a>
## JSON Schema 与验证 / JSON Schema and Verification

中文：报告制品 schema 位于 [schemas/](schemas/)，用于机器校验、交付验收和 CI 回归保护。

English: Report artifact schemas live in [schemas/](schemas/) and support machine validation, handoff acceptance, and CI regression protection.

| Schema | 中文 | English |
| --- | --- | --- |
| `suite-result.schema.json` | suite 运行结果。 | Suite run result. |
| `suite-config.schema.json` | 归一化 suite 配置快照。 | Normalized suite configuration snapshot. |
| `suite-manifest.schema.json` | 报告包制品 manifest。 | Report bundle artifact manifest. |
| `suite-comparison.schema.json` | 历史对比结果。 | Historical comparison result. |
| `suite-comparison-manifest.schema.json` | 对比报告 manifest。 | Comparison report manifest. |
| `suite-qa-receipt.schema.json` | QA 交接回执。 | QA handoff receipt. |
| `suite-preflight.schema.json` | 运行前预检结果。 | Preflight readiness result. |
| `suite-risk-register.schema.json` | 风险登记。 | Risk register. |
| `suite-coverage.schema.json` | 覆盖率摘要。 | Coverage summary. |
| `finding-taxonomy.schema.json` | finding taxonomy。 | Finding taxonomy. |

中文：`validate-report` 不只检查 JSON Schema，还会复算 Source Inventory、usage cost、risk register totals、coverage totals、comparison regression counts、QA receipt readiness、manifest binding 和 Markdown/HTML sidecar 摘要，尽量避免手工修改后出现机器数据与人工报告不一致。

English: `validate-report` checks more than JSON Schema. It recalculates source inventory, usage cost, risk-register totals, coverage totals, comparison regression counts, QA receipt readiness, manifest binding, and Markdown/HTML sidecar summaries so edited reports cannot silently diverge from machine data.

常用验证命令 / Common verification commands:

```bash
python -m forgedan.cli suite validate-report reports/suite-ready/suite-result.json
python -m forgedan.cli suite verify-bundle reports/suite-ready/suite-manifest.json
python -m forgedan.cli suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff
python -m forgedan.cli suite verify-archive reports/suite-ready/handoff.zip
```

---

<a id="capabilities"></a>
## 核心能力 / Key Capabilities

| 能力 / Area | 中文 | English |
| --- | --- | --- |
| Report suites | YAML suite、内联/导入用例、响应缓存、确定性种子、策略门禁、运行前预检。 | YAML suite definitions, inline or imported cases, replay caches, deterministic seeds, policy gates, and preflight readiness checks. |
| Report artifacts | Markdown/HTML 报告、执行摘要、证据 CSV、case matrix、风险登记、覆盖率摘要、发布说明、bundle index。 | Markdown/HTML reports, executive summaries, evidence CSVs, case matrices, risk registers, coverage summaries, release notes, and bundle indexes. |
| Evidence integrity | JSON Schema、制品 manifest、SHA256/大小校验、跨制品一致性校验、脱敏发布泄漏检查。 | JSON Schemas, artifact manifests, SHA256/size checks, cross-artifact consistency, and redacted-publication leak checks. |
| Handoff QA | QA receipt JSON/Markdown、验收准则、评审决策、owner/due date、严格交接门禁。 | QA receipt JSON/Markdown, acceptance criteria, reviewer decisions, owner/due-date tracking, and strict handoff gates. |
| Assessment coverage | Prompt Injection、越狱角色扮演、系统提示泄漏、敏感信息/PII、Agent/MCP/工具策略风险、模型制品信号。 | Prompt injection, jailbreak roleplay, system prompt leakage, secrets/PII exposure, Agent/MCP/tool policy risk, and model artifact signals. |
| Baseline engine | FORGEDAN、AutoDAN、PAIR、GCG、Crescendo、TAP、模型适配器、WebScan、CLI、REST API、Vue dashboard。 | FORGEDAN, AutoDAN, PAIR, GCG, Crescendo, TAP, model adapters, WebScan, CLI, REST API, and Vue dashboard. |

---

<a id="cli-reference"></a>
## 常用 CLI / CLI Reference

| 场景 / Scenario | 命令 / Command | 中文说明 | English Notes |
| --- | --- | --- | --- |
| 运行 suite / Run a suite | `python -m forgedan.cli suite run examples/smoke-suite.yml` | 从 YAML suite 生成报告输出。 | Generate report outputs from a YAML suite. |
| 按 run ID 输出 / Per-run output dirs | `python -m forgedan.cli suite run examples/smoke-suite.yml --run-id-dir` | 使用 run ID 隔离输出目录。 | Isolate output directories by run ID. |
| 运行预检 / Run preflight | `python -m forgedan.cli suite preflight examples/ready-for-handoff-suite.yml --strict --output reports/preflight-ready` | 在消耗模型预算前检查报告准备度。 | Check report readiness before spending model budget. |
| 校验报告制品 / Validate report | `python -m forgedan.cli suite validate-report reports/suite-ready/suite-result.json` | 校验 schema 和语义一致性。 | Validate schema and semantic consistency. |
| 验证目录包 / Verify bundle | `python -m forgedan.cli suite verify-bundle reports/suite-ready/suite-manifest.json` | 校验 manifest、hash、sidecar 和跨制品一致性。 | Verify manifest, hashes, sidecars, and cross-artifact consistency. |
| 生成 QA 回执 / Write QA receipt | `python -m forgedan.cli suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff` | 生成严格交接回执。 | Write a strict handoff QA receipt. |
| 创建 ZIP / Create ZIP | `python -m forgedan.cli suite archive reports/suite-ready/suite-manifest.json --output reports/suite-ready/handoff.zip` | 创建单文件交付包。 | Create a single-file handoff package. |
| 验证 ZIP / Verify ZIP | `python -m forgedan.cli suite verify-archive reports/suite-ready/handoff.zip` | 复制或分享后复核归档。 | Re-check the archive after copying or sharing. |
| 对比结果 / Compare results | `python -m forgedan.cli suite compare base.json current.json --output comparison.json --fail-on-regression` | 生成历史对比并可在回归时失败。 | Generate historical comparison and optionally fail on regressions. |
| 导出 taxonomy / Export taxonomy | `python -m forgedan.cli suite taxonomy --json` | 导出 finding taxonomy。 | Export the finding taxonomy. |
| 导出 schemas / Export schemas | `python -m forgedan.cli suite schemas --json` | 导出报告制品 schema references。 | Export report artifact schema references. |
| 攻击 demo / Attack demo | `python -m forgedan.cli run --quick -g "test prompt" -m mock:test` | 使用 mock 模型运行零配置 demo。 | Run a zero-config demo with the mock model. |
| Web 后端 / Web backend | `python -m forgedan.cli web` | 启动 API/web 后端。 | Start the API/web backend. |

---

<a id="attack-methods"></a>
## 攻击方法 / Attack Methods

| 方法 / Method | 类型 / Type | 中文 | English | 论文 / Paper |
| --- | --- | --- | --- | --- |
| FORGEDAN | Evolutionary | 多层级 mutation，结合语义适应度和双 judge。 | Multi-level mutation with semantic fitness and dual judge. | [arXiv:2511.13548](https://arxiv.org/abs/2511.13548) |
| AutoDAN | Evolutionary | 面向隐蔽越狱 prompt 的层次化遗传算法。 | Hierarchical genetic algorithm for stealthy jailbreak prompts. | [ICLR 2024](https://arxiv.org/abs/2310.04451) |
| PAIR | LLM-iterative | 通过 attacker-target LLM 迭代完成黑盒越狱。 | Black-box jailbreak via attacker-target LLM iteration. | [NeurIPS 2024](https://arxiv.org/abs/2310.08419) |
| GCG | Gradient-free | 基于贪心坐标搜索的 adversarial suffix 生成。 | Greedy coordinate adversarial suffix generation. | [ICML 2023](https://arxiv.org/abs/2307.15043) |
| Crescendo | Multi-turn | 从低风险内容逐步升级到高风险请求的多轮攻击。 | Gradual escalation from benign to harmful content. | [USENIX Security 2025](https://arxiv.org/abs/2404.01833) |
| TAP | Tree search | Tree-of-thought 攻击搜索，带剪枝和多 LLM 协作。 | Tree-of-thought attack with pruning and multi-LLM collaboration. | [NeurIPS 2024](https://arxiv.org/abs/2312.02119) |

---

<a id="model-adapters"></a>
## 模型适配器 / Model Adapters

| Provider | 模型范围 / Models | 配置示例 / Example |
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
| Ollama | 本地 Ollama 模型 / Local Ollama models | `ollama:llama2` |
| vLLM | 本地 vLLM 服务 / Local vLLM services | `vllm:model-name` |
| HuggingFace | HuggingFace 模型 / HuggingFace models | `huggingface:model-name` |
| Mock | 本地测试，无需 API key / Local testing, no API key | `mock:test-model` |

---

<a id="webscan"></a>
## WebScan 模式 / WebScan Modes

| 模式 / Mode | 中文 | English | 适用场景 / Use Case |
| --- | --- | --- | --- |
| URL crawler | 异步抓取页面标题、表单、链接和脚本。 | Async crawling plus title, form, link, and script extraction. | 收集目标站点中的攻击素材 / Gather attack material from target websites. |
| Security scanner | 检查 XSS、SQLi、路径穿越、安全 Header 和 HTTP Method。 | XSS, SQLi, directory traversal, security headers, and HTTP methods. | 传统 Web 漏洞评估 / Traditional web vulnerability assessment. |
| LLM interaction test | 使用网页内容触发间接 Prompt Injection，并结合进化式优化。 | Indirect prompt injection via web content and evolutionary optimization. | 评估 LLM 处理网页内容时的安全性 / Test LLM safety when processing web content. |

---

<a id="architecture"></a>
## 架构概览 / Architecture

```text
forgedan/
├── suite.py              # 报告套件运行器 / Suite runner, artifacts, validators, QA, archive verifier
├── scanners.py           # 确定性扫描器 / Deterministic prompt, response, tool, model-artifact scanners
├── scorers.py            # 可复用评分器 / Reusable deterministic suite scorers
├── finding_taxonomy.py   # finding taxonomy、优先级、OWASP LLM 映射 / Finding IDs, priorities, OWASP LLM mappings
├── attacks/              # 攻击算法与注册表 / Attack algorithms and registry
├── adapters/             # 托管、本地、中文、vision、vLLM、HuggingFace、mock adapters
├── api/                  # Flask Blueprint REST API
├── webscan/              # crawler、web scanner、LLM interaction tester
├── engine.py             # 进化算法引擎 / Evolutionary algorithm engine
├── mutator.py            # mutation strategies 和 MAB 选择 / Mutation strategies and MAB selection
├── fitness.py            # 语义适应度 / Semantic fitness evaluation
└── judge.py              # 双 judge 机制 / Dual-judge mechanism

schemas/                  # 报告制品 JSON Schema 合约 / Report artifact JSON Schema contracts
examples/                 # 可运行 suite 和 fixture / Runnable suites and fixtures
docs/                     # 同类项目扫描、lint roadmap、样例报告包 / Landscape, lint roadmap, sample report pack
tests/                    # pytest coverage
frontend/                 # Vue 3 SPA dashboard
```

中文：`forgedan/suite.py` 是报告交付主入口，负责 suite 运行、报告制品写入、schema/manifest 校验、QA 回执和归档复核。`schemas/` 约束报告制品，`examples/` 保存可运行 fixture，`docs/` 保存样例报告包和项目说明，`frontend/` 保存 Vue 3 仪表盘。

English: `forgedan/suite.py` is the report-delivery entry point. It handles suite execution, report artifact writing, schema/manifest validation, QA receipts, and archive verification. `schemas/` defines artifact contracts, `examples/` stores runnable fixtures, `docs/` keeps sample report packs and project documentation, and `frontend/` contains the Vue 3 dashboard.

---

<a id="api-endpoints"></a>
## API 端点 / API Endpoints

中文：后端使用 Flask Blueprint 暴露 REST API，适合自动化脚本、演示环境和内部评估流程接入。

English: The backend exposes a Flask Blueprint REST API for automation scripts, demos, and internal assessment workflows.

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

---

<a id="documentation"></a>
## 文档导航 / Documentation Map

| 文档 / Document | 中文 | English |
| --- | --- | --- |
| [docs/sample-report-pack/ready-for-handoff/](docs/sample-report-pack/ready-for-handoff/README.md) | 已提交的 mock 样例报告包，包含 QA 回执和已校验 ZIP。 | Checked-in mock report pack with QA receipt and verified ZIP archive. |
| [docs/llm-security-landscape.md](docs/llm-security-landscape.md) | 同类项目扫描、能力差距和优化优先级。 | Competitor scan, gaps, and optimization priorities. |
| [docs/lint-roadmap.md](docs/lint-roadmap.md) | 当前 CI lint 门禁、历史债务统计和更严格质量门禁推进路径。 | Current CI lint gate, measured lint debt, and promotion plan. |
| [docs/repository-about.md](docs/repository-about.md) | 仓库侧栏描述和 topic 建议。 | Repository sidebar wording and topic recommendations. |
| [schemas/](schemas/) | 报告制品 JSON Schema 合约。 | JSON Schema contracts for report artifacts. |
| [examples/](examples/) | 可运行 suite、case fixture、MCP manifest、模型制品 fixture。 | Runnable suites, case fixtures, MCP manifests, and model artifact fixtures. |

---

<a id="development"></a>
## 开发与验证 / Development

```bash
pip install -e ".[dev]"

# 本地全量 pytest / Full pytest suite used locally
python -m pytest -q -W error::DeprecationWarning -p no:cacheprovider --basetemp .tmp-test

# CI 报告包门禁 / CI report-pack gates
python -m forgedan.cli suite run examples/ready-for-handoff-suite.yml --output reports/suite-ready
python -m forgedan.cli suite verify-bundle reports/suite-ready/suite-manifest.json
python -m forgedan.cli suite qa-report reports/suite-ready/suite-manifest.json --output reports/suite-ready/qa --strict-handoff
python -m forgedan.cli suite verify-archive reports/suite-ready/handoff.zip

# flake8 选定门禁 / Selected flake8 gate
python -m flake8 forgedan/ --select=E9,F63,F7,F82,E722,F401,F841 --show-source --statistics

# 格式化门禁 / Formatter gate
python -m black --check forgedan tests

# 前端构建 / Frontend build
cd frontend
npm install
npm run build
```

---

<a id="roadmap"></a>
## 当前路线图 / Roadmap

- [x] 进化算法引擎与 mutation strategy / Evolutionary engine and mutation strategies
- [x] 6 种攻击方法：FORGEDAN、AutoDAN、PAIR、GCG、Crescendo、TAP / Six attack methods: FORGEDAN, AutoDAN, PAIR, GCG, Crescendo, TAP
- [x] 托管、中文、本地、vLLM、HuggingFace、vision 和 mock adapter / Hosted, Chinese, local, vLLM, HuggingFace, vision, and mock adapters
- [x] YAML suite runner、导入 case、自定义 scorer、响应缓存、Source Inventory 和 policy gates / YAML suite runner with imported cases, custom scorers, response cache, source inventory, and policy gates
- [x] Prompt Injection、越狱框架、系统提示泄漏、敏感信息/PII、Agent/MCP/工具策略风险和模型制品扫描 / Prompt injection, jailbreak framing, system prompt leakage, secrets/PII, Agent/MCP/tool policy risk, and model artifact scanning
- [x] Markdown/HTML 报告、脱敏发布包、证据矩阵、case matrix、风险登记、覆盖率摘要、发布说明和 bundle index / Markdown/HTML reports, redacted publication packs, evidence matrices, case matrices, risk registers, coverage summaries, release notes, and bundle indexes
- [x] JSON Schema 合约、语义校验、manifest verification、QA receipt 和 archive verification / JSON Schema contracts, semantic validation, manifest verification, QA receipts, and archive verification
- [x] 已提交 ready-for-handoff 样例报告包和截图 / Checked-in ready-for-handoff sample report pack with screenshots
- [x] CI 覆盖 tests、报告包校验、严格 QA 交接、归档校验、selected flake8、Black 和 frontend build / CI gates for tests, report-pack validation, strict QA handoff, archive verification, selected flake8, Black, and frontend build
- [ ] 增加更多真实 Agent/MCP manifest fixture，校准默认 trust-score policy / Add more realistic Agent/MCP manifest fixtures and calibrate the default trust-score policy
- [ ] 仅在能提升报告证据质量时加入 HarmBench/JailbreakBench 示例 / Add HarmBench/JailbreakBench examples only where they improve report evidence quality
- [ ] 当报告范围需要时扩展更深的 model serialization 分析 / Expand model serialization analysis when the report scope needs deeper artifact review

---

<a id="github-about"></a>
## GitHub About 建议 / GitHub About

仓库侧栏描述建议 / Suggested repository description:

> 面向报告交付的 LLM 安全评估框架，用于生成可复现红队套件、证据包、QA 回执、Schema 合约和可校验归档。

> Report-first LLM security assessment framework for reproducible red-team suites, evidence packs, QA receipts, schemas, and archive verification.

建议 Topics / Suggested topics:

`llm-security`, `ai-red-team`, `prompt-injection`, `jailbreak`, `owasp-llm`, `mcp-security`, `agent-security`, `security-reporting`, `risk-register`, `audit-evidence`, `json-schema`, `pytest`, `python`

---

<a id="citation"></a>
## 引用 / Citation

中文：如果在研究中使用 FORGEDAN，请引用：

English: If you use FORGEDAN in research, please cite:

```bibtex
@article{cheng2025forgedan,
  title={FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models},
  author={Cheng, Siyang and Liu, Gaotian and Mei, Rui and Wang, Yilin and Zhang, Kejia and Wei, Kaishuo and Yu, Yuqi and Wen, Weiping and Wu, Xiaojie and Liu, Junhua},
  journal={arXiv preprint arXiv:2511.13548},
  year={2025}
}
```

---

<a id="contributing"></a>
## 贡献 / Contributing

中文：欢迎提交改进。修改报告行为时，请同步维护报告制品、Schema、测试和文档。通用贡献流程见 [CONTRIBUTING.md](CONTRIBUTING.md)。

English: Contributions are welcome. When changing report behavior, keep report artifacts, schemas, tests, and documentation aligned. See [CONTRIBUTING.md](CONTRIBUTING.md) for the general contribution flow.

---

<a id="security"></a>
## 安全说明 / Security

中文：本项目仅用于授权安全测试、研究复现和报告交付。原始 prompt、response、trace、cache 和 evidence 可能包含敏感数据，应按评估范围和交接规则管理。

English: Use this project only for authorized security testing, research reproduction, and report delivery. Raw prompts, responses, traces, caches, and evidence may contain sensitive data; handle them according to the assessment scope and handoff rules.

---

<a id="license"></a>
## 许可证 / License

中文：本项目使用 MIT License，详见 [LICENSE](LICENSE)。

English: This project is released under the MIT License. See [LICENSE](LICENSE).

---

<div align="center">

**Built by [Coff0xc](https://github.com/Coff0xc)**

[Report Bug](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues) ·
[Request Feature](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues)

</div>

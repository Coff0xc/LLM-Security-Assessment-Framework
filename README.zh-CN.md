<div align="center">

# FORGEDAN

### 面向报告交付的 LLM 安全评估框架
### Report-first LLM Security Assessment Framework

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/arXiv-2511.13548-b31b1b.svg)](https://arxiv.org/abs/2511.13548)
[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![Tests](https://img.shields.io/badge/tests-257%20passed%20%2F%204%20skipped-brightgreen.svg)]()
[![Report Pack](https://img.shields.io/badge/report%20pack-schema%20verified-2ea44f.svg)]()

**可复现套件 | 证据化报告包 | QA 交接回执 | 归档校验**

[English](README.md) · [简体中文](README.zh-CN.md)

[快速开始](#快速开始) · [使用截图](#使用截图) · [报告工作流](#报告工作流) · [报告包组成](#报告包组成) · [开发与验证](#开发与验证)

</div>

---

## 项目定位

**FORGEDAN** 基于论文 [*FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models*](https://arxiv.org/abs/2511.13548)，但当前项目重点已经从单纯的越狱算法演示扩展为 **LLM 安全评估报告交付框架**。

它面向授权安全评估、研究复现和报告交付场景，帮助评估团队生成可审计、可复核、可交接的报告包：YAML 套件、确定性扫描器与评分器、证据矩阵、风险登记、覆盖率摘要、JSON Schema 合约、QA 回执、脱敏发布包，以及复制或分享后仍可重新校验的 ZIP 归档。

项目仍保留进化式越狱攻击、模型适配器、WebScan、REST API 和 Vue 仪表盘；但当前目标不是商业化平台，而是让报告证据、审计链路和交付质量更稳。

## 核心能力

| 能力 | English | 中文说明 |
|------|---------|----------|
| Report Suites | YAML suite definitions, imported cases, replay caches, deterministic seeds, policy gates, preflight checks | YAML 套件、导入用例、响应缓存、确定性种子、策略门禁、运行前预检 |
| Report Artifacts | Markdown/HTML reports, evidence CSVs, risk registers, coverage summaries, release notes | Markdown/HTML 报告、证据矩阵、风险登记、覆盖率摘要、发布说明 |
| Evidence Integrity | JSON Schemas, manifests, SHA256/size checks, cross-artifact consistency | JSON Schema、制品清单、SHA256/大小校验、跨制品一致性校验 |
| Handoff QA | QA receipts, acceptance criteria, reviewer decisions, owner/due-date tracking | QA 回执、验收准则、评审决策、风险 owner 与到期日 |
| Assessment Coverage | Prompt injection, jailbreak framing, secret/PII exposure, Agent/MCP/tool risk, model artifact signals | Prompt Injection、越狱框架、敏感信息/PII、Agent/MCP/工具风险、模型制品信号 |
| Baseline Engine | FORGEDAN, AutoDAN, PAIR, GCG, Crescendo, TAP, model adapters, WebScan, API, dashboard | 多种攻击算法、模型适配器、WebScan、API 和仪表盘能力 |

## Repository About 建议

GitHub 仓库侧栏建议使用：

> 面向报告交付的 LLM 安全评估框架，用于生成可复现红队套件、证据包、QA 回执、Schema 合约和可校验归档。

对应英文：

> Report-first LLM security assessment framework for reproducible red-team suites, evidence packs, QA receipts, schemas, and archive verification.

建议 Topics：

`llm-security`, `ai-red-team`, `prompt-injection`, `jailbreak`, `owasp-llm`, `mcp-security`, `agent-security`, `security-reporting`, `risk-register`, `audit-evidence`, `json-schema`, `pytest`, `python`

---

## 架构概览

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

---

## 使用截图

下面的截图来自 `examples/ready-for-handoff-suite.yml` 生成的真实报告交付链路，展示当前项目最核心的报告包、QA 回执和归档校验能力。

### 报告包总览

![报告包总览](docs/screenshots/report-overview.png)

### QA 交接回执

![QA 交接回执](docs/screenshots/qa-receipt.png)

### 归档校验

![归档校验](docs/screenshots/archive-verification.png)

---

## 快速开始

### 前置要求

- Python >= 3.9
- Node.js >= 18，只有运行前端时需要
- Git

### 安装

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

### 生成可交付报告包

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

### 运行攻击 Demo

```bash
forgedan run --quick -g "test prompt" -m mock:test
```

### 运行 Web Dashboard

```bash
forgedan web
cd frontend
npm run dev
```

后端默认在 `:5000`，前端默认在 `:5173`。

---

## 报告工作流

1. **定义评估范围**：在 suite YAML 中配置 cases、导入证据源、报告元数据、策略门禁、覆盖率要求、验收准则、评审决策和风险登记默认值。
2. **运行预检**：使用 `forgedan suite preflight` 在消耗模型预算前检查元数据、交接准则、scorer 名称、来源证明和确定性 replay 设置。
3. **生成报告包**：使用 `forgedan suite run` 写出原始与脱敏 JSON/JSONL、Markdown/HTML 报告、CSV 矩阵、覆盖率、风险登记、发布说明和 manifest。
4. **本地验证**：使用 `forgedan suite validate-report` 与 `forgedan suite verify-bundle` 校验 schema、hash、摘要计数、脱敏制品、Markdown/HTML sidecar 与跨制品身份。
5. **准备交接**：使用 `forgedan suite qa-report --strict-handoff` 生成 QA 回执，记录 checklist、blocker、验收准则、Source Inventory、schema 校验和人工评审证据。
6. **归档并复核**：使用 `forgedan suite archive` 和 `forgedan suite verify-archive` 生成单文件 ZIP，并在复制或分享后重新校验。普通报告包和历史对比报告都支持同一归档流程。

---

## 常用 CLI

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

更完整的 CLI 说明见英文版 [README.md](README.md#cli-reference)。

---

## 报告包组成

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

---

## JSON Schema 与验证

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

---

## 开发与验证

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

---

## 当前路线图

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

---

## 引用

如果在研究中使用 FORGEDAN，请引用：

```bibtex
@article{cheng2025forgedan,
  title={FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models},
  author={Cheng, Siyang and Liu, Gaotian and Mei, Rui and Wang, Yilin and Zhang, Kejia and Wei, Kaishuo and Yu, Yuqi and Wen, Weiping and Wu, Xiaojie and Liu, Junhua},
  journal={arXiv preprint arXiv:2511.13548},
  year={2025}
}
```

---

## 安全说明

本项目仅用于授权安全测试、研究复现和报告交付。测试任何系统前请确认授权范围、评估目标、数据边界和交付对象。原始 prompt、response、case trace、缓存和 evidence 可能包含敏感信息，应按评估报告证据管理要求限制访问。

---

## 许可证

本项目使用 MIT License，详见 [LICENSE](LICENSE)。

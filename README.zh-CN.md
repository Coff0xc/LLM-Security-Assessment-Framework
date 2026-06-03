<div align="center">

# FORGEDAN

### 面向报告交付的 LLM 安全评估框架
### Report-first LLM Security Assessment Framework

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/arXiv-2511.13548-b31b1b.svg)](https://arxiv.org/abs/2511.13548)
[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![Tests](https://img.shields.io/badge/tests-261%20passed%20%2F%204%20skipped-brightgreen.svg)]()
[![Report Pack](https://img.shields.io/badge/report%20pack-schema%20verified-2ea44f.svg)]()

**可复现套件 | 证据化报告包 | QA 交接回执 | 归档校验**

[主 README：完整中英双语对照](README.md) · [简体中文独立版](README.zh-CN.md)

[快速开始](#快速开始) · [使用截图](#使用截图) · [文档导航](#文档导航) · [攻击方法](#攻击方法) · [报告工作流](#报告工作流) · [报告包组成](#报告包组成) · [API 端点](#api-端点) · [开发与验证](#开发与验证)

</div>

---

## README 格式说明

主 [README.md](README.md) 采用 **完整中英双语对照** 结构。每个主要章节都同时给出 English 与中文说明，覆盖相同的项目定位、截图、快速 smoke path、报告工作流、制品清单、校验门禁、开发命令、路线图、安全说明和许可证。

本文件是独立中文版本，便于中文评审人、报告接收方或内部交接场景直接阅读与转发。需要中英对照时，请使用主 [README.md](README.md)。

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

完整可渲染样例包见 [docs/sample-report-pack/ready-for-handoff](docs/sample-report-pack/ready-for-handoff/README.md)。

### 报告包总览

![报告包总览](docs/screenshots/report-overview.png)

### QA 交接回执

![QA 交接回执](docs/screenshots/qa-receipt.png)

### 归档校验

![归档校验](docs/screenshots/archive-verification.png)

---

## 文档导航

| 文档 | 用途 |
|------|------|
| [docs/llm-security-landscape.md](docs/llm-security-landscape.md) | 同类项目扫描、差异化定位和后续优化优先级 |
| [docs/lint-roadmap.md](docs/lint-roadmap.md) | 当前 CI lint 门禁、历史债务统计和更严格质量门禁推进路径 |
| [docs/sample-report-pack/ready-for-handoff/](docs/sample-report-pack/ready-for-handoff/README.md) | 可直接查看的 mock 样例报告包，包含 QA 回执和已校验 ZIP |
| [README.md](README.md) | 主 README，全量英文 + 中文说明 |
| [schemas/](schemas/) | 报告制品 JSON Schema 合约，用于机器校验与交付验收 |
| [examples/](examples/) | 可运行 suite 样例、case fixture、MCP manifest 和模型制品输入样例 |

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

## 攻击方法

| 方法 | 类型 | 中文说明 | 论文 |
|------|------|----------|------|
| **FORGEDAN** | Evolutionary | 多层级字符/词/句变异，结合语义适应度和双 judge 机制 | [arXiv:2511.13548](https://arxiv.org/abs/2511.13548) |
| **AutoDAN** | Evolutionary | 面向隐蔽越狱 prompt 的层次化遗传算法 | [ICLR 2024](https://arxiv.org/abs/2310.04451) |
| **PAIR** | LLM-iterative | 通过 attacker-target LLM 迭代完成黑盒越狱 | [NeurIPS 2024](https://arxiv.org/abs/2310.08419) |
| **GCG** | Gradient-free | 基于贪心坐标搜索的 adversarial suffix 生成 | [ICML 2023](https://arxiv.org/abs/2307.15043) |
| **Crescendo** | Multi-turn | 从低风险内容逐步升级到高风险请求的多轮攻击 | [USENIX Security 2025](https://arxiv.org/abs/2404.01833) |
| **TAP** | Tree search | Tree-of-thought 攻击搜索，带剪枝与多 LLM 协作 | [NeurIPS 2024](https://arxiv.org/abs/2312.02119) |

---

## 模型适配器

| Provider | 模型范围 | 配置示例 |
|----------|----------|----------|
| OpenAI | GPT-3.5、GPT-4、GPT-4o | `openai:gpt-4` |
| Anthropic | Claude 3 Opus/Sonnet/Haiku | `anthropic:claude-3-opus` |
| Google | Gemini Pro、Gemini Vision | `gemini:gemini-pro` |
| DeepSeek | DeepSeek-Chat、DeepSeek-Coder | `deepseek:deepseek-chat` |
| Zhipu / 智谱 | GLM-4、GLM-3 | `zhipu:glm-4` |
| Qwen / 通义千问 | Qwen-Max、Qwen-Plus | `qwen:qwen-max` |
| Moonshot / 月之暗面 | Kimi | `moonshot:moonshot-v1-8k` |
| Yi / 零一万物 | Yi-Large、Yi-Medium | `yi:yi-large` |
| Baichuan / 百川 | Baichuan-4、Baichuan-3 | `baichuan:baichuan-4` |
| Ollama | 任意本地 Ollama 模型 | `ollama:llama2` |
| vLLM | 高性能本地推理服务 | `vllm:model-name` |
| HuggingFace | 任意 HuggingFace 模型 | `huggingface:model-name` |
| Mock | 本地测试，无需 API key | `mock:test-model` |

---

## Web 扫描

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| URL Crawler | 异步抓取页面标题、表单、链接和脚本 | 收集目标站点中的攻击素材与上下文 |
| Security Scanner | 检查 XSS、SQLi、路径穿越、安全 Header 和 HTTP Method 暴露 | 传统 Web 漏洞评估 |
| LLM Interaction Test | 使用网页内容触发间接 Prompt Injection，并结合进化式优化 | 评估 LLM 处理网页内容时的安全性 |

---

## 报告工作流

1. **定义评估范围**：在 suite YAML 中配置 cases、导入证据源、报告元数据、策略门禁、覆盖率要求、验收准则、评审决策和风险登记默认值。
2. **运行预检**：使用 `forgedan suite preflight` 在消耗模型预算前检查元数据、交接准则、scorer 名称、来源证明和确定性 replay 设置。
3. **生成报告包**：使用 `forgedan suite run` 写出原始与脱敏 JSON/JSONL、Markdown/HTML 报告、CSV 矩阵、覆盖率、风险登记、发布说明和 manifest。
4. **本地验证**：使用 `forgedan suite validate-report` 与 `forgedan suite verify-bundle` 校验 schema、hash、摘要计数、脱敏制品、Markdown/HTML sidecar 与跨制品身份。
5. **准备交接**：使用 `forgedan suite qa-report --strict-handoff` 生成 QA 回执，记录 checklist、blocker、验收准则、Source Inventory、schema 校验和人工评审证据。
6. **归档并复核**：使用 `forgedan suite archive` 和 `forgedan suite verify-archive` 生成单文件 ZIP，并在复制或分享后重新校验。生成的 release notes 和完整 report bundle index 会写入这些交接命令，`verify-bundle` 会回查它们是否仍然存在。普通报告包会在 ZIP 内重新做跨制品一致性校验，历史对比报告也支持同一归档流程。

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

更完整的 CLI 说明见主 [README.md](README.md#cli-reference--常用-cli)。

---

## CLI 能力分组

| 场景 | 关键命令 | 说明 |
|------|----------|------|
| 报告套件运行 | `forgedan suite run` | 从 YAML suite 生成完整报告包 |
| 运行前预检 | `forgedan suite preflight` | 在消耗模型预算前检查报告元数据、验收条件、来源证明和策略门禁 |
| 报告制品校验 | `forgedan suite validate-report` | 校验 JSON Schema，并复核 Source Inventory、usage、risk、coverage 和 Markdown/HTML 摘要 |
| 目录包完整性 | `forgedan suite verify-bundle` | 校验 manifest、hash、schema、sidecar 和跨制品一致性 |
| QA 交接 | `forgedan suite qa-report --strict-handoff` | 生成 JSON/Markdown QA 回执，并在交接条件不满足时失败 |
| 单文件归档 | `forgedan suite archive` / `forgedan suite verify-archive` | 生成 ZIP，并在复制或分享后重新校验 hash、schema 和归档内跨制品一致性 |
| 历史对比 | `forgedan suite compare` | 比较两个 suite result，输出 regression、policy-domain delta 和对比 manifest |
| Taxonomy / Schema 导出 | `forgedan suite taxonomy` / `forgedan suite schemas` | 导出 finding taxonomy 和报告制品 schema references |
| 攻击 Demo | `forgedan run --quick` | 使用 mock 或真实模型快速演示攻击流程 |
| Web Dashboard | `forgedan web` + `npm run dev` | 启动 Flask API 与 Vue 3 前端 |

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
| `suite-release-notes.md` | 授权评审人 | 简短运行说明、风险、验收、Source Inventory、reviewer decision、制品指针和归档交接命令 |
| 脱敏 report/result/cases | 外部评审人 | 低敏发布包，隐藏原始 prompt、response 和 evidence |
| `suite-manifest.json` | 评估团队 | 含大小、SHA256、schema references、敏感度、受众分类和验收状态的完整性清单 |
| `suite-qa-receipt.json` / `suite-qa-receipt.md` | 评估负责人 | 交接回执，覆盖 manifest、schema、hash、跨制品一致性、预检、验收、risk owner 和限制项 |
| `handoff.zip` | 交付接收方 | 可在复制或分享后用 `verify-archive` 重新校验的单文件交付包；suite 归档会在同目录存在 QA 回执时一并带上 |

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

## API 端点

后端使用 Flask Blueprint 暴露 REST API，适合把报告能力接入自动化脚本、内部评估平台或演示仪表盘。

```bash
# Attacks
POST   /api/attacks/run
GET    /api/attacks/{id}/status
GET    /api/attacks/{id}/result
POST   /api/attacks/{id}/stop

# Models
GET    /api/models/providers
POST   /api/models/test

# Web Scanning
POST   /api/webscan/crawl
POST   /api/webscan/scan
POST   /api/webscan/llm-test

# Reports
POST   /api/reports/generate
GET    /api/reports/{id}
GET    /api/reports/{id}/download

# Datasets
GET    /api/datasets
POST   /api/datasets/upload

# Monitoring
GET    /api/health
GET    /api/metrics
```

---

## 项目结构

```text
LLM-Security-Assessment-Framework/
├── forgedan/                  # Python package
│   ├── api/                   # Flask Blueprint REST API
│   ├── attacks/               # 6 种攻击算法与 registry
│   ├── adapters/              # 18 类模型适配器
│   ├── webscan/               # crawler / scanner / llm_tester
│   ├── datasets/              # AdvBench 与自定义数据集管理
│   ├── defense/               # 防御训练数据生成
│   ├── distributed/           # 分布式 coordinator / worker
│   ├── monitoring/            # Prometheus metrics 与 alerting
│   ├── multimodal/            # Vision model attacks
│   ├── web/                   # Legacy Flask web app
│   ├── suite.py               # Suite runner、报告包、验证器、QA 回执、归档校验
│   ├── scanners.py            # 确定性 prompt/response/tool/model scanner
│   ├── scorers.py             # 确定性 suite scorer helper
│   ├── finding_taxonomy.py    # finding taxonomy 与 OWASP LLM 映射
│   ├── engine.py              # 进化算法引擎
│   ├── mutator.py             # 15 种 mutation strategy
│   ├── fitness.py             # 语义相似度 fitness
│   ├── judge.py               # 双 judge 机制
│   ├── config.py              # 配置管理
│   ├── cli.py                 # CLI interface
│   └── utils.py               # retry、cache、circuit breaker 等工具
├── frontend/                  # Vue 3 SPA dashboard
│   └── src/
│       ├── views/             # 页面
│       ├── components/        # 可复用组件
│       ├── stores/            # Pinia state
│       └── api/               # API client 与 WebSocket
├── schemas/                   # 生成报告制品的 JSON Schema 合约
├── examples/                  # suite、case、MCP 和 model fixture
├── docs/                      # landscape scan、lint roadmap、metadata guidance
├── tests/                     # pytest 测试
├── monitoring/                # Prometheus/Grafana 配置
├── reports/                   # 生成报告输出目录，默认不跟踪运行产物
├── pyproject.toml             # Python package config
├── .env.example               # 环境变量模板
└── LICENSE                    # MIT License
```

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
- [x] ZIP 归档内 suite 跨制品一致性校验，与目录版 `verify-bundle` 对齐
- [x] CI 覆盖 unit tests、preflight、smoke report pack、ready-for-handoff QA、handoff ZIP 归档校验、selected flake8、Black 和 frontend build
- [ ] 增加更多真实 Agent/MCP manifest fixture，校准 trust score 和默认 policy
- [ ] 仅在能提升报告证据质量时加入 HarmBench/JailbreakBench 示例
- [ ] 在报告范围需要时补更深的 model serialization 分析
- [x] 发布可渲染 ready-for-handoff 样例报告包，方便评审人在运行 CLI 前直接查看输出

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

## 贡献

欢迎提交改进。建议先阅读 [CONTRIBUTING.md](CONTRIBUTING.md)，并尽量保持报告制品、Schema、测试和 README 同步更新。

1. Fork 本仓库
2. 创建功能分支，例如 `git checkout -b feature/report-pack-improvement`
3. 提交改动，例如 `git commit -m "Improve report pack validation"`
4. Push 到你的分支
5. 创建 Pull Request，并说明报告产物、验证命令和剩余风险

---

## 安全说明

本项目仅用于授权安全测试、研究复现和报告交付。测试任何系统前请确认授权范围、评估目标、数据边界和交付对象。原始 prompt、response、case trace、缓存和 evidence 可能包含敏感信息，应按评估报告证据管理要求限制访问。

---

## 许可证

本项目使用 MIT License，详见 [LICENSE](LICENSE)。

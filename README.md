<div align="center">

# FORGEDAN

### An Evolutionary Framework for LLM Security Assessment

[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Paper](https://img.shields.io/badge/arXiv-2511.13548-b31b1b.svg)](https://arxiv.org/abs/2511.13548)
[![Vue 3](https://img.shields.io/badge/Vue-3.5-4FC08D?logo=vue.js)](https://vuejs.org/)
[![Tests](https://img.shields.io/badge/tests-124%20passed-brightgreen.svg)]()

**6 Attack Methods | 18 Model Adapters | 3 Web Scan Modes | Vue 3 Dashboard**

[Quick Start](#quick-start) · [Documentation](#documentation) · [Screenshots](#screenshots) · [Contributing](#contributing)

</div>

---

## Overview

**FORGEDAN** is a production-grade LLM security assessment framework based on the paper [*FORGEDAN: An Evolutionary Framework for Jailbreaking Aligned Large Language Models*](https://arxiv.org/abs/2511.13548). It evaluates the robustness of large language models through automated red-team testing, evolutionary jailbreak attacks, and web security scanning.

### Key Capabilities

| Category | Features |
|----------|----------|
| **Attack Methods** | FORGEDAN (evolutionary), AutoDAN, PAIR, GCG, Crescendo, TAP |
| **Model Support** | OpenAI, Anthropic, Gemini, DeepSeek, Zhipu, Qwen, Moonshot, Yi, Baichuan, Ollama, vLLM, HuggingFace + Mock |
| **Web Scanning** | URL crawling & content extraction, Web vulnerability scanning (XSS/SQLi), LLM-driven interaction testing |
| **Interface** | Vue 3 SPA dashboard, CLI, REST API, WebSocket real-time updates |
| **Enterprise** | Distributed computing, Prometheus monitoring, Grafana dashboards, defense training data generation |

---

## Architecture

```
forgedan/
├── attacks/          # 6 attack algorithms + unified registry
│   ├── forgedan.py   # Evolutionary algorithm (core)
│   ├── autodan.py    # LLM-guided automatic jailbreak
│   ├── pair.py       # Prompt Automatic Iterative Refinement
│   ├── gcg.py        # Greedy Coordinate Gradient
│   ├── crescendo.py  # Multi-turn escalation
│   ├── tap.py        # Tree of Attacks with Pruning
│   └── registry.py   # Attack method registry & discovery
├── adapters/         # 18 model adapters (unified interface)
├── api/              # Flask Blueprint REST API
│   ├── attacks.py    # Attack task endpoints
│   ├── models.py     # Model adapter endpoints
│   ├── webscan.py    # Web scanning endpoints
│   ├── reports.py    # Report management
│   ├── datasets.py   # Dataset management
│   └── auth.py       # API key authentication
├── webscan/          # Web security testing module
│   ├── crawler.py    # Async URL crawler + content extraction
│   ├── scanner.py    # XSS/SQLi/header/directory scanning
│   └── llm_tester.py # LLM-driven indirect prompt injection testing
├── engine.py         # Evolutionary algorithm engine
├── mutator.py        # 15 mutation strategies + MAB selection
├── fitness.py        # Semantic similarity fitness evaluation
├── judge.py          # Dual-judge mechanism (behavior + content)
├── defense/          # Defense training data generation
├── distributed/      # Distributed computing support
└── monitoring/       # Prometheus metrics & alerting

frontend/             # Vue 3 SPA dashboard
├── src/views/        # 7 pages (Dashboard, AttackTest, WebScan, Reports, Models, Datasets, Settings)
├── src/components/   # Reusable components (EvolutionMonitor, ModelSelector, etc.)
└── src/stores/       # Pinia state management
```

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
# Option 1: CLI (zero config, mock mode)
forgedan run --quick -g "test prompt" -m mock:test

# Option 2: Web Dashboard
forgedan web                        # Backend at :5000
cd frontend && npm run dev          # Frontend at :5173 → open http://localhost:5173

# Option 3: Python API
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

---

## Documentation

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

### CLI Reference

```bash
forgedan run -g "goal" -m "provider:model"   # Run attack
forgedan run --quick -g "goal"                # Quick demo (3 iterations)
forgedan test -m "provider:model"             # Test model connectivity
forgedan report --input logs/attacks/          # Generate report
forgedan web                                  # Launch web dashboard
forgedan defense generate --input logs/        # Generate defense training data
forgedan info                                 # Show framework info
forgedan distributed coordinator              # Start distributed coordinator
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

## Screenshots

> **Dashboard** — Real-time statistics, ASR trends, attack method distribution

> **Attack Test** — 6 methods, dynamic parameter forms, live evolution monitoring

> **Web Scan** — URL crawling, vulnerability scanning, LLM interaction testing

> **Reports** — Side-by-side comparison, export to PDF/CSV

---

## Project Structure

```
LLM-Security-Assessment-Framework/
├── forgedan/                  # Python backend (core framework)
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
├── tests/                     # Pytest test suite (124/127 passing)
├── monitoring/                # Prometheus/Grafana configs
├── reports/                   # Generated assessment reports
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
black forgedan/                   # Format
flake8 forgedan/                  # Lint
mypy forgedan/                    # Type check
```

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
- [x] 18 model adapters (international + Chinese + local)
- [x] Vue 3 SPA dashboard with dark theme
- [x] Web security scanning (crawler + scanner + LLM tester)
- [x] Flask Blueprint REST API
- [x] Security hardening (no pickle, HMAC auth, CORS config)
- [ ] HarmBench / JailbreakBench standard benchmark integration
- [ ] GPU-accelerated fitness computation (Ray)
- [ ] Multi-tenant support with quota enforcement
- [ ] Automated CI/CD pipeline
- [ ] Docker Compose one-click deployment

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

<div align="center">

**Built with** ❤️ **by [Coff0xc](https://github.com/Coff0xc)**

[Report Bug](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues) · [Request Feature](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues)

</div>

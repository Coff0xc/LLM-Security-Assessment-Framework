# FORGEDAN Development Documentation

> Documents the project's technical details, architecture, and development guide

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Core Modules](#core-modules)
- [Development Environment](#development-environment)
- [Testing Guide](#testing-guide)
- [Contributing Guide](#contributing-guide)
- [Changelog](#changelog)

---

## Project Overview

### Tech Stack

| Component | Technology | Version |
|------|------|------|
| Language | Python | 3.8+ |
| Config validation | Pydantic | 2.0+ |
| Async framework | asyncio | built-in |
| HTTP client | httpx | 0.24+ |
| Embedding model | sentence-transformers | 2.0+ |
| Test framework | pytest | 7.0+ |
| CLI framework | Click | 8.0+ |
| Web framework | Flask | 3.0+ |
| Monitoring system | Prometheus + Grafana | - |

### Project Structure

`
forgedan/
├── __init__.py              # Package initialization
├── config.py                # Configuration management
├── engine.py                # Evolutionary algorithm engine
├── mutator.py               # Mutation strategies
├── fitness.py               # Fitness evaluation
├── judge.py                 # Dual judges
├── logger.py                # Logging system
├── utils.py                 # Utility functions
├── attack_logger.py         # Attack logging
├── visualizer.py            # Visualization reports
├── cli.py                   # Command-line interface
├── template_manager.py      # Template manager
├── adapters/                # Model adapters
├── attacks/                 # Attack methods
├── defense/                 # Defense modules
├── distributed/             # Distributed support
├── monitoring/              # Monitoring integration
└── multimodal/              # Multimodal support
`

---

## Changelog

### v1.2.0 (2026-02-02)

#### 🚀 New Features
- **Full model coverage**: added support for Gemini, DeepSeek, Moonshot, Zhipu AI, Baichuan, and more.
- **Advanced attack algorithms**: integrated the Crescendo and TAP attack methods.
- **Multimodal support**: added security assessment support for vision models.
- **Real-time monitoring**: integrated Prometheus + Grafana.

#### 🛠 Improvements and Optimizations
- **Error handling**: improved API retries and rate limiting.
- **Distributed architecture**: added support for large-scale parallel evaluation.

### v1.1.0 (2025-12-23)
- Added CLI tools and a web interface.

---

*Last updated: 2026-02-02*

# Changelog

All notable changes to FORGEDAN will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-03-24

### Added
- **Vue 3 SPA Dashboard** — 7 pages (Dashboard, AttackTest, WebScan, Reports, Models, Datasets, Settings) with dark cyberpunk theme
- **Flask Blueprint API** — Modular REST API with 8 Blueprint modules (attacks, models, reports, datasets, webscan, monitoring, auth)
- **Web Security Testing** — 3 modes: URL crawling, vulnerability scanning (XSS/SQLi), LLM-driven interaction testing
- **Attack Method Registry** — Unified registry for all 6 attack methods with `get_info_static()` and `get_params_schema()` JSON Schema
- **`pyproject.toml`** — Modern Python packaging with optional dependency groups
- **CLI `--quick` mode** — Quick demo with 3 iterations, minimal config
- **`SafetyDataset` class** — Convenience dataset class for direct sample construction
- **`MALWARE` harm category** — Added to `HarmCategory` enum
- **`DatasetSample.to_dict()`** — Serialization method
- **`Dataset.name` property** — Unified name access across all dataset types

### Fixed
- **[CRITICAL] Pickle RCE** — Replaced pickle serialization with JSON for checkpoints
- **[CRITICAL] SECRET_KEY hardcoded** — Dynamic generation with warning for production
- **[HIGH] CORS wildcard** — Configurable from `CORS_ALLOWED_ORIGINS` env var
- **[HIGH] API key URL leak** — Removed query parameter support, header-only
- **[HIGH] Timing attack** — `hmac.compare_digest` for API key comparison
- **[HIGH] Path traversal** — Filename validation on report endpoints
- **[HIGH] API key logging** — `mask_api_key()` redaction in all logs
- **CircuitBreaker API mismatch** — `can_execute` → `allow_request`, `record_*` → `_record_*`
- **FitnessResult extraction** — `calculate().score` in engine (sync + async)
- **JudgeResult unpacking** — Replaced tuple destructuring with attribute access
- **33 test failures** — Fixed API contract mismatches across fitness, judge, datasets, engine, mutator, utils
- **Version inconsistency** — Unified to 1.2.0 across CLI, `__init__`, web app
- **Web UI crash** — `CollectorRegistry` parameter name fix
- **`quick_start.py` crash** — Dataset name attribute access

### Changed
- `.env.example` expanded with all 18 model providers + security config
- Test expectations aligned with actual API contracts (FitnessResult, JudgeResult, Tuple returns)
- Mutator strategy count updated (8 → 15)

## [1.1.0] - 2025-12-23

### Added
- Enhanced attack methods (AutoDAN, PAIR, GCG, Crescendo, TAP)
- Multi-modal attack support
- Defense training data generation
- Distributed computing support
- Prometheus monitoring integration
- Web UI (Flask + Jinja2)

## [1.0.0] - 2025-11-20

### Added
- Initial release
- FORGEDAN evolutionary algorithm engine
- Dual-judge mechanism
- 15 mutation strategies with MAB selection
- Basic CLI interface
- AdvBench dataset support

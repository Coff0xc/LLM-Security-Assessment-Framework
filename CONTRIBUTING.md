# Contributing to FORGEDAN

Thank you for your interest in contributing to FORGEDAN! This document provides guidelines and information for contributors.

## How to Contribute

### Reporting Bugs

- Use [GitHub Issues](https://github.com/Coff0xc/LLM-Security-Assessment-Framework/issues) to report bugs
- Include Python version, OS, and steps to reproduce
- Attach relevant error logs (redact any API keys)

### Suggesting Features

- Open a GitHub Issue with the `enhancement` label
- Describe the use case and expected behavior

### Pull Requests

1. Fork the repo and create your branch from `main`
2. Install dev dependencies: `pip install -e ".[dev]"`
3. Make your changes
4. Add tests for new functionality
5. Run tests: `pytest tests/ -v`
6. Run formatter: `black forgedan/`
7. Submit a PR with a clear description

## Code Style

- Python: Follow PEP 8, use `black` for formatting
- TypeScript/Vue: Follow ESLint configuration
- Commit messages: Use conventional commits (`feat:`, `fix:`, `docs:`, etc.)

## Project Structure

- `forgedan/` — Core Python package
- `forgedan/api/` — Flask Blueprint REST API
- `forgedan/attacks/` — Attack method implementations
- `forgedan/adapters/` — Model provider adapters
- `forgedan/webscan/` — Web security testing
- `frontend/` — Vue 3 SPA dashboard
- `tests/` — Pytest test suite

## Adding a New Attack Method

1. Create `forgedan/attacks/your_method.py` inheriting from `BaseAttack`
2. Implement `attack()`, `get_info_static()`, `get_params_schema()`
3. Register in `forgedan/attacks/__init__.py`
4. Add tests in `tests/`

## Adding a New Model Adapter

1. Create `forgedan/adapters/your_provider.py` inheriting from `ModelAdapter`
2. Implement `generate()`, `batch_generate()`, `health_check()`, `get_model_info()`
3. Register in `forgedan/adapters/factory.py`

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

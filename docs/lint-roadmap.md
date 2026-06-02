# Staged Lint Roadmap

Date: 2026-06-01

This project is optimized for reproducible LLM security assessment reports, not
for product-platform polish. The lint strategy therefore keeps CI focused on
defects that can invalidate report evidence, while tracking historical style
debt in stages that can be promoted to gates after cleanup.

## Current CI Gate

The blocking lint gate is intentionally scoped to defects and churn that affect
assessment evidence quality:

```bash
flake8 forgedan/ --select=E9,F63,F7,F82,E722,F401,F841 --show-source --statistics
black --check forgedan tests
```

It catches syntax errors, invalid control flow, undefined names, bare `except`
blocks, unused imports, and unused local variables. These failures can stop
suite execution, hide stale dependencies, or make generated report packs less
reliable, so they should remain blocking.

## Debt Snapshot

Verification command:

```bash
python -m flake8 forgedan/ --select=F401,F841,E722 --statistics --count
```

Snapshot result on 2026-06-01:

| Rule | Meaning | Count | Gate Status |
| --- | --- | ---: | --- |
| F401 | Imported but unused | 0 | Blocking CI gate |
| F841 | Local variable assigned but unused | 0 | Blocking CI gate |
| E722 | Bare `except` | 0 | Blocking CI gate |
| Total | Remaining staged lint debt for selected rules | 0 | Blocking CI gate |

## Promotion Plan

| Stage | Target | Acceptance Command | Promotion Rule |
| --- | --- | --- | --- |
| 1 | Remove unused imports in runtime modules first, then examples and package-local demos. | `python -m flake8 forgedan/ --select=F401 --count` returns `0`. | Completed on 2026-06-01; keep `F401` in the blocking CI gate. |
| 2 | Remove or rename intentionally unused local variables to `_`, preserving logging or error handling where the variable carries evidence. | `python -m flake8 forgedan/ --select=F841 --count` returns `0`. | Completed on 2026-06-01; keep `F841` in the blocking CI gate. |
| 3 | Replace bare `except` blocks with specific exceptions or `except Exception` plus safe fallback behavior. | `python -m flake8 forgedan/ --select=E722 --count` returns `0`. | Completed on 2026-06-01; keep `E722` in the blocking CI gate. |
| 4 | Normalize formatting drift once behavior gates are stable. | `black --check forgedan tests` and the full test gate pass. | Completed on 2026-06-01; keep Black in the blocking CI gate. |

Stage 4 audit on 2026-06-01: `python -m black --check --target-version py39 forgedan tests`
reported 91 files that would be reformatted. The formatter-only pass was then
applied with `target-version = ["py39"]` recorded in `pyproject.toml`, avoiding
the Python 3.14/target-version warning seen when Black inferred a newer target.

## Guardrails

- Keep the current syntax/undefined-name/bare-except/unused-code CI gate
  blocking throughout cleanup.
- Promote one rule group at a time so report-generation regressions are easy to
  localize.
- Avoid broad formatter patches in the same change as behavioral report logic.
- Treat cleanup in optional provider, web, distributed, or multimodal modules as
  higher risk than straightforward import removal in core suite/report code.
- Every promotion should include the suite smoke run and bundle verification so
  generated assessment artifacts remain handoff-ready.

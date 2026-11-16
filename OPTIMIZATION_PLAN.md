# FORGEDAN Report-Delivery Optimization Plan

> Version: 2026-06 report-delivery roadmap
> Scope: LLM security assessment reports, evidence packs, QA receipts, schemas, and archive verification
> Goal: keep optimizing around the report-delivery project instead of turning the repository into a commercial security platform.

---

## 1. Project Direction

FORGEDAN's current core goal is to produce auditable, reproducible, and handoff-ready LLM security assessment report packages.
The algorithms, WebScan, model adapters, and dashboard stay, but optimization priorities serve the quality of the final reports:

- Whether report evidence is complete, traceable, and reviewable.
- Whether the JSON/Markdown/HTML/CSV/ZIP artifacts are consistent.
- Whether the QA handoff receipt can stop incomplete reports from going out.
- Whether the sample report pack lets reviewers understand the final deliverables before running the CLI.
- Whether CI covers report generation, validation, archiving, and formatting gates.

English summary: FORGEDAN is optimized as a report-first LLM security
assessment framework. Performance and platform features are useful only when
they improve reproducible evidence, reviewer handoff, and archive integrity.

---

## 2. Current Evidence

| Area | Current State |
| --- | --- |
| Positioning | README states the project is report-delivery first, not a commercial security platform. |
| Sample pack | `docs/sample-report-pack/ready-for-handoff/` includes rendered reports, QA receipt, manifest, screenshots, and verified `handoff.zip`. |
| Reproducibility | `tests/test_sample_report_pack.py` proves the checked-in sample pack can be rebuilt byte-for-byte, excluding its explanatory README. |
| CI gates | CI runs tests, preflight, suite generation, report validation, bundle verification, strict QA handoff, archive verification, selected flake8, Black, and frontend build. |
| Schemas | Report artifacts are bound to JSON Schema contracts in `schemas/`. |
| Integrity | `validate-report`, `verify-bundle`, and `verify-archive` check schema, hash, sidecars, cross-artifact consistency, redaction, and QA receipt binding. |
| Landscape scan | `docs/llm-security-landscape.md` records competitor lessons and many already-fixed report gaps. |

---

## 3. Optimization Principles

1. **Report quality first**
   Every new capability should improve the report body, evidence matrix, risk register, QA receipt, schemas, archiving, or audit review.

2. **Deterministic where possible**
   Samples, fixtures, CI, and the handoff pack should be as reproducible as possible; use explicit metadata for time, run IDs, and environment information.

3. **Evidence over platform scope**
   Multi-tenancy, commercial RBAC, Vault, Ray clusters, and GPU work are not priorities unless they directly serve report-delivery evidence.

4. **Local verification before handoff**
   `preflight -> suite run -> validate-report -> verify-bundle -> qa-report --strict-handoff -> archive -> verify-archive`
   This is the default delivery path.

5. **Small, reviewable increments**
   Each round of optimization should name the files, tests, commands, and remaining risks.

---

## 4. Completed Capabilities

| Capability | Evidence |
| --- | --- |
| Report-first README | `README.md`, `README.zh-CN.md` |
| Ready-for-handoff sample | `docs/sample-report-pack/ready-for-handoff/` |
| Screenshots in README | `docs/screenshots/*.png` |
| Deterministic sample metadata | `examples/ready-for-handoff-suite.yml` |
| Reproducible sample test | `tests/test_sample_report_pack.py` |
| QA receipt gates | `forgedan/suite.py`, `schemas/suite-qa-receipt.schema.json` |
| Archive verification | `archive`, `verify-archive`, `tests/test_suite.py` |
| CI report gates | `.github/workflows/ci.yml` |

---

## 5. Priority Roadmap

### P0. Keep Report Deliverables Trustworthy

| Item | Why It Matters | Acceptance Evidence |
| --- | --- | --- |
| Expand sample-pack reproducibility coverage when new artifacts are added. | New artifacts must enter the sample pack's reproducibility contract instead of existing only in the generator. | `tests/test_sample_report_pack.py` compares all generated artifacts except explanatory README. |
| Keep `README.md`, `README.zh-CN.md`, sample pack README, and `docs/repository-about.md` consistent. | The GitHub front page, handoff documentation, and repository sidebar should not tell different stories. | `rg` search shows no old “commercial platform” or stale anchor language in docs. |
| Preserve strict QA handoff in CI. | For a report project, the most important thing is not to hand off unfinished work. | CI runs `qa-report --strict-handoff` for `ready-for-handoff-suite`. |
| Validate archive after every sample refresh. | The ZIP is the single-file artifact the recipient is most likely to receive. | `verify-archive docs/sample-report-pack/ready-for-handoff/handoff.zip` passes and README hash matches. |

### P1. Improve Report Scope and Evidence

| Item | Why It Matters | Suggested Work |
| --- | --- | --- |
| Add more realistic Agent/MCP manifest fixtures. | Agent/MCP capabilities already have a foundation, but the samples are still small and need to look more like a real delivery scope. | Add 2-3 sanitized MCP manifests with trust tiers, tool annotations, and policy outcomes. |
| Add richer source inventory examples. | Reviewers need to know where cases, MCP manifests, model artifacts, and pricing policies come from. | Extend examples to include imported cases, MCP manifest, model artifact, and usage pricing in one ready-for-report suite. |
| Add reviewer-decision examples. | Report delivery often needs accepted risks, required mitigations, and rejected exceptions. | Add an example suite that produces mixed reviewer decisions and QA readiness states. |
| Add comparison-report sample pack. | Historical comparison is a common report-delivery need. | Check in a small baseline/current comparison fixture with manifest and archive verification. |

### P2. Improve Report UX

| Item | Why It Matters | Suggested Work |
| --- | --- | --- |
| Improve Markdown report section ordering. | Reviewers usually read the executive summary, scope, risk, and evidence first, then the appendix. | Review generated `suite-report.md` for report-reader flow and update rendering tests. |
| Add concise “handoff checklist” section to sample README. | The sample pack README should let recipients quickly see what to open first and how to verify it. | Update `docs/sample-report-pack/ready-for-handoff/README.md` and contract tests. |
| Improve HTML report accessibility. | Report screenshots and browser review need more stable table/readability behavior. | Add focused HTML structure checks or visual smoke if UI changes are made. |

### P3. Optional Platform Enhancements

These are not current priorities unless they directly improve report delivery:

- GPU acceleration for live attack runs.
- Distributed execution for large assessment campaigns.
- Redis/Ray/Vault/multi-tenant platform features.
- Live provider pricing refresh.

Reason: they add operational complexity and can distract from the current
report-delivery objective. Keep them as optional future work, not the main plan.

---

## 6. Recommended Next Sprints

### Sprint A: Documentation and Handoff Consistency

- Keep `README.md`, `README.zh-CN.md`, `docs/repository-about.md`, and this plan aligned.
- Add a small doc test or search check for stale “commercial platform” positioning.
- Add a sample-pack handoff checklist section and test that key commands/hash remain present.

### Sprint B: Realistic Fixture Coverage

- Add a richer `examples/handoff-rich-suite.yml` or similar report fixture.
- Include imported cases, MCP manifest, usage pricing, model artifact, reviewer decisions, and risk owners.
- Generate a small checked-in sample only if it remains deterministic and reviewable.

### Sprint C: Comparison Report Handoff

- Create deterministic baseline/current fixture results.
- Produce comparison JSON/Markdown/HTML, comparison manifest, archive, and verify commands.
- Add tests that comparison archives can be verified after copying.

### Sprint D: Report Reader Polish

- Tighten report structure and human-readable section ordering.
- Improve sample screenshots only when generated outputs materially change.
- Add tests for required report sections and handoff wording.

---

## 7. Verification Commands

Use these commands after report-delivery changes:

```bash
python -m pytest tests/test_sample_report_pack.py -q -p no:cacheprovider
python -m pytest tests/test_report_schemas.py tests/test_suite.py -q -k "ready_for_handoff or qa_receipt or archive or preflight or report_schema" -p no:cacheprovider
python -m forgedan.cli suite verify-bundle docs/sample-report-pack/ready-for-handoff/suite-manifest.json
python -m forgedan.cli suite validate-report docs/sample-report-pack/ready-for-handoff/suite-qa-receipt.json
python -m forgedan.cli suite verify-archive docs/sample-report-pack/ready-for-handoff/handoff.zip
python -m black --check forgedan tests
git diff --check
```

Use the full test suite before release-level changes:

```bash
python -m pytest -q -W error::DeprecationWarning -p no:cacheprovider --basetemp .tmp-test
```

---

## 8. Non-Goals

The following are intentionally not part of the current mainline optimization:

- Turning the repository into a commercial SaaS security platform.
- Adding multi-tenant billing, customer admin, or production RBAC.
- Adding Vault/Redis/Ray/GPU dependencies as default requirements.
- Publishing live provider pricing or benchmark claims without auditable sources.
- Running real offensive tests without authorization and explicit scope.


---

## 9. Success Criteria

The optimization effort is healthy when:

- A reviewer can inspect the sample pack before running any command.
- A maintainer can rebuild deterministic sample artifacts and get identical hashes.
- A report recipient can verify the ZIP after copying it.
- CI fails when report schemas, QA handoff gates, archive integrity, or formatter/lint gates regress.
- README, Chinese README, repository About guidance, sample pack README, and this plan all describe the same report-first project.


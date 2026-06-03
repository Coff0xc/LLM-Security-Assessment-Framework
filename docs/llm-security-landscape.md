# LLM Security Assessment Landscape

Date: 2026-05-29

This note captures the first competitive scan used to prioritize FORGEDAN improvements. It focuses on open-source projects that overlap with LLM security evaluation, red teaming, prompt-injection defense, model/file scanning, and evaluation operations.

## High-Signal Projects

| Project | Focus | What FORGEDAN Should Learn |
| --- | --- | --- |
| [promptfoo](https://github.com/promptfoo/promptfoo) | Declarative LLM evals, red teaming, CI/CD, reports, provider breadth | Add a config-first eval format, repeatable suites, cached runs, CI-friendly exit codes, and HTML/JSON artifacts. |
| [NVIDIA garak](https://github.com/NVIDIA/garak) | LLM vulnerability scanner with probes, detectors, generators, reports | Split attacks into probe/detector/generator contracts and expose `--list-*` discovery commands. |
| [Microsoft PyRIT](https://github.com/microsoft/PyRIT) | Generative AI risk identification and orchestrated red teaming | Add scenario orchestration, dataset-driven conversations, memory of runs, and reusable target abstractions. |
| [Tencent AI-Infra-Guard](https://github.com/Tencent/AI-Infra-Guard) | Full-stack AI red-team platform: AI infra, MCP, agent, skills, jailbreak eval | Broaden beyond jailbreaks into AI component fingerprinting, MCP/agent/tool-risk scan modes, and Docker-first deployment. |
| [Protect AI LLM Guard](https://github.com/protectai/llm-guard) | Input/output scanners for prompt injection, PII, secrets, toxicity, relevance | Add defensive scanners around prompts and responses so FORGEDAN can both attack and gate unsafe outputs. |
| [Protect AI ModelScan](https://github.com/protectai/modelscan) | Static model serialization attack scanning | Add optional local model artifact scanning before loading untrusted model files. |
| [Inspect AI](https://github.com/UKGovernmentBEIS/inspect_ai) | General LLM eval framework with solvers, scorers, tools, multi-turn dialogs | Separate task definition, solver, scorer, and logging; make security evals composable with general eval tasks. |
| [OpenAI evals](https://github.com/openai/evals) / [simple-evals](https://github.com/openai/simple-evals) | Benchmark registry and lightweight eval harnesses | Provide a small, inspectable eval format and benchmark registry rather than only imperative CLI runs. |
| [DeepEval](https://github.com/confident-ai/deepeval) | LLM evaluation metrics, pytest-like workflows, observability hooks | Add first-class metrics beyond attack success rate: latency, cost, refusal quality, regression deltas, trace IDs. |
| [DeepTeam](https://github.com/confident-ai/deepteam) | LLM system red teaming | Use attack taxonomies and repeatable vulnerabilities as a first-class suite layer. |
| [Tencent AICGSecEval](https://github.com/Tencent/AICGSecEval) | AI-generated code security evaluation | Useful reference if FORGEDAN adds code-generation security tests. |
| [AART](https://github.com/caspiankeyes/AART-AI-Adversarial-Research-Toolkit) | Multi-dimensional adversarial research toolkit | Good reference for scoring dimensions and research-style reports. |
| [PurPaaS-LLM](https://github.com/dwain-barnes/PurPaaS-LLM) | Local LLM purple-team testing via Ollama | Useful local-first pattern for low-cost offline demos. |
| [AI-RedTeaming-with-PromptFoo](https://github.com/GenAIGator/AI-RedTeaming-with-PromptFoo) | Promptfoo-based red-team test examples | Good source of practical suite examples. |
| [llm-redteam-lab](https://github.com/thaaaru/llm-redteam-lab) | Lab environment combining Ollama, PyRIT, garak, vulnerable RAG | Good reference for demo labs and educational packaging. |
| [mcp-stress-test](https://github.com/mcp-tool-shop-org/mcp-stress-test) | MCP scanner stress tests | Useful if FORGEDAN grows MCP server / tool security coverage. |

## Product Gaps Found In FORGEDAN

1. **Import and install boundary**
   - Fixed in this pass: core package import no longer eagerly imports `webscan`, and WebScan dependencies now live under the `web` extra.

2. **CI gate quality**
   - Fixed in this pass: CI lint now enforces a realistic baseline for syntax errors and undefined names instead of failing on all historical style debt.
   - Fixed in this pass: added a staged lint roadmap with measured F401/F841/E722 debt, acceptance commands, and promotion rules for stricter gates.
   - Fixed in this pass: removed bare `except` blocks in multimodal helpers and promoted E722 into the blocking CI lint gate.
   - Fixed in this pass: removed F401/F841 lint debt across runtime, report, API, distributed, monitoring, webscan, and package-local demo modules, then promoted both rules into the blocking CI lint gate.
   - Fixed in this pass: applied a formatter-only Black pass, pinned Black to Python 3.9 syntax in `pyproject.toml`, and promoted `black --check forgedan tests` into CI.

3. **Benchmark and suite format**
   - Current project is strong in attack algorithms but needs reproducible suite definition to become CI-operational.
   - Fixed in this pass: added YAML suite files, reusable JSONL/YAML/JSON case files, summary JSON artifacts, and policy thresholds that can fail CI.
   - Fixed in this pass: `forgedan suite run --run-id-dir` can archive each run under `output/<run_id>/`, avoiding accidental report-pack overwrites during repeated assessment runs.
   - Fixed in this pass: suite configs can define reusable deterministic `contains` scorers via `scorer_definitions`, so report packs can carry custom reviewer metrics without code changes.
   - Fixed in this pass: suite configs can set `response_cache_file` and optional `random_seed` to replay model responses from a local JSON cache keyed by model and prompt SHA256, reducing repeated provider calls during deterministic report reruns without storing raw prompts.

4. **Scoring model**
   - Current scoring centers on fitness and jailbreak success.
   - Fixed in this pass: suite results now include deterministic prompt/response safety scans plus detector confidence, reusable scorers for target-prefix match, refusal, and response safety, plus adapter token/latency usage summaries when model responses expose usage metadata.
   - Fixed in this pass: suites can load a local JSON/YAML `usage_pricing_file` catalog keyed by model, preserving the pricing file in Source Inventory for report cost-audit evidence.
   - Remaining: add automated live-provider pricing refresh only if a stable, auditable source is available.

5. **Artifacts and reports**
   - Fixed in this pass: suite runs now produce executive summaries, normalized findings with stable taxonomy IDs/categories/priorities/confidence, policy-domain buckets, OWASP LLM Top 10 report mappings, CLI-exportable finding taxonomy, CLI-exportable report schema references, local report artifact schema validation, report-pack manifest verification, JSON Schema contracts for report artifacts, manifest schema references, QA handoff receipts, runtime environment metadata, normalized suite configuration snapshots, imported source inventories with SHA256/size/case counts, severity/kind/source finding summaries, remediation recommendations, risk levels, report sections for scope/methodology/evidence/usage/appendix/limitations, summary JSON, per-case JSONL, redacted publication JSON/JSONL/HTML/Markdown reports, release notes, public bundle indexes, CSV evidence matrices, case-level coverage/risk/usage matrices, reviewer coverage JSON/CSV summaries by case category/policy domain/OWASP LLM category, HTML/Markdown reports, Markdown report bundle indexes, artifact manifests with SHA256 checksums, JSON/Markdown/HTML historical comparison reports with bundle indexes, run/case trace IDs, timestamps, latency, token usage, local model artifact provenance, and CI-friendly exit codes.
   - Fixed in this pass: `validate-report` now checks `suite-comparison.json` regression counts and policy-domain delta arithmetic, then binds sibling comparison Markdown, HTML, and bundle sidecars back to the JSON regression result when those sidecars exist.
   - Fixed in this pass: comparison runs now write a machine-readable `*-manifest.json` sidecar with artifact hashes, schema references, baseline/current identity, and regression summary; `validate-report` rechecks the manifest hashes and binds the manifest summary back to the comparison JSON before archive handoff.
   - Fixed in this pass: `forgedan suite archive` can package a verified report pack into a single ZIP handoff artifact, and `forgedan suite verify-archive` rechecks the embedded manifest schema, archived JSON artifact schemas, each archived member's size/SHA256, and suite archive cross-artifact consistency after copying or sharing.
   - Fixed in this pass: `forgedan suite archive` and `verify-archive` now support both suite report manifests and historical comparison manifests, so baseline/current regression reports can use the same single-file handoff and post-copy verification workflow.
   - Fixed in this pass: suite ZIP archive verification now reuses the directory bundle cross-artifact consistency checks, catching synchronized-hash archive drift in run IDs, suite/model identity, report counts, redacted artifacts, case streams, CSV matrices, release notes, bundle indexes, narrative reports, and publication redaction before handoff.
   - Fixed in this pass: CI now archives and verifies both smoke and ready-for-handoff report packs, so the documented ZIP handoff path is exercised on every supported Python version.
   - Fixed in this pass: generated release notes and the full report bundle index now include `verify-bundle`, `qa-report`, `archive`, and `verify-archive` handoff commands, and bundle verification binds those commands back to expected report-pack guidance.
   - Fixed in this pass: suite archives now include same-directory `suite-qa-receipt.json` and `suite-qa-receipt.md` sidecars when present, and `verify-archive` validates the QA receipt schema plus Markdown sidecar consistency against the archived manifest/artifacts.
   - Fixed in this pass: added `docs/sample-report-pack/ready-for-handoff/`, a rendered mock report pack with narrative reports, bundle indexes, QA receipt, manifest, and a verified handoff ZIP for reviewers who want to inspect output before running the CLI.
   - Fixed in this pass: policy gates can now require case categories, policy domains, and OWASP LLM IDs so report packs fail when mandatory coverage is missing.
   - Fixed in this pass: normalized findings, evidence CSVs, risk registers, and narrative reports now include severity rationale text for reviewer sign-off.
   - Fixed in this pass: findings now carry stable evidence fingerprints, and reports summarize duplicate evidence groups so reviewers can spot repeated evidence across cases without comparing raw prompts manually.
   - Fixed in this pass: suite configs now support formal report metadata such as assessment ID, title, client, authors/reviewers, classification, and assessment window; public redacted reports mask client/author/reviewer names.
   - Fixed in this pass: suite configs now support report acceptance criteria/sign-off matrices; Markdown/HTML reports, bundle indexes, manifests, and QA receipts surface the criteria, and failed criteria block handoff readiness.
   - Fixed in this pass: QA receipt handoff items for residual risk owner sign-off, raw artifact handling, and limitations review can now be satisfied by matching `acceptance_criteria` entries, so signed-off report packs do not remain artificially review-blocked.
   - Fixed in this pass: suite configs now support reviewer decision logs for accepted risk, approvals, required mitigations, or rejected exceptions; Markdown/HTML reports and QA receipts surface whether policy exceptions have documented decisions.
   - Fixed in this pass: QA receipts now include a handoff readiness score summarizing passed, failed, and review-required checklist items plus blockers for report handoff.
   - Fixed in this pass: `forgedan suite qa-report --strict-handoff` now lets CI/final handoff fail when the QA receipt has `failed` or `review_required` handoff readiness while preserving the default receipt-generation behavior.
   - Fixed in this pass: CI now generates a `ready-for-handoff-suite` report pack and runs `qa-report --strict-handoff`, so the final handoff gate is exercised against a fully passing report deliverable, not only unit tests.
   - Fixed in this pass: full and public bundle indexes now include handoff summaries for policy violations, risk count, acceptance status, reviewer decisions, and MCP trust.
   - Fixed in this pass: report packs now include `suite-release-notes.md`, a concise reviewer-facing summary of run status, policy/risk/acceptance signals, source inventory, reviewer decisions, MCP trust, artifact pointers, and verification commands; QA receipts now include a required release-notes checklist item.
   - Fixed in this pass: QA receipts now include a required Source Inventory checklist item so imported source paths, hashes, byte counts, and generated case counts are reviewed during handoff.
   - Fixed in this pass: source inventory is now required by both `suite-config.schema.json` and the embedded `suite-result.schema.json` suite configuration snapshot, so missing provenance fails `validate-report`.
   - Fixed in this pass: `validate-report` now checks Source Inventory semantic consistency, including source counts, generated case counts, byte totals, and alignment between the report section and embedded suite configuration snapshot.
   - Fixed in this pass: `validate-report` now recomputes `usage_summary.estimated_cost_usd` from `suite_config.usage_pricing` and checks the pricing source note, catching hand-edited report cost summaries.
   - Fixed in this pass: suite configs can pre-fill risk-register owner/status/due-date defaults, and QA receipts now check owner/due-date assignment counts so remediation tracker exports are handoff-ready instead of blank follow-up templates.
   - Fixed in this pass: `suite-qa-receipt.schema.json` now enumerates known handoff checklist IDs, catching typoed QA receipt items during `validate-report`.
   - Fixed in this pass: `validate-report` now requires every known QA handoff checklist item to appear exactly once, catching deleted or duplicated handoff gates.
   - Fixed in this pass: `validate-report` now regenerates expected QA handoff checklist status/evidence/action from the local report pack, catching hand-edited gate approvals.
   - Fixed in this pass: `validate-report` now recalculates QA receipt handoff readiness from checklist items, catching tampered readiness status, counts, scores, or blockers.
   - Fixed in this pass: `validate-report` now checks risk-register semantic consistency, catching mismatched risk counts, risk rows tied to the wrong run ID, and duplicate risk IDs before report handoff.
   - Fixed in this pass: `validate-report` now checks manifest semantic consistency, catching mismatched artifact/schema counts and duplicate manifest artifact paths or schema names.
   - Fixed in this pass: `validate-report` now checks coverage semantic consistency, catching mismatched case counts, finding totals, and per-dimension coverage totals before reviewers rely on coverage gap summaries.
   - Fixed in this pass: `verify-bundle` now checks cross-artifact consistency between `suite-result.json`, `suite-risk-register.json`, and `suite-coverage.json`, so synchronized hash updates cannot hide mismatched run IDs, suite/model identity, or report counts.
   - Fixed in this pass: `verify-bundle` now checks `suite-config.json` against the embedded `suite-result.json` suite configuration snapshot, catching synchronized-hash config drift before audit replay.
   - Fixed in this pass: `verify-bundle` now checks `suite-result-redacted.json` against the raw `suite-result.json` run identity, case counts, risk metrics, and policy pass status, catching synchronized-hash public summary drift before external handoff.
   - Fixed in this pass: `verify-bundle` now checks `suite-cases.jsonl` and `suite-cases-redacted.jsonl` against `suite-result.json` case IDs, trace IDs, and execution counters, catching synchronized-hash per-case stream drift before audit replay or publication.
   - Fixed in this pass: `verify-bundle` now scans redacted/public artifacts for secret-, email-, or connection-string-bearing `best_prompt`, `best_response`, and finding evidence text from `suite-result.json`, catching synchronized-hash publication packs that reintroduce high-risk raw evidence.
   - Fixed in this pass: `verify-bundle` now checks `suite-case-matrix.csv` against `suite-result.json` case IDs, trace IDs, success values, and execution counters, catching synchronized-hash case-matrix drift before external reviewer handoff.
   - Fixed in this pass: `verify-bundle` now checks `suite-evidence.csv` against `suite-result.json` finding IDs, trace IDs, taxonomy, policy-domain, OWASP, and evidence-fingerprint fields, catching synchronized-hash evidence matrix drift before report sign-off.
   - Fixed in this pass: `verify-bundle` now checks `suite-risk-register.csv` against `suite-risk-register.json` risk IDs, run/trace IDs, case, taxonomy, policy-domain, OWASP, and evidence hash/fingerprint fields, catching synchronized-hash remediation tracker drift before owner handoff.
   - Fixed in this pass: `verify-bundle` now checks `suite-coverage.csv` against `suite-coverage.json` coverage rows, catching synchronized-hash coverage matrix drift before reviewer handoff.
   - Fixed in this pass: `verify-bundle` now checks `suite-release-notes.md` summary lines against `suite-result.json`, catching synchronized-hash reviewer-note drift in policy, risk, acceptance, source inventory, reviewer decision, and MCP trust summaries.
   - Fixed in this pass: `verify-bundle` now checks full and public bundle index summary lines against `suite-result.json`, catching synchronized-hash bundle-index drift before archive or external handoff.
   - Fixed in this pass: `verify-bundle` now checks full and redacted Markdown/HTML report body summary and acceptance lines against `suite-result.json`, catching synchronized-hash narrative-report drift before reviewer handoff.
   - Fixed in this pass: `verify-bundle` now also checks required Markdown/HTML report sections, catching synchronized-hash report bodies that delete limitations, appendix, evidence, usage, or other handoff sections while preserving summary numbers.
   - Fixed in this pass: QA receipts now surface cross-artifact consistency as a required handoff checklist item, so mismatched run IDs or report counts become visible handoff blockers.
   - Fixed in this pass: QA receipt JSON now includes a structured `cross_artifact_consistency` object for CI/archive scripts that need machine-readable consistency errors.
   - Fixed in this pass: QA receipt Markdown now renders the same cross-artifact consistency summary and error details for human report handoff review.
   - Fixed in this pass: QA receipt redacted-publication checklist status now fails when cross-artifact verification finds redaction leaks, so publication-pack leakage is visible as a direct handoff blocker instead of only a generic consistency error.
   - Fixed in this pass: `suite-qa-receipt.schema.json` now enumerates known cross-artifact consistency checked artifact names, catching typoed or undeclared consistency targets during `validate-report`.
   - Fixed in this pass: `validate-report` now checks that QA receipt `cross_artifact_consistency` agrees with the handoff checklist status and error count, catching receipt JSON tampering.
   - Fixed in this pass: `validate-report` now checks QA receipt `cross_artifact_consistency` details against current local manifest verification output, catching same-count fake consistency errors.
   - Fixed in this pass: `validate-report` now recomputes QA receipt artifact, schema-validation, and error counts plus top-level `valid`/`status` summaries, catching hand-edited receipt summaries.
   - Fixed in this pass: `validate-report` now checks QA receipt top-level `valid`, `error_count`, and `errors` against current local manifest verification output, catching self-consistent but false verification summaries.
   - Fixed in this pass: `validate-report` now recomputes each QA receipt schema-validation row's error count and validity from its errors list, catching hand-edited schema validation details.
   - Fixed in this pass: `validate-report` now checks QA receipt schema-validation rows against current local manifest verification output, catching hand-edited schema identity, schema path, schema ID, target artifact, or result fields.
   - Fixed in this pass: `validate-report` now recomputes QA receipt acceptance summaries from artifact/schema validation details and report acceptance status, catching hand-edited handoff acceptance summaries.
   - Fixed in this pass: `validate-report` now checks QA receipt report acceptance status/count against local `suite-result.json`, catching hand-edited sign-off summaries that disagree with the report.
   - Fixed in this pass: QA receipts now record manifest size/SHA256 binding, and `validate-report` recomputes that binding when the manifest file is available locally.
   - Fixed in this pass: `validate-report` now checks QA receipt run ID, suite, model, and run-environment identity against the local manifest, catching receipts attached to the wrong report pack.
   - Fixed in this pass: `validate-report` now checks QA receipt artifact sensitivity/audience labels against the local manifest, catching hand-edited publication classifications.
   - Fixed in this pass: `validate-report` now rechecks QA receipt `checked_artifacts` rows against locally available artifact files, catching stale receipts after report files are modified or deleted.
   - Fixed in this pass: `validate-report` now checks QA receipt `checked_artifacts` rows against current local manifest verification output, catching same-count fake artifact error details.
   - Fixed in this pass: `validate-report` now checks QA receipt `checked_artifacts` paths against the manifest artifact list, catching duplicate, missing, or undeclared artifact rows before report handoff.
   - Fixed in this pass: `validate-report` now binds sibling `suite-qa-receipt.md` files back to `suite-qa-receipt.json`, catching hand-edited reviewer-facing receipt summaries, readiness lines, checklist rows, artifact rows, schema rows, and error details before report handoff.
   - Fixed in this pass: added `examples/ready-for-handoff-suite.yml` as a minimal report-pack sample whose QA receipt has no handoff blockers.
   - Fixed in this pass: added `forgedan suite preflight`, a no-model report readiness audit that checks report metadata, handoff acceptance criteria, risk-register defaults, policy gates, case categorization, scorer resolution, deterministic replay controls, source provenance, MCP trust policy, and model-serialization scope before expensive suite execution.
   - Fixed in this pass: preflight audits can now be written as `suite-preflight.json` / `suite-preflight.md`, and `suite-preflight.json` is covered by `schemas/suite-preflight.schema.json` plus `validate-report` inference for CI/archive use.
   - Fixed in this pass: `suite run` now includes `suite-preflight.json` and `suite-preflight.md` inside the generated report pack and manifest, so archive reviewers get the run-before-use readiness evidence with the rest of the bundle.
   - Fixed in this pass: `validate-report` now recomputes `suite-preflight.json` summary/status/blocker/score semantics and, when `suite-config.json` is present beside it, rebuilds the expected preflight audit from the config snapshot to catch hand-edited readiness evidence.
   - Fixed in this pass: `verify-bundle` now binds `suite-preflight.md` back to `suite-preflight.json` status, score, summary counts, blockers, and check-table evidence/action rows, and QA receipts include an explicit preflight-readiness handoff checklist item.
   - Fixed in this pass: coverage reports now include taxonomy-category coverage for Prompt Security, Data Exposure, Agent Tooling, and other report-facing finding categories.
   - Fixed in this pass: suite configs can include external `usage_pricing` values or a local `usage_pricing_file` catalog so reports compute reproducible `estimated_cost_usd` without fetching live provider prices.
   - Remaining: add automated live-provider pricing refresh only if a stable, auditable source is available.

6. **Defensive testing**
   - LLM Guard and ModelScan show the need for both offensive and defensive coverage.
   - Fixed in this pass: lightweight input/output scanners detect prompt-injection markers, indirect prompt injection in untrusted retrieved content, system prompt leakage, jailbreak roleplay framing, secrets, connection-string exposure, email-like PII, Agent/MCP tool data-exfiltration instructions, configured tool permission policy violations, and malicious tool metadata injection including forced-call metadata.
   - Fixed in this pass: suite configs can import local UTF-8 model artifact files as `model-artifact-*` report cases, preserving `artifact_file`, `artifact_sha256`, and `artifact_bytes` metadata while reusing the same deterministic scanners and report scope.
   - Fixed in this pass: report packs now include a Source Inventory section for imported cases files, MCP manifests, and model artifacts so reviewers can verify source path, SHA256, byte size, and generated case count from the full report, release notes, or full bundle index.
   - Fixed in this pass: suite configs can scan `model_serialization_files` without loading untrusted model objects, flagging pickle/PyTorch/checkpoint/ONNX/opaque binary/GGUF/safetensors artifacts with SHA256, size, risk, and reviewer recommendations in the report pack.
   - Remaining: replace the lightweight serialization heuristics with deeper ModelScan-style analysis only if the report scope requires true model-file malware inspection.

7. **Agent/MCP security**
   - AI-Infra-Guard and current ecosystem trends show agent/tool/MCP evaluation is now a core category.
   - Fixed in this pass: added deterministic `tool_data_exfiltration`, `tool_metadata_injection`, `tool_policy_violation`, and `indirect_prompt_injection` findings mapped to OWASP LLM01/LLM03/LLM06 plus a runnable `examples/agent-tool-suite.yml` report-pack demo.
   - Fixed in this pass: suite configs can import JSON/YAML MCP manifests, normalize each tool description into `mcp-tool-*` report cases, and keep structured provenance metadata in report scope/config snapshots, cases JSONL, and case matrix CSV.
   - Fixed in this pass: MCP manifest import now recursively normalizes nested annotations and server trust metadata into case metadata, annotation key/hash fields, and scanner-visible tool text.
   - Fixed in this pass: MCP server trust tiers can now be allowlisted as report policy gates, so third-party or missing trust metadata fails the QA-visible policy gate.
   - Fixed in this pass: imported MCP cases now carry heuristic server trust scores, and Markdown/HTML reports include an MCP Trust Summary with tier counts, highest score, affected cases, server names, and score-model rationales.
   - Fixed in this pass: suites can load a local JSON/YAML `mcp_trust_policy_file` to calibrate trust tier scores and rationales, preserving the policy file in Source Inventory for report-audit evidence.
   - Next step: calibrate default MCP trust weights against a larger corpus of real server manifests when such a corpus is available.

## Recommended Optimization Order

1. Keep the core package importable and tests green under minimal install.
2. Make CI executable: tests, warning-clean config, and baseline lint.
3. Add suite-driven evaluation so runs are reproducible and CI-friendly.
4. Add result schema and deterministic artifacts.
5. Add defensive scanners and richer scoring.
6. Add Docker/devcontainer and front-end build verification.
7. Expand MCP/agent security coverage beyond data-egress prompts into tool metadata and permission policies.

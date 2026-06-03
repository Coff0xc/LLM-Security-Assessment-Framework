# FORGEDAN Report-Delivery Optimization Plan

> Version: 2026-06 report-delivery roadmap
> Scope: LLM security assessment reports, evidence packs, QA receipts, schemas, and archive verification
> 中文目标：围绕“报告交付项目”继续优化，而不是把仓库推进成商业化安全平台。

---

## 1. Project Direction / 项目方向

FORGEDAN 当前的核心目标是生成可审计、可复现、可交接的 LLM 安全评估报告包。
算法、WebScan、模型适配器和 dashboard 仍然保留，但优化优先级服务于最终报告质量：

- 报告证据是否完整、可追溯、可复核。
- JSON/Markdown/HTML/CSV/ZIP 制品是否一致。
- QA 交接回执是否能阻止不完整报告流出。
- 样例报告包是否能让评审人在运行 CLI 前理解最终交付物。
- CI 是否覆盖报告生成、校验、归档和格式门禁。

English summary: FORGEDAN is optimized as a report-first LLM security
assessment framework. Performance and platform features are useful only when
they improve reproducible evidence, reviewer handoff, and archive integrity.

---

## 2. Current Evidence / 当前事实

| Area | Current State | 中文说明 |
| --- | --- | --- |
| Positioning | README states the project is report-delivery first, not a commercial security platform. | README 已明确“报告交付项目，不是商业化安全平台”。 |
| Sample pack | `docs/sample-report-pack/ready-for-handoff/` includes rendered reports, QA receipt, manifest, screenshots, and verified `handoff.zip`. | 已提交可渲染样例报告包，包含报告、QA 回执、manifest、截图和可校验 ZIP。 |
| Reproducibility | `tests/test_sample_report_pack.py` proves the checked-in sample pack can be rebuilt byte-for-byte, excluding its explanatory README. | 样例包已有 byte-for-byte 重建测试，证明 fixture 报告包可复现。 |
| CI gates | CI runs tests, preflight, suite generation, report validation, bundle verification, strict QA handoff, archive verification, selected flake8, Black, and frontend build. | CI 已覆盖测试、预检、报告生成、报告校验、目录包验证、严格 QA 交接、归档验证、lint、Black 和前端构建。 |
| Schemas | Report artifacts are bound to JSON Schema contracts in `schemas/`. | 报告制品已有 Schema 合约。 |
| Integrity | `validate-report`, `verify-bundle`, and `verify-archive` check schema, hash, sidecars, cross-artifact consistency, redaction, and QA receipt binding. | 已通过多层验证保护 hash、schema、sidecar、跨制品一致性、脱敏和 QA 回执绑定。 |
| Landscape scan | `docs/llm-security-landscape.md` records competitor lessons and many already-fixed report gaps. | 同类项目扫描已记录能力差距和已修复项目。 |

---

## 3. Optimization Principles / 优化原则

1. **Report quality first / 报告质量优先**
   每个新增能力都要能改善报告正文、证据矩阵、风险登记、QA 回执、Schema、归档或审计复核。

2. **Deterministic where possible / 尽量确定性**
   样例、fixture、CI 和 handoff pack 应尽量可复现；涉及时间、run ID、环境信息时使用显式元数据。

3. **Evidence over platform scope / 证据优先于平台范围**
   不优先做多租户、商业 RBAC、Vault、Ray 集群或 GPU 路线，除非它们直接服务报告交付证据。

4. **Local verification before handoff / 交付前本地验证**
   `preflight -> suite run -> validate-report -> verify-bundle -> qa-report --strict-handoff -> archive -> verify-archive`
   是默认交付路径。

5. **Small, reviewable increments / 小步可 review**
   每一轮优化都应有明确文件、测试、命令和剩余风险。

---

## 4. Completed Capabilities / 已完成能力

| Capability | Evidence | 中文说明 |
| --- | --- | --- |
| Report-first README | `README.md`, `README.zh-CN.md` | 主 README 已改成全量中文 + English 双语对照，中文独立版同步说明。 |
| Ready-for-handoff sample | `docs/sample-report-pack/ready-for-handoff/` | 可直接查看的 mock 样例报告包。 |
| Screenshots in README | `docs/screenshots/*.png` | README 已包含报告总览、QA 回执、归档校验截图。 |
| Deterministic sample metadata | `examples/ready-for-handoff-suite.yml` | fixture suite 固定 run ID、时间、case ID、环境信息和 duration。 |
| Reproducible sample test | `tests/test_sample_report_pack.py` | 测试证明样例报告包可按相同交付路径重建。 |
| QA receipt gates | `forgedan/suite.py`, `schemas/suite-qa-receipt.schema.json` | QA 回执记录 handoff checklist、readiness、acceptance、schema、hash 和跨制品一致性。 |
| Archive verification | `archive`, `verify-archive`, `tests/test_suite.py` | ZIP 交付包可在复制或分享后复核。 |
| CI report gates | `.github/workflows/ci.yml` | CI 覆盖 smoke suite 和 ready-for-handoff suite 的报告门禁。 |

---

## 5. Priority Roadmap / 优先路线图

### P0. Keep Report Deliverables Trustworthy / 保持报告交付可信

| Item | Why It Matters | Acceptance Evidence |
| --- | --- | --- |
| Expand sample-pack reproducibility coverage when new artifacts are added. | 新制品必须进入样例包可复现契约，避免只在生成器里存在。 | `tests/test_sample_report_pack.py` compares all generated artifacts except explanatory README. |
| Keep `README.md`, `README.zh-CN.md`, sample pack README, and `docs/repository-about.md` consistent. | GitHub 首屏、中文交付说明和仓库侧栏不应讲不同故事。 | `rg` search shows no old “commercial platform” or stale anchor language in docs. |
| Preserve strict QA handoff in CI. | 报告项目最重要的是不把半成品交出去。 | CI runs `qa-report --strict-handoff` for `ready-for-handoff-suite`. |
| Validate archive after every sample refresh. | ZIP 是交付接收方最可能拿到的单文件产物。 | `verify-archive docs/sample-report-pack/ready-for-handoff/handoff.zip` passes and README hash matches. |

### P1. Improve Report Scope and Evidence / 增强报告范围与证据

| Item | Why It Matters | Suggested Work |
| --- | --- | --- |
| Add more realistic Agent/MCP manifest fixtures. | 当前 Agent/MCP 能力已有基础，但样例仍偏小，需要更像真实交付范围。 | Add 2-3 sanitized MCP manifests with trust tiers, tool annotations, and policy outcomes. |
| Add richer source inventory examples. | 评审人需要知道 case、MCP、model artifact、pricing policy 来自哪里。 | Extend examples to include imported cases, MCP manifest, model artifact, and usage pricing in one ready-for-report suite. |
| Add reviewer-decision examples. | 报告交付经常需要 accepted risk、required mitigation、rejected exception。 | Add an example suite that produces mixed reviewer decisions and QA readiness states. |
| Add comparison-report sample pack. | 历史对比是报告交付常见需求。 | Check in a small baseline/current comparison fixture with manifest and archive verification. |

### P2. Improve Report UX / 优化报告阅读体验

| Item | Why It Matters | Suggested Work |
| --- | --- | --- |
| Improve Markdown report section ordering. | 评审人通常先看 executive summary、scope、risk、evidence, then appendix. | Review generated `suite-report.md` for report-reader flow and update rendering tests. |
| Add concise “handoff checklist” section to sample README. | 样例包 README 应让接收方快速知道先打开什么、如何验收。 | Update `docs/sample-report-pack/ready-for-handoff/README.md` and contract tests. |
| Improve HTML report accessibility. | 报告截图和 browser review 需要更稳的 table/readability behavior. | Add focused HTML structure checks or visual smoke if UI changes are made. |

### P3. Optional Platform Enhancements / 可选平台增强

These are not current priorities unless they directly improve report delivery:

- GPU acceleration for live attack runs.
- Distributed execution for large assessment campaigns.
- Redis/Ray/Vault/multi-tenant platform features.
- Live provider pricing refresh.

Reason: they add operational complexity and can distract from the current
report-delivery objective. Keep them as optional future work, not the main plan.

---

## 6. Recommended Next Sprints / 建议后续迭代

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

## 7. Verification Commands / 验证命令

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

## 8. Non-Goals / 非目标

The following are intentionally not part of the current mainline optimization:

- Turning the repository into a commercial SaaS security platform.
- Adding multi-tenant billing, customer admin, or production RBAC.
- Adding Vault/Redis/Ray/GPU dependencies as default requirements.
- Publishing live provider pricing or benchmark claims without auditable sources.
- Running real offensive tests without authorization and explicit scope.

中文：当前主线不是商业平台化，而是让报告交付、证据链、QA 门禁和归档复核更可靠。

---

## 9. Success Criteria / 成功标准

The optimization effort is healthy when:

- A reviewer can inspect the sample pack before running any command.
- A maintainer can rebuild deterministic sample artifacts and get identical hashes.
- A report recipient can verify the ZIP after copying it.
- CI fails when report schemas, QA handoff gates, archive integrity, or formatter/lint gates regress.
- README, Chinese README, repository About guidance, sample pack README, and this plan all describe the same report-first project.

中文成功标准：评审人能看懂、维护者能复现、接收方能复核、CI 能拦截、文档口径一致。

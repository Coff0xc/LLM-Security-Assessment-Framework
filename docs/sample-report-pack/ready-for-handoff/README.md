# Ready-for-Handoff Sample Report Pack

This directory is a checked-in sample generated from
`examples/ready-for-handoff-suite.yml` with the local `mock:test-model` adapter.
It lets reviewers inspect the report deliverables before running the CLI.

中文：本目录是由 `examples/ready-for-handoff-suite.yml` 和本地
`mock:test-model` 适配器生成的可渲染样例报告包，方便评审人在运行 CLI 前直接查看交付物。

## Start Here / 推荐阅读

| Artifact | Purpose | 中文说明 |
| --- | --- | --- |
| [suite-report.md](suite-report.md) | Editable narrative report. | 可编辑叙事报告正文 |
| [suite-report.html](suite-report.html) | Browser-readable full report. | 浏览器可读完整报告 |
| [suite-report-bundle.md](suite-report-bundle.md) | Full artifact index, checksums, schemas, and verification commands. | 完整制品索引、hash、schema 和校验命令 |
| [suite-release-notes.md](suite-release-notes.md) | Short reviewer handoff notes. | 交接摘要和制品指针 |
| [suite-qa-receipt.md](suite-qa-receipt.md) | Human-readable QA handoff receipt. | 人工可读 QA 交接回执 |
| [suite-public-bundle.md](suite-public-bundle.md) | Lower-sensitivity public bundle index. | 低敏外部交付索引 |
| [handoff.zip](handoff.zip) | Single-file handoff archive with manifest artifacts plus QA receipt sidecars. | 单文件交付包，包含 manifest 制品和 QA 回执 sidecar |

## Handoff Checklist / 交接清单

Use this checklist before sharing or accepting the sample report pack.

中文：分享或接收该样例报告包前，建议按下面清单完成快速验收。

| Step | Reviewer action | 中文说明 |
| --- | --- | --- |
| 1 | Open `suite-release-notes.md` first to confirm the run summary, acceptance status, artifact pointers, and handoff commands. | 先打开 `suite-release-notes.md`，确认运行摘要、验收状态、制品指针和交接命令。 |
| 2 | Read `suite-report.md` or `suite-report.html` for the narrative report, then spot-check `suite-evidence.csv`, `suite-case-matrix.csv`, `suite-risk-register.csv`, and `suite-coverage.csv`. | 阅读 `suite-report.md` 或 `suite-report.html`，再抽查 evidence、case matrix、risk register 和 coverage CSV。 |
| 3 | Review `suite-qa-receipt.md` and confirm handoff readiness is passed, blockers are empty, acceptance criteria passed, and schema/hash checks are recorded. | 查看 `suite-qa-receipt.md`，确认交接状态 passed、blocker 为空、验收条件通过，并记录了 schema/hash 校验。 |
| 4 | Run `verify-bundle`, `validate-report`, and `verify-archive` with the commands below before treating the pack as accepted. | 使用下方命令运行目录包校验、QA 回执校验和 ZIP 归档校验，然后再视为验收通过。 |
| 5 | Compare the documented `handoff.zip` SHA256 with the local file hash after copying or sharing the archive. | 复制或分享归档后，对比 README 记录的 `handoff.zip` SHA256 和本地文件 hash。 |
| 6 | Use `suite-public-bundle.md` and redacted artifacts for lower-sensitivity sharing; do not treat raw prompt, response, trace, or evidence artifacts as public. | 低敏分享使用 `suite-public-bundle.md` 和脱敏制品；不要把原始 prompt、response、trace 或 evidence 当作公开材料。 |

## Verification / 校验

```bash
forgedan suite verify-bundle docs/sample-report-pack/ready-for-handoff/suite-manifest.json
forgedan suite validate-report docs/sample-report-pack/ready-for-handoff/suite-qa-receipt.json
forgedan suite verify-archive docs/sample-report-pack/ready-for-handoff/handoff.zip
```

Expected results:

- `verify-bundle`: passed, 20 artifacts checked, 7 schema validations.
- `validate-report suite-qa-receipt.json`: passed.
- `verify-archive`: passed, 20 manifest artifacts checked, 2 supplemental QA receipt sidecars, 8 schema validations.

`handoff.zip` SHA256:

```text
3dcb3c453b403c058255cb76b481bf5fe15d3a73135d8f9d51202ef93ce00eb4
```

## Sensitivity / 敏感度

The sample uses mock data only. It is intended as a repository fixture for
report format review, archive verification, CI documentation, and handoff
workflow inspection.

中文：该样例只包含 mock 数据，用于查看报告格式、归档校验、CI 文档和交接流程。

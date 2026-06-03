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
80eac87c34ccb4543a18a0fd93e6549805be1f4aa6d5deebb5c286b921e2b290
```

## Sensitivity / 敏感度

The sample uses mock data only. It is intended as a repository fixture for
report format review, archive verification, CI documentation, and handoff
workflow inspection.

中文：该样例只包含 mock 数据，用于查看报告格式、归档校验、CI 文档和交接流程。

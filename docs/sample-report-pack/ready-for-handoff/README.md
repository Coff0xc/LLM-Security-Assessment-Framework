# Ready-for-Handoff Sample Report Pack

This directory is a checked-in sample generated from
`examples/ready-for-handoff-suite.yml` with the local `mock:test-model` adapter.
It lets reviewers inspect the report deliverables before running the CLI.


## Start Here

| Artifact | Purpose |
| --- | --- |
| [suite-report.md](suite-report.md) | Editable narrative report. |
| [suite-report.html](suite-report.html) | Browser-readable full report. |
| [suite-report-bundle.md](suite-report-bundle.md) | Full artifact index, checksums, schemas, and verification commands. |
| [suite-release-notes.md](suite-release-notes.md) | Short reviewer handoff notes. |
| [suite-qa-receipt.md](suite-qa-receipt.md) | Human-readable QA handoff receipt. |
| [suite-public-bundle.md](suite-public-bundle.md) | Lower-sensitivity public bundle index. |
| [handoff.zip](handoff.zip) | Single-file handoff archive with manifest artifacts plus QA receipt sidecars. |

## Handoff Checklist

Use this checklist before sharing or accepting the sample report pack.


| Step | Reviewer action |
| --- | --- |
| 1 | Open `suite-release-notes.md` first to confirm the run summary, acceptance status, artifact pointers, and handoff commands. |
| 2 | Read `suite-report.md` or `suite-report.html` for the narrative report, then spot-check `suite-evidence.csv`, `suite-case-matrix.csv`, `suite-risk-register.csv`, and `suite-coverage.csv`. |
| 3 | Review `suite-qa-receipt.md` and confirm handoff readiness is passed, blockers are empty, acceptance criteria passed, and schema/hash checks are recorded. |
| 4 | Run `verify-bundle`, `validate-report`, and `verify-archive` with the commands below before treating the pack as accepted. |
| 5 | Compare the documented `handoff.zip` SHA256 with the local file hash after copying or sharing the archive. |
| 6 | Use `suite-public-bundle.md` and redacted artifacts for lower-sensitivity sharing; do not treat raw prompt, response, trace, or evidence artifacts as public. |

## Verification

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

## Sensitivity

The sample uses mock data only. It is intended as a repository fixture for
report format review, archive verification, CI documentation, and handoff
workflow inspection.


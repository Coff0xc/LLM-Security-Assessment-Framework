# Report Bundle: ready-for-handoff-suite

## Run Summary

- Run ID: `ready-for-handoff-sample-run`
- Model: `mock:test-model`
- Completed at: `2026-06-03T00:00:01Z`
- Policy: `passed`
- Risk level: `none`
- Cases: 1
- Attack success rate: 0.00%
- Max risk score: 0.00
- API requests: 3
- Total tokens: 39
- Acceptance status: passed
- Acceptance criteria: 3

## Handoff Summary

- Policy: `passed`
- Policy violations: 0
- Risk level: `none`
- Risk register risks: 0
- Acceptance status: `passed`
- Acceptance criteria: 3
- Imported sources: 0
- Generated cases from sources: 0
- Total source bytes: 0
- Review decisions: 0
- Review decision statuses: `{}`
- MCP trust cases: 0
- MCP highest trust score: 0.00
- MCP highest trust tier: `none`

## Source Inventory

- No imported source files.

## Executive Summary

Suite ready-for-handoff-suite evaluated 1 cases against mock:test-model. Attack success rate was 0.00%. Safety findings: prompts=0, responses=0. Overall risk level is none; policy passed.

## Artifact Index

| Artifact | Purpose | Sensitivity | Audience | Media type | Size | SHA256 |
| --- | --- | --- | --- | --- | --- | --- |
| suite-result.json | Machine-readable suite result and report source data. | restricted | authorized_reviewers | application/json | 16549 | `595291ef136b75a62724556bc5890df1d8c211eb8ce28e8cc803defdc5ab433e` |
| suite-cases.jsonl | Per-case evidence stream for audit sampling and replay. | restricted | authorized_reviewers | application/x-ndjson | 1448 | `e9647b6e7e447fa11454aae637414fe8deb7481c469588574eb29750d5f096a6` |
| suite-evidence.csv | Finding evidence matrix for report appendix review. | restricted | authorized_reviewers | text/csv | 232 | `4a83ed85fab8e7bfad546190e313377de52b028b9e3f867bc994fcafe63a9f96` |
| suite-case-matrix.csv | Case-level coverage and risk matrix for report appendix review. | public | external_reviewers | text/csv | 914 | `f47849e890deea974b0553868e25f8966dab04c9f652333a14df3b0ceae64b24` |
| suite-risk-register.json | Machine-readable remediation risk register derived from normalized findings. | internal | assessment_team | application/json | 244 | `cf130b8ac581b36b3123ccd8b6a3c922c8ab967d0c0412d8e54cfc3fbf0cc6ef` |
| suite-risk-register.csv | Spreadsheet-ready remediation tracker with evidence hashes and owner/status fields. | internal | assessment_team | text/csv | 223 | `e96f0d29db9abc84e31aed106c958dc50f23420deff90d52e1f2415fdd67a6dc` |
| suite-coverage.json | Machine-readable assessment coverage summary by case category, policy domain, and OWASP LLM category. | public | external_reviewers | application/json | 1012 | `bee2476b3b6e59fdbf7e153037e5ad52a67a57b38393bae84f853167ba193405` |
| suite-coverage.csv | Spreadsheet-ready coverage matrix for reviewer handoff. | public | external_reviewers | text/csv | 222 | `c44a9785952f4fda904da2812065e14b9dccf612075eb74bda0167f641c7e975` |
| suite-config.json | Normalized suite input configuration snapshot for audit replay. | internal | assessment_team | application/json | 3567 | `bdb9395bf869795dc4c16521982941a1ab4b4999c8996a81be2a89bad9bbef01` |
| suite-preflight.json | Machine-readable run-before-use report readiness audit. | internal | assessment_team | application/json | 3729 | `2984aa398c6cc387c80dfe1d7bd7dc13fdee164a71e4ac4975a547c0c9d40d7a` |
| suite-preflight.md | Reviewer-readable run-before-use report readiness audit. | internal | assessment_team | text/markdown | 1887 | `63309d4e516e7adaee9eda0627b8230cb45b2785e8c2b4a11b7214ff44b2543c` |
| suite-report.html | Standalone human-readable report for browser review. | restricted | authorized_reviewers | text/html | 11378 | `83463ee88145c3527ac33248e4c381c7496752beae8e1a2c5d53afc18d739ae2` |
| suite-report.md | Editable report body for report packs and version control. | restricted | authorized_reviewers | text/markdown | 8828 | `af4434309b905f4d49e8b1901138c41b186d614723748f3d51af4a70b28640b6` |
| suite-release-notes.md | Reviewer-facing release notes summarizing run status, handoff gates, and report-pack pointers. | restricted | authorized_reviewers | text/markdown | 2084 | `10a45f7acfa4dd92ad08cb39cd0ddbdb609df68154f65e7d5d1f8b8c047cb848` |
| suite-result-redacted.json | Publication suite result with prompt, response, and evidence text redacted. | public | external_reviewers | application/json | 16931 | `eb81dbe9d96531de574b9ec53c8ccdebcc21be78629df05acc1cdd86329533a0` |
| suite-cases-redacted.jsonl | Publication per-case evidence stream with content-bearing fields redacted. | public | external_reviewers | application/x-ndjson | 1466 | `eea7b74638f92bcad9c7264005fe43481b48785c6db6787bd8be7e2d4ca21e04` |
| suite-report-redacted.html | Standalone redacted report for external browser review. | public | external_reviewers | text/html | 11542 | `61866ee4a73d0716332cf6d8315de0e125823afb7f9c6a23751723d1fd5c55a2` |
| suite-report-redacted.md | Editable redacted report body for external handoff. | public | external_reviewers | text/markdown | 8992 | `13bc63a365baced42d00fc75f08718cb8a64fc0486d20f7e4f3160e74a9fbb94` |
| suite-public-bundle.md | Publication handoff index for lower-sensitivity report sharing. | public | external_reviewers | text/markdown | 2580 | `037cff9a40d24384b54d3a3c9730e721b76229be3cfc01968a2a916ea6062906` |

## Integrity Manifest

- `suite-manifest.json` records artifact size and SHA256 values.
- The manifest is generated after this bundle index so it can include the bundle checksum.

## Schema Contracts

| Schema | Target Artifact | Schema ID |
| --- | --- | --- |
| schemas/suite-result.schema.json | suite-result.json | https://coff0xc.local/forgedan/schemas/suite-result.schema.json |
| schemas/suite-config.schema.json | suite-config.json | https://coff0xc.local/forgedan/schemas/suite-config.schema.json |
| schemas/suite-manifest.schema.json | suite-manifest.json | https://coff0xc.local/forgedan/schemas/suite-manifest.schema.json |
| schemas/suite-comparison.schema.json | suite-comparison.json | https://coff0xc.local/forgedan/schemas/suite-comparison.schema.json |
| schemas/suite-comparison-manifest.schema.json | suite-comparison-manifest.json | https://coff0xc.local/forgedan/schemas/suite-comparison-manifest.schema.json |
| schemas/suite-qa-receipt.schema.json | suite-qa-receipt.json | https://coff0xc.local/forgedan/schemas/suite-qa-receipt.schema.json |
| schemas/suite-preflight.schema.json | suite-preflight.json | https://coff0xc.local/forgedan/schemas/suite-preflight.schema.json |
| schemas/suite-risk-register.schema.json | suite-risk-register.json | https://coff0xc.local/forgedan/schemas/suite-risk-register.schema.json |
| schemas/suite-coverage.schema.json | suite-coverage.json | https://coff0xc.local/forgedan/schemas/suite-coverage.schema.json |
| schemas/finding-taxonomy.schema.json | finding-taxonomy.json | https://coff0xc.local/forgedan/schemas/finding-taxonomy.schema.json |

## Verification Commands

- `forgedan suite verify-bundle suite-manifest.json`
- `forgedan suite qa-report suite-manifest.json`
- `forgedan suite archive suite-manifest.json --output handoff.zip`
- `forgedan suite verify-archive handoff.zip`

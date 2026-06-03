# Report Bundle: ready-for-handoff-suite

## Run Summary

- Run ID: `cc90e3cf-040f-4366-9f08-5e9c1df63ca0`
- Model: `mock:test-model`
- Completed at: `2026-06-03T06:47:41.041283Z`
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
| suite-result.json | Machine-readable suite result and report source data. | restricted | authorized_reviewers | application/json | 16167 | `fb46d02eb1a7a6351c0da7ccb0d49cf780e36cc5fcb931e6b64d3a4c2f3430f8` |
| suite-cases.jsonl | Per-case evidence stream for audit sampling and replay. | restricted | authorized_reviewers | application/x-ndjson | 1498 | `9d7b3f24ba250d1e2f94e48f2c3bc420c8769c655de83343f9f6c454bc9c3391` |
| suite-evidence.csv | Finding evidence matrix for report appendix review. | restricted | authorized_reviewers | text/csv | 232 | `4a83ed85fab8e7bfad546190e313377de52b028b9e3f867bc994fcafe63a9f96` |
| suite-case-matrix.csv | Case-level coverage and risk matrix for report appendix review. | public | external_reviewers | text/csv | 939 | `a9127ff0db59328f16d8f8680262f8e39c1fb6c8e9ef9ddd70b1f46eb947ec74` |
| suite-risk-register.json | Machine-readable remediation risk register derived from normalized findings. | internal | assessment_team | application/json | 259 | `d5b13b1828175f4cd9428ad6feae75073aaec20cc840336317689db0fefbb93f` |
| suite-risk-register.csv | Spreadsheet-ready remediation tracker with evidence hashes and owner/status fields. | internal | assessment_team | text/csv | 223 | `e96f0d29db9abc84e31aed106c958dc50f23420deff90d52e1f2415fdd67a6dc` |
| suite-coverage.json | Machine-readable assessment coverage summary by case category, policy domain, and OWASP LLM category. | public | external_reviewers | application/json | 1027 | `91da7b9f3bf59fe36a1cfffad961a54d6847c84af41701498ca6ce4d72a79cd9` |
| suite-coverage.csv | Spreadsheet-ready coverage matrix for reviewer handoff. | public | external_reviewers | text/csv | 230 | `f3d07a2f6bfb3139601409fc00d9a8fd06e7890d3ca4698e6dcc22ff1d299e61` |
| suite-config.json | Normalized suite input configuration snapshot for audit replay. | internal | assessment_team | application/json | 3121 | `88d841f916cee298e23860c3f8b6e2726c8805d628d78b71159af68f474f742c` |
| suite-preflight.json | Machine-readable run-before-use report readiness audit. | internal | assessment_team | application/json | 3736 | `89023e17bbbe7a32fad456a2eb0a49ade206c38a4692716460838d1c1dfcfd38` |
| suite-preflight.md | Reviewer-readable run-before-use report readiness audit. | internal | assessment_team | text/markdown | 1894 | `acc921b6e2c053361665e3e5a3bca4ecca6af0b5096acdc08fdc94791426d73a` |
| suite-report.html | Standalone human-readable report for browser review. | restricted | authorized_reviewers | text/html | 11408 | `3f34516292e6dfbd737d45e97a7ebba4943bb21edac547b9a940ebf07cb6465b` |
| suite-report.md | Editable report body for report packs and version control. | restricted | authorized_reviewers | text/markdown | 8858 | `df0564e92a7ba0ee4e8818e4fc57348a3fe67de3caf947ed012b2bd89423efae` |
| suite-release-notes.md | Reviewer-facing release notes summarizing run status, handoff gates, and report-pack pointers. | restricted | authorized_reviewers | text/markdown | 2099 | `ff752332735aacb89d084606e9298f39b3b2c8ba025254b2c38f3a6b55170e66` |
| suite-result-redacted.json | Publication suite result with prompt, response, and evidence text redacted. | public | external_reviewers | application/json | 16549 | `04ebe53a6d3a3c553272a0aa6416a80cfd84ffe108aecf37a7ebc78ab1c0a532` |
| suite-cases-redacted.jsonl | Publication per-case evidence stream with content-bearing fields redacted. | public | external_reviewers | application/x-ndjson | 1516 | `90fa882e46b09c4fc56b659379ea8af6aa06fc40406628c52f550a961ad378d9` |
| suite-report-redacted.html | Standalone redacted report for external browser review. | public | external_reviewers | text/html | 11572 | `d8d5db1a3b9e1b0a49488ce985c05b55cd7dafdc98beb8c2b13ff17dc793d74d` |
| suite-report-redacted.md | Editable redacted report body for external handoff. | public | external_reviewers | text/markdown | 9022 | `9c76257732d4b5be2e43890804fc2f9a32bf3d513c000bca7bbf28209969872b` |
| suite-public-bundle.md | Publication handoff index for lower-sensitivity report sharing. | public | external_reviewers | text/markdown | 2595 | `0ee858d4565efcf4db9bdba0ec84aaa7c7ca35f5da534a98df9333c428ba515d` |

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

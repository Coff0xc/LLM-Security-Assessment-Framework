# Report Bundle: ready-for-handoff-suite

## Run Summary

- Run ID: `f6ffb806-28b9-4eab-a5b0-6095552740fc`
- Model: `mock:test-model`
- Completed at: `2026-06-03T08:13:58.962913Z`
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
| suite-result.json | Machine-readable suite result and report source data. | restricted | authorized_reviewers | application/json | 16166 | `aeaeeadd9faa1a13d352af70038ebd4d0ac2e8f1e332ad4de5fce4eac52c2108` |
| suite-cases.jsonl | Per-case evidence stream for audit sampling and replay. | restricted | authorized_reviewers | application/x-ndjson | 1497 | `3674f1c589ba947667044795defc6699ffc1fecac00c54021646722bef1da11c` |
| suite-evidence.csv | Finding evidence matrix for report appendix review. | restricted | authorized_reviewers | text/csv | 232 | `4a83ed85fab8e7bfad546190e313377de52b028b9e3f867bc994fcafe63a9f96` |
| suite-case-matrix.csv | Case-level coverage and risk matrix for report appendix review. | public | external_reviewers | text/csv | 939 | `6227736569a48066b6fc6f129e42e262def8eaa8093afd6fbbb91ac1d0d836f0` |
| suite-risk-register.json | Machine-readable remediation risk register derived from normalized findings. | internal | assessment_team | application/json | 259 | `f07325defef106faa78852cfeabb0cef0d737f1c69566b359e7cccd03c3e6134` |
| suite-risk-register.csv | Spreadsheet-ready remediation tracker with evidence hashes and owner/status fields. | internal | assessment_team | text/csv | 223 | `e96f0d29db9abc84e31aed106c958dc50f23420deff90d52e1f2415fdd67a6dc` |
| suite-coverage.json | Machine-readable assessment coverage summary by case category, policy domain, and OWASP LLM category. | public | external_reviewers | application/json | 1027 | `562850e715282f7530b5ace01b58fb99052163290b7ad4756d2a2f1fb43bfed8` |
| suite-coverage.csv | Spreadsheet-ready coverage matrix for reviewer handoff. | public | external_reviewers | text/csv | 230 | `211d25fbc472a3408c59da599423c00f8d89b1fe7b3084e074ddf616da30d825` |
| suite-config.json | Normalized suite input configuration snapshot for audit replay. | internal | assessment_team | application/json | 3121 | `88d841f916cee298e23860c3f8b6e2726c8805d628d78b71159af68f474f742c` |
| suite-preflight.json | Machine-readable run-before-use report readiness audit. | internal | assessment_team | application/json | 3736 | `66ed73580ee8bd1628a3f6bebbb2b81c436496d7a6f22685ec1018f9aa46a0ce` |
| suite-preflight.md | Reviewer-readable run-before-use report readiness audit. | internal | assessment_team | text/markdown | 1894 | `2b8674577c1fc9be5ee5267ebb35913c318b992dc1f48c92e68d8bb56b367dd9` |
| suite-report.html | Standalone human-readable report for browser review. | restricted | authorized_reviewers | text/html | 11408 | `dfe7f9523d8b18ea64859d74dc1f557e462755a4ccddb25fbffce2d18bd4154e` |
| suite-report.md | Editable report body for report packs and version control. | restricted | authorized_reviewers | text/markdown | 8858 | `dd1d5d873f0a90a888d971078cc08100b88ed4417b8949c8e0edb5b285b81903` |
| suite-release-notes.md | Reviewer-facing release notes summarizing run status, handoff gates, and report-pack pointers. | restricted | authorized_reviewers | text/markdown | 2099 | `51acd033615780cdfb89e8f3a4aca492d2608e0477ff94a7e6b0da62f17a079a` |
| suite-result-redacted.json | Publication suite result with prompt, response, and evidence text redacted. | public | external_reviewers | application/json | 16548 | `5c2fef57587bc233bcfdb42de8a68ef8e30a5ca5b108f01ab28886f308791041` |
| suite-cases-redacted.jsonl | Publication per-case evidence stream with content-bearing fields redacted. | public | external_reviewers | application/x-ndjson | 1515 | `84bd4c006571c7d416807285ab31c184e6de77c5a16bfd646a1f4c1a627e79e1` |
| suite-report-redacted.html | Standalone redacted report for external browser review. | public | external_reviewers | text/html | 11572 | `39336a01045800ebaaa40c6b47775adf26cbfd2761442cdafc361af1bbcd483a` |
| suite-report-redacted.md | Editable redacted report body for external handoff. | public | external_reviewers | text/markdown | 9022 | `4aee4d3822c577ec44dab134e47d05fa6c8f131577d4c2d90fc2fdc28b153991` |
| suite-public-bundle.md | Publication handoff index for lower-sensitivity report sharing. | public | external_reviewers | text/markdown | 2595 | `95bb792bcf976f6a2e1adaed7ef5c1fbbd897d8c6a388131220e999bcc72ec45` |

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

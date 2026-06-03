# Report QA Receipt: ready-for-handoff-suite

## Summary

- Status: passed
- Run ID: `f6ffb806-28b9-4eab-a5b0-6095552740fc`
- Model: `mock:test-model`
- Generated at: `2026-06-03T08:14:09.474902Z`
- Manifest: `docs/sample-report-pack/ready-for-handoff/suite-manifest.json`
- Manifest size: 8666
- Manifest SHA256: `ac8debccd7a3e4f375d96403494d83c056e61af61d5a16d671d18c2e9cf96bc7`
- Artifacts checked: 20
- Schema validations: 7
- Errors: 0

## Acceptance Gates

- Manifest valid: yes
- Artifacts valid: yes
- Schemas valid: yes
- Report acceptance status: passed
- Report acceptance criteria: 3
- Ready for handoff: yes

## Handoff Readiness

- Status: `passed`
- Score: 100.00%
- Required items: 16
- Passed: 16
- Failed: 0
- Review required: 0
- Blockers: None

## Handoff Checklist

| ID | Status | Required | Evidence | Action |
| --- | --- | --- | --- | --- |
| manifest-verified | passed | yes | suite-manifest.json schema validation passed | Attach the manifest and keep it with the report pack. |
| artifact-integrity | passed | yes | 20 artifacts checked for existence, size, and SHA256 | Re-run verify-bundle after copying or archiving the pack. |
| schema-contracts | passed | yes | suite-config, suite-coverage, suite-manifest, suite-preflight, suite-result, suite-risk-register | Validate JSON artifacts before reviewer handoff. |
| cross-artifact-consistency | passed | yes | checked=suite-result.json, suite-report.md, suite-report.html, suite-report-redacted.md, suite-report-redacted.html, suite-cases.jsonl, suite-evidence.csv, suite-case-matrix.csv, suite-config.json, suite-preflight.json, suite-preflight.md, suite-risk-register.json, suite-risk-register.csv, suite-coverage.json, suite-coverage.csv, suite-release-notes.md, suite-report-bundle.md, suite-public-bundle.md, suite-result-redacted.json, suite-cases-redacted.jsonl; errors=0 | Resolve mismatched run IDs or report counts before handoff. |
| release-notes | passed | yes | suite-release-notes.md | Review suite-release-notes.md before final report sign-off. |
| preflight-readiness | passed | yes | suite-preflight.json status=passed; score=1.0000; blockers=None; artifacts=suite-preflight.json, suite-preflight.md | Keep suite-preflight.json and suite-preflight.md with the report pack. |
| source-inventory | passed | yes | sources=0; generated_cases=0; total_size_bytes=0 | Review imported source paths, SHA256 values, and generated case counts before sign-off. |
| coverage-review | passed | yes | suite-coverage.json, suite-coverage.csv | Review case-category, policy-domain, OWASP LLM, and coverage-gap summaries before sign-off. |
| redacted-publication-pack | passed | yes | suite-result-redacted.json, suite-cases-redacted.jsonl, suite-report-redacted.html, suite-report-redacted.md, suite-public-bundle.md | Use the redacted/public artifacts for lower-sensitivity sharing. |
| raw-artifact-handling | passed | yes | acceptance_criteria.raw-artifact-handling: Raw prompts and responses restricted to authorized reviewers. | Restrict raw prompts, responses, and evidence to authorized reviewers. |
| policy-gate | passed | yes | suite-result.json policy_passed=true | Resolve failed policy gates or document accepted risk. |
| review-decisions | passed | yes | decisions=0; policy_violations=0 | Document accepted risk, mitigation requirements, or rejection decisions for policy exceptions. |
| risk-owner-assignment | passed | yes | risks=0; assigned_owners=0; due_dates=0 | Assign owners and due dates for open report risks before handoff. |
| residual-risk-owner-signoff | passed | yes | acceptance_criteria.residual-risk-owner-signoff: No open residual risks require exception approval for this sample. | Record residual risk owner sign-off or accepted risk evidence before handoff. |
| acceptance-criteria | passed | yes | criteria=3; status=passed | Resolve failed acceptance criteria before report handoff. |
| limitations-reviewed | passed | yes | acceptance_criteria.limitations-reviewed: Report limitations match the scoped assessment. | Confirm limitations match the assessment scope before sign-off. |

## Cross-Artifact Consistency

- Valid: yes
- Checked artifacts: suite-result.json, suite-report.md, suite-report.html, suite-report-redacted.md, suite-report-redacted.html, suite-cases.jsonl, suite-evidence.csv, suite-case-matrix.csv, suite-config.json, suite-preflight.json, suite-preflight.md, suite-risk-register.json, suite-risk-register.csv, suite-coverage.json, suite-coverage.csv, suite-release-notes.md, suite-report-bundle.md, suite-public-bundle.md, suite-result-redacted.json, suite-cases-redacted.jsonl
- Errors: 0
- Error details:
  - None

## Run Environment

- ForgeDAN version: `1.2.0`
- Python version: `3.14.5`
- Python implementation: `CPython`
- Platform: `Windows-11-10.0.26100-SP0`
- OS: `Windows`

## Artifact Checks

| Artifact | Valid | Sensitivity | Audience | Size | SHA256 |
| --- | --- | --- | --- | --- | --- |
| suite-result.json | yes | restricted | authorized_reviewers | 16166 | `aeaeeadd9faa1a13d352af70038ebd4d0ac2e8f1e332ad4de5fce4eac52c2108` |
| suite-cases.jsonl | yes | restricted | authorized_reviewers | 1497 | `3674f1c589ba947667044795defc6699ffc1fecac00c54021646722bef1da11c` |
| suite-evidence.csv | yes | restricted | authorized_reviewers | 232 | `4a83ed85fab8e7bfad546190e313377de52b028b9e3f867bc994fcafe63a9f96` |
| suite-case-matrix.csv | yes | public | external_reviewers | 939 | `6227736569a48066b6fc6f129e42e262def8eaa8093afd6fbbb91ac1d0d836f0` |
| suite-risk-register.json | yes | internal | assessment_team | 259 | `f07325defef106faa78852cfeabb0cef0d737f1c69566b359e7cccd03c3e6134` |
| suite-risk-register.csv | yes | internal | assessment_team | 223 | `e96f0d29db9abc84e31aed106c958dc50f23420deff90d52e1f2415fdd67a6dc` |
| suite-coverage.json | yes | public | external_reviewers | 1027 | `562850e715282f7530b5ace01b58fb99052163290b7ad4756d2a2f1fb43bfed8` |
| suite-coverage.csv | yes | public | external_reviewers | 230 | `211d25fbc472a3408c59da599423c00f8d89b1fe7b3084e074ddf616da30d825` |
| suite-config.json | yes | internal | assessment_team | 3121 | `88d841f916cee298e23860c3f8b6e2726c8805d628d78b71159af68f474f742c` |
| suite-preflight.json | yes | internal | assessment_team | 3736 | `66ed73580ee8bd1628a3f6bebbb2b81c436496d7a6f22685ec1018f9aa46a0ce` |
| suite-preflight.md | yes | internal | assessment_team | 1894 | `2b8674577c1fc9be5ee5267ebb35913c318b992dc1f48c92e68d8bb56b367dd9` |
| suite-report.html | yes | restricted | authorized_reviewers | 11408 | `dfe7f9523d8b18ea64859d74dc1f557e462755a4ccddb25fbffce2d18bd4154e` |
| suite-report.md | yes | restricted | authorized_reviewers | 8858 | `dd1d5d873f0a90a888d971078cc08100b88ed4417b8949c8e0edb5b285b81903` |
| suite-release-notes.md | yes | restricted | authorized_reviewers | 2099 | `51acd033615780cdfb89e8f3a4aca492d2608e0477ff94a7e6b0da62f17a079a` |
| suite-result-redacted.json | yes | public | external_reviewers | 16548 | `5c2fef57587bc233bcfdb42de8a68ef8e30a5ca5b108f01ab28886f308791041` |
| suite-cases-redacted.jsonl | yes | public | external_reviewers | 1515 | `84bd4c006571c7d416807285ab31c184e6de77c5a16bfd646a1f4c1a627e79e1` |
| suite-report-redacted.html | yes | public | external_reviewers | 11572 | `39336a01045800ebaaa40c6b47775adf26cbfd2761442cdafc361af1bbcd483a` |
| suite-report-redacted.md | yes | public | external_reviewers | 9022 | `4aee4d3822c577ec44dab134e47d05fa6c8f131577d4c2d90fc2fdc28b153991` |
| suite-public-bundle.md | yes | public | external_reviewers | 2595 | `95bb792bcf976f6a2e1adaed7ef5c1fbbd897d8c6a388131220e999bcc72ec45` |
| suite-report-bundle.md | yes | restricted | authorized_reviewers | 7232 | `1fbb9c9f3bb289f35f91ce5a674e145c98ff690f4cba6db622838406cc375ea0` |

## Schema Checks

| Artifact | Schema | Valid | Errors |
| --- | --- | --- | --- |
| suite-manifest.json | suite-manifest | yes | 0 |
| suite-result.json | suite-result | yes | 0 |
| suite-risk-register.json | suite-risk-register | yes | 0 |
| suite-coverage.json | suite-coverage | yes | 0 |
| suite-config.json | suite-config | yes | 0 |
| suite-preflight.json | suite-preflight | yes | 0 |
| suite-result-redacted.json | suite-result | yes | 0 |

## Errors

- None

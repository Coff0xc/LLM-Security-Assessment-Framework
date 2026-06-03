# Report QA Receipt: ready-for-handoff-suite

## Summary

- Status: passed
- Run ID: `cc90e3cf-040f-4366-9f08-5e9c1df63ca0`
- Model: `mock:test-model`
- Generated at: `2026-06-03T06:47:51.895676Z`
- Manifest: `docs\sample-report-pack\ready-for-handoff\suite-manifest.json`
- Manifest size: 8666
- Manifest SHA256: `faff440ce74440b6f4c33e3ce37339459cea3e4f8b92e68edc29487cf3541082`
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
| suite-result.json | yes | restricted | authorized_reviewers | 16167 | `fb46d02eb1a7a6351c0da7ccb0d49cf780e36cc5fcb931e6b64d3a4c2f3430f8` |
| suite-cases.jsonl | yes | restricted | authorized_reviewers | 1498 | `9d7b3f24ba250d1e2f94e48f2c3bc420c8769c655de83343f9f6c454bc9c3391` |
| suite-evidence.csv | yes | restricted | authorized_reviewers | 232 | `4a83ed85fab8e7bfad546190e313377de52b028b9e3f867bc994fcafe63a9f96` |
| suite-case-matrix.csv | yes | public | external_reviewers | 939 | `a9127ff0db59328f16d8f8680262f8e39c1fb6c8e9ef9ddd70b1f46eb947ec74` |
| suite-risk-register.json | yes | internal | assessment_team | 259 | `d5b13b1828175f4cd9428ad6feae75073aaec20cc840336317689db0fefbb93f` |
| suite-risk-register.csv | yes | internal | assessment_team | 223 | `e96f0d29db9abc84e31aed106c958dc50f23420deff90d52e1f2415fdd67a6dc` |
| suite-coverage.json | yes | public | external_reviewers | 1027 | `91da7b9f3bf59fe36a1cfffad961a54d6847c84af41701498ca6ce4d72a79cd9` |
| suite-coverage.csv | yes | public | external_reviewers | 230 | `f3d07a2f6bfb3139601409fc00d9a8fd06e7890d3ca4698e6dcc22ff1d299e61` |
| suite-config.json | yes | internal | assessment_team | 3121 | `88d841f916cee298e23860c3f8b6e2726c8805d628d78b71159af68f474f742c` |
| suite-preflight.json | yes | internal | assessment_team | 3736 | `89023e17bbbe7a32fad456a2eb0a49ade206c38a4692716460838d1c1dfcfd38` |
| suite-preflight.md | yes | internal | assessment_team | 1894 | `acc921b6e2c053361665e3e5a3bca4ecca6af0b5096acdc08fdc94791426d73a` |
| suite-report.html | yes | restricted | authorized_reviewers | 11408 | `3f34516292e6dfbd737d45e97a7ebba4943bb21edac547b9a940ebf07cb6465b` |
| suite-report.md | yes | restricted | authorized_reviewers | 8858 | `df0564e92a7ba0ee4e8818e4fc57348a3fe67de3caf947ed012b2bd89423efae` |
| suite-release-notes.md | yes | restricted | authorized_reviewers | 2099 | `ff752332735aacb89d084606e9298f39b3b2c8ba025254b2c38f3a6b55170e66` |
| suite-result-redacted.json | yes | public | external_reviewers | 16549 | `04ebe53a6d3a3c553272a0aa6416a80cfd84ffe108aecf37a7ebc78ab1c0a532` |
| suite-cases-redacted.jsonl | yes | public | external_reviewers | 1516 | `90fa882e46b09c4fc56b659379ea8af6aa06fc40406628c52f550a961ad378d9` |
| suite-report-redacted.html | yes | public | external_reviewers | 11572 | `d8d5db1a3b9e1b0a49488ce985c05b55cd7dafdc98beb8c2b13ff17dc793d74d` |
| suite-report-redacted.md | yes | public | external_reviewers | 9022 | `9c76257732d4b5be2e43890804fc2f9a32bf3d513c000bca7bbf28209969872b` |
| suite-public-bundle.md | yes | public | external_reviewers | 2595 | `0ee858d4565efcf4db9bdba0ec84aaa7c7ca35f5da534a98df9333c428ba515d` |
| suite-report-bundle.md | yes | restricted | authorized_reviewers | 7232 | `dc6df5d3c914f574865e220de298c2269b85e40806bb3381cc42ca9ffa8d684c` |

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

# Report QA Receipt: ready-for-handoff-suite

## Summary

- Status: passed
- Run ID: `ready-for-handoff-sample-run`
- Model: `mock:test-model`
- Generated at: `2026-06-03T00:00:02Z`
- Manifest: `docs/sample-report-pack/ready-for-handoff/suite-manifest.json`
- Manifest size: 8651
- Manifest SHA256: `3f28af1bf4b78709fb6b673ca765e33425e696bf21b3cd6b6f9f0c4c4d540d56`
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
| suite-result.json | yes | restricted | authorized_reviewers | 16549 | `595291ef136b75a62724556bc5890df1d8c211eb8ce28e8cc803defdc5ab433e` |
| suite-cases.jsonl | yes | restricted | authorized_reviewers | 1448 | `e9647b6e7e447fa11454aae637414fe8deb7481c469588574eb29750d5f096a6` |
| suite-evidence.csv | yes | restricted | authorized_reviewers | 232 | `4a83ed85fab8e7bfad546190e313377de52b028b9e3f867bc994fcafe63a9f96` |
| suite-case-matrix.csv | yes | public | external_reviewers | 914 | `f47849e890deea974b0553868e25f8966dab04c9f652333a14df3b0ceae64b24` |
| suite-risk-register.json | yes | internal | assessment_team | 244 | `cf130b8ac581b36b3123ccd8b6a3c922c8ab967d0c0412d8e54cfc3fbf0cc6ef` |
| suite-risk-register.csv | yes | internal | assessment_team | 223 | `e96f0d29db9abc84e31aed106c958dc50f23420deff90d52e1f2415fdd67a6dc` |
| suite-coverage.json | yes | public | external_reviewers | 1012 | `bee2476b3b6e59fdbf7e153037e5ad52a67a57b38393bae84f853167ba193405` |
| suite-coverage.csv | yes | public | external_reviewers | 222 | `c44a9785952f4fda904da2812065e14b9dccf612075eb74bda0167f641c7e975` |
| suite-config.json | yes | internal | assessment_team | 3567 | `bdb9395bf869795dc4c16521982941a1ab4b4999c8996a81be2a89bad9bbef01` |
| suite-preflight.json | yes | internal | assessment_team | 3729 | `2984aa398c6cc387c80dfe1d7bd7dc13fdee164a71e4ac4975a547c0c9d40d7a` |
| suite-preflight.md | yes | internal | assessment_team | 1887 | `63309d4e516e7adaee9eda0627b8230cb45b2785e8c2b4a11b7214ff44b2543c` |
| suite-report.html | yes | restricted | authorized_reviewers | 11378 | `83463ee88145c3527ac33248e4c381c7496752beae8e1a2c5d53afc18d739ae2` |
| suite-report.md | yes | restricted | authorized_reviewers | 8828 | `af4434309b905f4d49e8b1901138c41b186d614723748f3d51af4a70b28640b6` |
| suite-release-notes.md | yes | restricted | authorized_reviewers | 2084 | `10a45f7acfa4dd92ad08cb39cd0ddbdb609df68154f65e7d5d1f8b8c047cb848` |
| suite-result-redacted.json | yes | public | external_reviewers | 16931 | `eb81dbe9d96531de574b9ec53c8ccdebcc21be78629df05acc1cdd86329533a0` |
| suite-cases-redacted.jsonl | yes | public | external_reviewers | 1466 | `eea7b74638f92bcad9c7264005fe43481b48785c6db6787bd8be7e2d4ca21e04` |
| suite-report-redacted.html | yes | public | external_reviewers | 11542 | `61866ee4a73d0716332cf6d8315de0e125823afb7f9c6a23751723d1fd5c55a2` |
| suite-report-redacted.md | yes | public | external_reviewers | 8992 | `13bc63a365baced42d00fc75f08718cb8a64fc0486d20f7e4f3160e74a9fbb94` |
| suite-public-bundle.md | yes | public | external_reviewers | 2580 | `037cff9a40d24384b54d3a3c9730e721b76229be3cfc01968a2a916ea6062906` |
| suite-report-bundle.md | yes | restricted | authorized_reviewers | 7217 | `1dad1eee6ef90d2512a629a9da007d2feca6279e23a56d1cd2898075efc2aa28` |

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

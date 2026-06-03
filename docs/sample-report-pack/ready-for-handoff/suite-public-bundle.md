# Public Report Bundle: ready-for-handoff-suite

## Run Summary

- Run ID: `ready-for-handoff-sample-run`
- Model: `mock:test-model`
- Completed at: `2026-06-03T00:00:01Z`
- Risk level: `none`
- Cases: 1
- Attack success rate: 0.00%
- Max risk score: 0.00
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

## Redaction Policy

- Raw `best_prompt`, `best_response`, and finding evidence fields are replaced with SHA256-based placeholders.
- Secret and email-like strings in metadata are masked while preserving the report structure.
- Restricted raw artifacts remain in the full report pack for authorized audit replay.
- `suite-manifest.json` records checksums for both restricted and public artifacts.

## Public Artifact Index

| Artifact | Purpose | Media type | Size | SHA256 |
| --- | --- | --- | --- | --- |
| suite-result-redacted.json | Machine-readable suite result with prompt, response, and evidence text redacted. | application/json | 16931 | `eb81dbe9d96531de574b9ec53c8ccdebcc21be78629df05acc1cdd86329533a0` |
| suite-cases-redacted.jsonl | Per-case evidence stream with content-bearing fields replaced by stable hashes. | application/x-ndjson | 1466 | `eea7b74638f92bcad9c7264005fe43481b48785c6db6787bd8be7e2d4ca21e04` |
| suite-report-redacted.html | Standalone redacted report for browser review. | text/html | 11542 | `61866ee4a73d0716332cf6d8315de0e125823afb7f9c6a23751723d1fd5c55a2` |
| suite-report-redacted.md | Editable redacted report body for external handoff. | text/markdown | 8992 | `13bc63a365baced42d00fc75f08718cb8a64fc0486d20f7e4f3160e74a9fbb94` |
| suite-case-matrix.csv | Case-level coverage and risk matrix without prompt or response bodies. | text/csv | 914 | `f47849e890deea974b0553868e25f8966dab04c9f652333a14df3b0ceae64b24` |
| suite-coverage.json | Machine-readable assessment coverage summary without prompt or response bodies. | application/json | 1012 | `bee2476b3b6e59fdbf7e153037e5ad52a67a57b38393bae84f853167ba193405` |
| suite-coverage.csv | Spreadsheet-ready coverage matrix for external reviewer handoff. | text/csv | 222 | `c44a9785952f4fda904da2812065e14b9dccf612075eb74bda0167f641c7e975` |

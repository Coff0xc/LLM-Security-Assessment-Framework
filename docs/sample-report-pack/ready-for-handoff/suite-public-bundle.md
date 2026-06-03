# Public Report Bundle: ready-for-handoff-suite

## Run Summary

- Run ID: `f6ffb806-28b9-4eab-a5b0-6095552740fc`
- Model: `mock:test-model`
- Completed at: `2026-06-03T08:13:58.962913Z`
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
| suite-result-redacted.json | Machine-readable suite result with prompt, response, and evidence text redacted. | application/json | 16548 | `5c2fef57587bc233bcfdb42de8a68ef8e30a5ca5b108f01ab28886f308791041` |
| suite-cases-redacted.jsonl | Per-case evidence stream with content-bearing fields replaced by stable hashes. | application/x-ndjson | 1515 | `84bd4c006571c7d416807285ab31c184e6de77c5a16bfd646a1f4c1a627e79e1` |
| suite-report-redacted.html | Standalone redacted report for browser review. | text/html | 11572 | `39336a01045800ebaaa40c6b47775adf26cbfd2761442cdafc361af1bbcd483a` |
| suite-report-redacted.md | Editable redacted report body for external handoff. | text/markdown | 9022 | `4aee4d3822c577ec44dab134e47d05fa6c8f131577d4c2d90fc2fdc28b153991` |
| suite-case-matrix.csv | Case-level coverage and risk matrix without prompt or response bodies. | text/csv | 939 | `6227736569a48066b6fc6f129e42e262def8eaa8093afd6fbbb91ac1d0d836f0` |
| suite-coverage.json | Machine-readable assessment coverage summary without prompt or response bodies. | application/json | 1027 | `562850e715282f7530b5ace01b58fb99052163290b7ad4756d2a2f1fb43bfed8` |
| suite-coverage.csv | Spreadsheet-ready coverage matrix for external reviewer handoff. | text/csv | 230 | `211d25fbc472a3408c59da599423c00f8d89b1fe7b3084e074ddf616da30d825` |

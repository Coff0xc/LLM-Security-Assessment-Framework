# Release Notes: ready-for-handoff-suite

## Run Summary

- Run ID: `ready-for-handoff-sample-run`
- Model: `mock:test-model`
- Completed at: `2026-06-03T00:00:01Z`
- Cases: 1
- Attack success rate: 0.00%
- Max risk score: 0.00
- Risk level: `none`
- Acceptance status: `passed`
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

## Reviewer Decision Notes

- Review decision count: 0
- Review decision statuses: `{}`
- MCP unreviewed cases: None

## Artifact Pointers

- `suite-report.md` / `suite-report.html`: full narrative report.
- `suite-evidence.csv`: finding evidence matrix.
- `suite-case-matrix.csv`: case-level coverage and outcome matrix.
- `suite-risk-register.json` / `suite-risk-register.csv`: remediation tracker.
- `suite-coverage.json` / `suite-coverage.csv`: assessment coverage summary.
- `suite-preflight.json` / `suite-preflight.md`: run-before-use report readiness audit.
- `suite-public-bundle.md`: lower-sensitivity external handoff index.
- `suite-report-bundle.md`: full report-pack index with checksums.
- `suite-manifest.json`: integrity manifest for archive or handoff verification.

## Verification Commands

- `forgedan suite verify-bundle suite-manifest.json`
- `forgedan suite qa-report suite-manifest.json`
- `forgedan suite archive suite-manifest.json --output handoff.zip`
- `forgedan suite verify-archive handoff.zip`

## Notes

- These release notes summarize one generated report pack. Use `forgedan suite compare` when a historical baseline is required.
- Policy failures remain visible here even when reviewer decisions document accepted risk or required mitigation.

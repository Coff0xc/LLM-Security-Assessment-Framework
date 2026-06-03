# Suite Preflight: ready-for-handoff-suite

- Schema version: `suite-preflight.v1`
- Generated at: `2026-06-03T06:47:41.046821Z`
- Model: `mock:test-model`
- Cases: 1
- Status: `passed`
- Ready for report: yes
- Score: 100.00%
- Passed: 10
- Review required: 0
- Failed: 0
- Not applicable: 2
- Blockers: None

## Checks

| ID | Status | Severity | Evidence | Action |
| --- | --- | --- | --- | --- |
| report-metadata | passed | recommended | assessment_id=LLM-HANDOFF-001; reviewers=1 | No action required. |
| acceptance-criteria | passed | required | criteria=3; status=passed | No action required. |
| risk-register-defaults | passed | recommended | owner=Risk Owner; due_date=2026-06-15; status=open | No action required. |
| policy-gates | passed | recommended | configured policy gates=5 | No action required. |
| case-coverage | passed | required | cases=1; categories=baseline | No action required. |
| scorer-definitions | passed | required | scorers=target_prefix, refusal, response_safety | No action required. |
| deterministic-replay | passed | recommended | random_seed=7; response_cache_file=not required | No action required. |
| usage-pricing | passed | recommended | mock/fake model; provider cost estimate not required | No action required. |
| source-inventory | passed | required | external_sources=0; inventory_entries=0 | No action required. |
| mcp-trust-policy | not_applicable | recommended | no mcp_manifest_file configured | No action required. |
| model-serialization-scope | not_applicable | recommended | no model_serialization_files configured | No action required. |
| review-decisions | passed | recommended | decisions=0 | No action required. |

## Notes

- This preflight artifact checks suite readiness before model execution.
- It does not replace `verify-bundle` or the QA receipt generated after a report pack exists.
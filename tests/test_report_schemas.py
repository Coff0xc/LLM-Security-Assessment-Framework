# -*- coding: utf-8 -*-
"""
Report schema contract tests.
"""

import json
from pathlib import Path

from forgedan.finding_taxonomy import TAXONOMY_VERSION, list_finding_taxonomy
from forgedan.suite import (
    SuiteCase,
    SuiteConfig,
    compare_suite_results,
    run_suite,
    write_suite_preflight_report,
    write_suite_qa_receipt,
    write_suite_artifacts,
    write_suite_comparison_artifacts,
)

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_DIR = ROOT / "schemas"


def _load_schema(name: str) -> dict:
    path = SCHEMA_DIR / name
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_required_fields(schema: dict, data: dict):
    for field in schema["required"]:
        assert field in data


def test_report_schema_files_define_required_contracts():
    schema_names = {
        "suite-result.schema.json": {
            "run_id",
            "name",
            "model",
            "findings",
            "cases",
            "usage_summary",
            "run_environment",
            "suite_config",
        },
        "suite-config.schema.json": {
            "name",
            "model",
            "iterations",
            "population",
            "elite",
            "report_metadata",
            "run_metadata",
            "acceptance_criteria",
            "review_decisions",
            "risk_register_defaults",
            "usage_pricing",
            "source_inventory",
            "cases",
        },
        "suite-manifest.schema.json": {
            "schema_version",
            "run_id",
            "artifacts",
            "report_acceptance",
            "schema_count",
            "schemas",
        },
        "suite-comparison.schema.json": {
            "baseline_run_id",
            "current_run_id",
            "deltas",
            "policy_domain_deltas",
            "regressions",
        },
        "suite-comparison-manifest.schema.json": {
            "schema_version",
            "baseline_run_id",
            "current_run_id",
            "comparison",
            "artifacts",
            "schema_count",
            "schemas",
        },
        "suite-qa-receipt.schema.json": {
            "schema_version",
            "manifest_size_bytes",
            "manifest_sha256",
            "run_id",
            "suite",
            "status",
            "acceptance",
            "handoff_readiness",
            "handoff_checklist",
            "cross_artifact_consistency",
            "checked_artifacts",
            "schema_validations",
        },
        "suite-preflight.schema.json": {
            "schema_version",
            "generated_at",
            "suite",
            "model",
            "case_count",
            "status",
            "ready_for_report",
            "score",
            "summary",
            "blockers",
            "checks",
        },
        "suite-risk-register.schema.json": {
            "schema_version",
            "run_id",
            "suite",
            "risk_count",
            "risks",
        },
        "suite-coverage.schema.json": {
            "schema_version",
            "run_id",
            "suite",
            "case_count",
            "case_category_coverage",
            "policy_domain_coverage",
            "taxonomy_category_coverage",
            "owasp_llm_coverage",
        },
        "finding-taxonomy.schema.json": {"taxonomy_version", "findings"},
    }

    for name, required in schema_names.items():
        schema = _load_schema(name)

        assert schema["$schema"] == "https://json-schema.org/draft/2020-12/schema"
        assert schema["$id"].startswith("https://coff0xc.local/forgedan/schemas/")
        assert schema["type"] == "object"
        assert required.issubset(set(schema["required"]))

    manifest_artifact_required = set(
        _load_schema("suite-manifest.schema.json")["properties"]["artifacts"]["items"][
            "required"
        ]
    )
    qa_artifact_required = set(
        _load_schema("suite-qa-receipt.schema.json")["properties"]["checked_artifacts"][
            "items"
        ]["required"]
    )
    assert {"sensitivity", "audience"}.issubset(manifest_artifact_required)
    assert {"sensitivity", "audience"}.issubset(qa_artifact_required)
    qa_handoff_ids = set(
        _load_schema("suite-qa-receipt.schema.json")["properties"]["handoff_checklist"][
            "items"
        ]["properties"]["id"]["enum"]
    )
    assert qa_handoff_ids == {
        "manifest-verified",
        "artifact-integrity",
        "schema-contracts",
        "cross-artifact-consistency",
        "release-notes",
        "preflight-readiness",
        "source-inventory",
        "coverage-review",
        "redacted-publication-pack",
        "raw-artifact-handling",
        "policy-gate",
        "review-decisions",
        "risk-owner-assignment",
        "residual-risk-owner-signoff",
        "acceptance-criteria",
        "limitations-reviewed",
    }
    qa_cross_artifact_names = set(
        _load_schema("suite-qa-receipt.schema.json")["properties"][
            "cross_artifact_consistency"
        ]["properties"]["checked_artifacts"]["items"]["enum"]
    )
    assert qa_cross_artifact_names == {
        "suite-result.json",
        "suite-report.md",
        "suite-report.html",
        "suite-report-redacted.md",
        "suite-report-redacted.html",
        "suite-cases.jsonl",
        "suite-evidence.csv",
        "suite-case-matrix.csv",
        "suite-config.json",
        "suite-preflight.json",
        "suite-preflight.md",
        "suite-risk-register.json",
        "suite-risk-register.csv",
        "suite-coverage.json",
        "suite-coverage.csv",
        "suite-release-notes.md",
        "suite-report-bundle.md",
        "suite-public-bundle.md",
        "suite-result-redacted.json",
        "suite-cases-redacted.jsonl",
    }
    preflight_check_ids = set(
        _load_schema("suite-preflight.schema.json")["properties"]["checks"]["items"][
            "properties"
        ]["id"]["enum"]
    )
    assert {
        "report-metadata",
        "acceptance-criteria",
        "risk-register-defaults",
        "policy-gates",
        "case-coverage",
        "scorer-definitions",
        "deterministic-replay",
        "usage-pricing",
        "source-inventory",
        "mcp-trust-policy",
        "model-serialization-scope",
        "review-decisions",
    }.issubset(preflight_check_ids)
    suite_config_policy_properties = set(
        _load_schema("suite-config.schema.json")["properties"]["policy"]["properties"]
    )
    assert "allowed_mcp_trust_tiers" in suite_config_policy_properties
    suite_config_properties = _load_schema("suite-config.schema.json")["properties"]
    assert "usage_pricing" in suite_config_properties
    assert "usage_pricing_file" in suite_config_properties
    assert "response_cache_file" in suite_config_properties
    assert "random_seed" in suite_config_properties
    assert "run_metadata" in suite_config_properties
    run_metadata_properties = suite_config_properties["run_metadata"]["properties"]
    assert "generated_at" in run_metadata_properties
    assert "duration_seconds" in run_metadata_properties
    assert "model_serialization_files" in suite_config_properties
    assert "mcp_trust_policy_file" in suite_config_properties
    assert "mcp_trust_tiers" in suite_config_properties
    assert "scorer_definitions" in suite_config_properties

    suite_result_schema = _load_schema("suite-result.schema.json")
    suite_result_report_sections = suite_result_schema["properties"]["report_sections"][
        "properties"
    ]
    assert "response_cache" in suite_result_report_sections
    assert "model_serialization" in suite_result_report_sections
    source_type_enum = set(
        suite_config_properties["source_inventory"]["items"]["properties"][
            "source_type"
        ]["enum"]
    )
    result_source_type_enum = set(
        suite_result_schema["properties"]["suite_config"]["properties"][
            "source_inventory"
        ]["items"]["properties"]["source_type"]["enum"]
    )
    assert "model_serialization_file" in source_type_enum
    assert "model_serialization_file" in result_source_type_enum
    assert "mcp_trust_policy_file" in source_type_enum
    assert "mcp_trust_policy_file" in result_source_type_enum
    finding_required = set(
        suite_result_schema["properties"]["findings"]["items"]["required"]
    )
    finding_summary_required = set(
        suite_result_schema["properties"]["finding_summary"]["required"]
    )
    assert {"severity_rationale", "evidence_fingerprint"}.issubset(finding_required)
    assert "duplicate_evidence_groups" in finding_summary_required
    assert (
        "source_inventory"
        in suite_result_schema["properties"]["suite_config"]["required"]
    )


def test_report_schemas_cover_generated_required_fields(tmp_path):
    suite = SuiteConfig(
        name="schema-suite",
        cases=[SuiteCase(name="schema-case", goal="test safety boundary")],
    )
    result = run_suite(suite)
    artifact_paths = write_suite_artifacts(result, tmp_path)
    suite_result = json.loads(
        artifact_paths["summary_json"].read_text(encoding="utf-8")
    )
    suite_config = json.loads(
        artifact_paths["suite_config_json"].read_text(encoding="utf-8")
    )
    manifest = json.loads(artifact_paths["manifest_json"].read_text(encoding="utf-8"))
    risk_register = json.loads(
        artifact_paths["risk_register_json"].read_text(encoding="utf-8")
    )
    coverage = json.loads(artifact_paths["coverage_json"].read_text(encoding="utf-8"))
    receipt_paths = write_suite_qa_receipt(
        artifact_paths["manifest_json"], tmp_path / "qa"
    )
    qa_receipt = json.loads(receipt_paths["json"].read_text(encoding="utf-8"))
    preflight = json.loads(
        artifact_paths["suite_preflight_json"].read_text(encoding="utf-8")
    )
    preflight_paths = write_suite_preflight_report(suite, tmp_path / "preflight")
    standalone_preflight = json.loads(
        preflight_paths["json"].read_text(encoding="utf-8")
    )
    comparison = compare_suite_results(suite_result, suite_result)
    comparison_paths = write_suite_comparison_artifacts(
        comparison,
        tmp_path / "suite-comparison.json",
    )
    comparison_json = json.loads(
        comparison_paths["comparison_json"].read_text(encoding="utf-8")
    )
    taxonomy_payload = {
        "taxonomy_version": TAXONOMY_VERSION,
        "findings": list_finding_taxonomy(),
    }

    _assert_required_fields(_load_schema("suite-result.schema.json"), suite_result)
    assert suite_result["usage_summary"]["total_tokens"] >= 0
    assert suite_result["run_environment"]["forgedan_version"] == "1.2.0"
    assert suite_result["run_environment"]["python_version"]
    assert suite_result["suite_config"]["name"] == "schema-suite"
    assert "report_metadata" in suite_result["suite_config"]
    assert "run_metadata" in suite_result["suite_config"]
    assert "acceptance_criteria" in suite_result["suite_config"]
    assert "review_decisions" in suite_result["suite_config"]
    assert "risk_register_defaults" in suite_result["suite_config"]
    assert "usage_pricing" in suite_result["suite_config"]
    assert "random_seed" in suite_result["suite_config"]
    assert "response_cache_file" in suite_result["suite_config"]
    assert "model_serialization_files" in suite_result["suite_config"]
    assert "mcp_trust_policy_file" in suite_result["suite_config"]
    assert "mcp_trust_tiers" in suite_result["suite_config"]
    assert "acceptance" in suite_result["report_sections"]
    assert "review_decisions" in suite_result["report_sections"]
    assert "response_cache" in suite_result["report_sections"]
    assert "model_serialization" in suite_result["report_sections"]
    _assert_required_fields(_load_schema("suite-config.schema.json"), suite_config)
    assert suite_result["report_sections"]["usage"]["total_tokens"] >= 0
    assert "usage" in suite_result["cases"][0]
    assert all("confidence" in item for item in suite_result["findings"])
    assert all("policy_domain" in item for item in suite_result["findings"])
    _assert_required_fields(_load_schema("suite-manifest.schema.json"), manifest)
    assert manifest["report_acceptance"]["status"] == "not_configured"
    assert manifest["report_acceptance"]["criteria_count"] == 0
    _assert_required_fields(
        _load_schema("suite-risk-register.schema.json"), risk_register
    )
    _assert_required_fields(_load_schema("suite-coverage.schema.json"), coverage)
    assert coverage["schema_version"] == "suite-coverage.v1"
    assert coverage["case_count"] == suite_result["total_cases"]
    assert coverage["case_category_coverage"]
    _assert_required_fields(_load_schema("suite-qa-receipt.schema.json"), qa_receipt)
    assert qa_receipt["schema_version"] == "suite-qa-receipt.v1"
    assert qa_receipt["acceptance"]["ready_for_handoff"] is True
    assert "handoff_readiness" in qa_receipt
    assert all(
        "required_for_handoff" in item for item in qa_receipt["handoff_checklist"]
    )
    _assert_required_fields(_load_schema("suite-preflight.schema.json"), preflight)
    assert preflight["schema_version"] == "suite-preflight.v1"
    assert preflight["checks"]
    _assert_required_fields(
        _load_schema("suite-preflight.schema.json"), standalone_preflight
    )
    _assert_required_fields(
        _load_schema("suite-comparison.schema.json"), comparison_json
    )
    _assert_required_fields(
        _load_schema("finding-taxonomy.schema.json"), taxonomy_payload
    )
    assert all("owasp_llm_id" in item for item in taxonomy_payload["findings"])
    assert all("owasp_llm_category" in item for item in taxonomy_payload["findings"])
    assert all("policy_domain" in item for item in taxonomy_payload["findings"])

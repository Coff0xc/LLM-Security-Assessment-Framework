# -*- coding: utf-8 -*-
"""
Checked-in sample report pack contract tests.
"""

import hashlib
import re
from pathlib import Path

from forgedan.suite import (
    archive_suite_bundle,
    load_suite_config,
    run_suite,
    validate_report_artifact,
    verify_suite_archive,
    verify_suite_manifest,
    write_suite_artifacts,
    write_suite_qa_receipt,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PACK = ROOT / "docs" / "sample-report-pack" / "ready-for-handoff"
SAMPLE_SUITE = ROOT / "examples" / "ready-for-handoff-suite.yml"


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_ready_for_handoff_sample_pack_stays_verified():
    manifest_path = SAMPLE_PACK / "suite-manifest.json"
    receipt_path = SAMPLE_PACK / "suite-qa-receipt.json"
    archive_path = SAMPLE_PACK / "handoff.zip"

    bundle = verify_suite_manifest(manifest_path)
    receipt = validate_report_artifact(receipt_path)
    archive = verify_suite_archive(archive_path)

    assert bundle["valid"] is True, bundle["errors"]
    assert bundle["artifact_count"] == 20
    assert bundle["schema_validation_count"] == 7
    assert receipt["valid"] is True, receipt["errors"]
    assert archive["valid"] is True, archive["errors"]
    assert archive["artifact_count"] == 20
    assert archive["supplemental_artifact_count"] == 2
    assert archive["schema_validation_count"] == 8


def test_ready_for_handoff_sample_readme_matches_archive_hash_and_commands():
    readme = (SAMPLE_PACK / "README.md").read_text(encoding="utf-8")
    archive_path = SAMPLE_PACK / "handoff.zip"
    actual_sha256 = _sha256(archive_path)
    match = re.search(r"`handoff\.zip` SHA256:\s+```text\s+([0-9a-f]{64})", readme)

    assert match is not None
    assert match.group(1) == actual_sha256
    assert (
        "forgedan suite verify-bundle "
        "docs/sample-report-pack/ready-for-handoff/suite-manifest.json"
    ) in readme
    assert (
        "forgedan suite validate-report "
        "docs/sample-report-pack/ready-for-handoff/suite-qa-receipt.json"
    ) in readme
    assert (
        "forgedan suite verify-archive "
        "docs/sample-report-pack/ready-for-handoff/handoff.zip"
    ) in readme
    assert (
        "- `verify-archive`: passed, 20 manifest artifacts checked, "
        "2 supplemental QA receipt sidecars, 8 schema validations."
    ) in readme


def test_ready_for_handoff_sample_pack_can_be_rebuilt_byte_for_byte(
    tmp_path, monkeypatch
):
    monkeypatch.chdir(tmp_path)
    # QA receipts intentionally record the report pack handoff path, so rebuild
    # the sample under the same repository-relative delivery path.
    output_dir = SAMPLE_PACK.relative_to(ROOT)

    result = run_suite(load_suite_config(SAMPLE_SUITE))
    paths = write_suite_artifacts(result, output_dir)
    write_suite_qa_receipt(paths["manifest_json"], output_dir)
    archive_suite_bundle(paths["manifest_json"], output_dir / "handoff.zip")

    expected_files = sorted(
        path.relative_to(SAMPLE_PACK).as_posix()
        for path in SAMPLE_PACK.iterdir()
        if path.is_file() and path.name != "README.md"
    )
    rebuilt_files = sorted(
        path.relative_to(output_dir).as_posix()
        for path in output_dir.iterdir()
        if path.is_file()
    )

    assert rebuilt_files == expected_files
    assert {
        relative_path: _sha256(output_dir / relative_path)
        for relative_path in rebuilt_files
    } == {
        relative_path: _sha256(SAMPLE_PACK / relative_path)
        for relative_path in expected_files
    }

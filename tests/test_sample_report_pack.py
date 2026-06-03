# -*- coding: utf-8 -*-
"""
Checked-in sample report pack contract tests.
"""

import hashlib
import re
from pathlib import Path

from forgedan.suite import (
    validate_report_artifact,
    verify_suite_archive,
    verify_suite_manifest,
)

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_PACK = ROOT / "docs" / "sample-report-pack" / "ready-for-handoff"


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
    actual_sha256 = hashlib.sha256(archive_path.read_bytes()).hexdigest()
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

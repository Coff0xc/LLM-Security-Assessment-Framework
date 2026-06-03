# -*- coding: utf-8 -*-
"""
CI workflow contract tests for report delivery gates.
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_ci_archives_and_verifies_report_handoff_packs():
    workflow = (ROOT / ".github" / "workflows" / "ci.yml").read_text(encoding="utf-8")

    for report_dir in ("suite-smoke", "suite-ready"):
        archive_command = (
            "python -m forgedan.cli suite archive "
            f"reports/{report_dir}/suite-manifest.json "
            f"--output reports/{report_dir}/handoff.zip"
        )
        verify_command = (
            "python -m forgedan.cli suite verify-archive "
            f"reports/{report_dir}/handoff.zip"
        )

        assert archive_command in workflow
        assert verify_command in workflow
        assert workflow.index(archive_command) < workflow.index(verify_command)

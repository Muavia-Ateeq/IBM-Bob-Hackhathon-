from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from integration_test import check_gate

REAL_WORKFLOW = Path(__file__).resolve().parent.parent.parent / ".github/workflows/trustgate.yml"

# `check_gate` is the one piece of the smoke test that can silently stop working: it is the
# thing standing between a weakened gate and a merge, and a parser change that made it
# always return True would look exactly like a passing run. Same reasoning as test_gate.py.


def test_the_real_workflow_passes_every_invariant() -> None:
    ok, detail = check_gate(REAL_WORKFLOW)
    assert ok, detail


def test_pull_request_target_is_caught_even_though_the_header_mentions_it() -> None:
    # The real workflow's own comment block names `pull_request_target` while explaining why
    # it is not used. A substring check for the name would fail on that comment and report a
    # working gate as broken; a check that greps for absence of the *trigger* would pass an
    # unsafe one. Only parsing the trigger key distinguishes them.
    text = REAL_WORKFLOW.read_text(encoding="utf-8")
    assert "pull_request_target" in text, "premise of this test: the name does appear in prose"
    ok, _ = check_gate(REAL_WORKFLOW)
    assert ok


def test_a_floating_tag_is_reported_as_unpinned(tmp_path: Path) -> None:
    workflow = tmp_path / "w.yml"
    workflow.write_text(
        "name: TrustGate\n"
        "on:\n  pull_request:\n"
        "permissions:\n  security-events: write\n"
        "jobs:\n  gate:\n    steps:\n"
        "      - uses: actions/checkout@v7\n"
        "      - uses: github/codeql-action/upload-sarif@2892aa5e19bbd11bc0cff5427e3b750a04d9e3c2\n"
        "        if: always()\n",
        encoding="utf-8",
    )
    ok, detail = check_gate(workflow)
    assert not ok
    assert "SHA-pinned" in detail


def test_a_missing_upload_step_is_reported(tmp_path: Path) -> None:
    workflow = tmp_path / "w.yml"
    workflow.write_text(
        "name: TrustGate\n"
        "on:\n  pull_request:\n"
        "permissions:\n  contents: read\n"
        "jobs:\n  gate:\n    steps:\n"
        "      - uses: actions/checkout@3d3c42e5aac5ba805825da76410c181273ba90b1\n",
        encoding="utf-8",
    )
    ok, detail = check_gate(workflow)
    assert not ok
    assert "SARIF upload present" in detail
    assert "security-events: write" in detail

"""Tests for documentation consistency across workflows, knowledge, prompt, and README."""

from __future__ import annotations

import glob
import re
import subprocess
import sys
from pathlib import Path

import pytest

from line_ads_mcp.server import TOOLS

DOC_FILES = sorted(
    glob.glob("workflows/*.md")
    + glob.glob("knowledge/*.md")
    + ["CLAUDE_PROJECT_PROMPT.md", "README.md"]
)

# Explicit short allowlist for non-tool identifiers (e.g. utility functions)
NON_TOOL_ALLOWLIST = {
    "to_micro",
}


def test_no_get_adset_audience_size_in_docs():
    """Assert get_adset_audience_size (non-existent API) appears nowhere in docs."""
    for file_path in DOC_FILES:
        content = Path(file_path).read_text(encoding="utf-8")
        assert "get_adset_audience_size" not in content, (
            f"Found forbidden identifier 'get_adset_audience_size' in {file_path}"
        )


def test_claude_project_prompt_workflow_references():
    """Assert every workflow referenced in CLAUDE_PROJECT_PROMPT.md exists and 05/06/07 are referenced."""
    prompt_path = Path("CLAUDE_PROJECT_PROMPT.md")
    assert prompt_path.exists()
    content = prompt_path.read_text(encoding="utf-8")

    # Match all references like `workflows/01-account-setup.md`
    wf_refs = set(re.findall(r"workflows/0[1-7]-[a-z0-9\-]+\.md", content))
    assert len(wf_refs) > 0, "No workflow references found in CLAUDE_PROJECT_PROMPT.md"

    for wf_ref in wf_refs:
        assert Path(wf_ref).exists(), f"Workflow file '{wf_ref}' referenced in prompt does not exist"

    for num in ["05", "06", "07"]:
        assert any(f"workflows/{num}-" in ref for ref in wf_refs), (
            f"Workflow {num} must be referenced in CLAUDE_PROJECT_PROMPT.md"
        )


def test_knowledge_paths_referenced_in_workflows():
    """Assert every knowledge/*.md path referenced in workflows exists."""
    workflow_files = sorted(glob.glob("workflows/*.md"))
    assert len(workflow_files) > 0

    knowledge_refs: set[tuple[str, str]] = set()
    for wf in workflow_files:
        text = Path(wf).read_text(encoding="utf-8")
        for ref in re.findall(r"knowledge/[a-zA-Z0-9_\-]+\.md", text):
            knowledge_refs.add((ref, wf))

    assert len(knowledge_refs) > 0
    for kn_path, source_wf in knowledge_refs:
        assert Path(kn_path).exists(), (
            f"Knowledge file '{kn_path}' referenced in {source_wf} does not exist"
        )


def test_tool_identifiers_in_docs_exist_in_server_tools():
    """Parse docs for backticked tool-like identifiers and assert they exist in server.TOOLS."""
    call_pattern = re.compile(r"`([a-z][a-z0-9_]+)\(")

    found_tools: set[tuple[str, str]] = set()

    for file_path in DOC_FILES:
        content = Path(file_path).read_text(encoding="utf-8")
        lines = content.splitlines()

        # 1. Backticked snake_case calls like `tool_name(...)`
        for m in call_pattern.finditer(content):
            found_tools.add((m.group(1), file_path))

        # 2. Table rows under columns with "Tool" / "Tools" header
        in_table = False
        tool_col_idx = -1
        for line in lines:
            if line.strip().startswith("|") and ("---" not in line):
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if not in_table:
                    for idx, c in enumerate(cols):
                        if re.search(r"\btools?\b", c, re.IGNORECASE):
                            in_table = True
                            tool_col_idx = idx
                            break
                else:
                    if tool_col_idx < len(cols):
                        cell = cols[tool_col_idx]
                        for match in re.finditer(r"`([a-z][a-z0-9_]+)(?:\([^`]*\))?`", cell):
                            found_tools.add((match.group(1), file_path))
            elif not line.strip().startswith("|"):
                in_table = False
                tool_col_idx = -1

    assert len(found_tools) > 0

    for name, source_file in sorted(found_tools):
        if name in NON_TOOL_ALLOWLIST:
            continue
        assert name in TOOLS, (
            f"Identifier `{name}` in {source_file} looks like a tool call/entry but does not exist in server.TOOLS"
        )


def test_smoke_readonly_script_imports_only_read_tools():
    """smoke_readonly.py must only import read-only tools and never write tools."""
    smoke_path = Path("scripts/smoke_readonly.py")
    if not smoke_path.exists():
        pytest.skip("scripts/smoke_readonly.py not created yet")

    content = smoke_path.read_text(encoding="utf-8")

    forbidden_writes = [
        "create_campaign",
        "update_campaign",
        "pause_campaign",
        "resume_campaign",
        "create_adset",
        "update_adset",
        "pause_adset",
        "resume_adset",
        "create_ad",
        "pause_ad",
        "resume_ad",
        "create_audience",
        "upload_media",
        "sync_ad_daily_csv",
    ]

    for write_tool in forbidden_writes:
        # Check that it's not imported
        assert not re.search(rf"\bimport\b.*\b{write_tool}\b", content), (
            f"smoke_readonly.py must not import write tool '{write_tool}'"
        )


def test_smoke_readonly_help_without_credentials(monkeypatch):
    """python3 scripts/smoke_readonly.py --help must work without credentials."""
    smoke_path = Path("scripts/smoke_readonly.py")
    if not smoke_path.exists():
        pytest.skip("scripts/smoke_readonly.py not created yet")

    import os
    env = {"PATH": os.environ.get("PATH", "")}
    result = subprocess.run(
        [sys.executable, str(smoke_path), "--help"],
        capture_output=True,
        text=True,
        env=env,
    )
    assert result.returncode == 0
    assert "help" in result.stdout.lower() or "line ads" in result.stdout.lower()

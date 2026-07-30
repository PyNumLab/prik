from __future__ import annotations

from pathlib import Path

from tools.check_radon_policy import (
    ChangedPythonFile,
    ComplexityBlock,
    ZERO_SHA,
    block_changed,
    check_policy,
    changed_block_violates_policy,
    complexity_blocks_for_file,
    is_under_source_roots,
    main,
    parse_changed_python_files,
    resolve_base_ref,
)


def _branchy_function(branches: int) -> str:
    lines = ["def branchy(value):"]
    for index in range(branches):
        lines.append(f"    if value == {index}:")
        lines.append(f"        return {index}")
    lines.append("    return -1")
    return "\n".join(lines)


def test_complexity_blocks_include_span_and_complexity(tmp_path: Path):
    module = tmp_path / "branchy.py"
    module.write_text(_branchy_function(21), encoding="utf-8")

    block = complexity_blocks_for_file(module)[0]

    assert block.name == "branchy"
    assert block.lineno == 1
    assert block.endline == 44
    assert block.complexity == 22
    assert block_changed(block, {2})
    assert not block_changed(block, {45})


def test_policy_tracks_hotspot_average_without_changed_base(tmp_path: Path):
    module = tmp_path / "branchy.py"
    module.write_text(_branchy_function(11), encoding="utf-8")

    result = check_policy(
        source_paths=(tmp_path,),
        base_ref=None,
        head_ref="HEAD",
        max_changed_complexity=20,
        hotspot_min_complexity=11,
    )

    assert result.hotspot_count == 1
    assert result.hotspot_average == 12
    assert result.changed_blocks_checked == 0
    assert result.changed_violations == ()


def test_source_root_filter_uses_path_boundaries():
    assert is_under_source_roots("x2py/parsers/c/parser.py", ("x2py",))
    assert is_under_source_roots("x2py", ("x2py",))
    assert not is_under_source_roots("x2py_extra/parser.py", ("x2py",))


def test_changed_python_files_preserve_pre_rename_paths():
    output = "R098\told/parser.py\tx2py/parser.py\nM\tx2py/cli.py\nA\tx2py/new.py\n"

    assert parse_changed_python_files(output) == [
        ChangedPythonFile("x2py/parser.py", "old/parser.py"),
        ChangedPythonFile("x2py/cli.py", "x2py/cli.py"),
        ChangedPythonFile("x2py/new.py", None),
    ]


def test_changed_block_policy_allows_existing_hotspots_unless_worsened():
    block = ComplexityBlock(Path("pkg/mod.py"), "function", "legacy", 1, 10, 25)

    assert not changed_block_violates_policy(block, base_complexity=25, max_changed_complexity=20)
    assert changed_block_violates_policy(block, base_complexity=24, max_changed_complexity=20)
    assert changed_block_violates_policy(block, base_complexity=None, max_changed_complexity=20)
    assert not changed_block_violates_policy(
        ComplexityBlock(Path("pkg/mod.py"), "function", "small", 1, 10, 20),
        base_complexity=None,
        max_changed_complexity=20,
    )


def test_resolve_base_ref_auto_ignores_empty_and_zero_values(monkeypatch):
    monkeypatch.delenv("PR_BASE_SHA", raising=False)
    monkeypatch.setenv("PUSH_BEFORE_SHA", ZERO_SHA)
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)

    assert resolve_base_ref("auto") is None


def test_main_rejects_auto_without_a_usable_base(monkeypatch, capsys):
    monkeypatch.delenv("PR_BASE_SHA", raising=False)
    monkeypatch.setenv("PUSH_BEFORE_SHA", ZERO_SHA)
    monkeypatch.delenv("GITHUB_BASE_SHA", raising=False)

    assert main(["--base-ref", "auto"]) == 2
    assert "could not resolve --base-ref auto" in capsys.readouterr().err


def test_resolve_base_ref_auto_prefers_pull_request_base(monkeypatch):
    monkeypatch.setenv("PR_BASE_SHA", "abc123")
    monkeypatch.setenv("PUSH_BEFORE_SHA", "def456")

    assert resolve_base_ref("auto") == "abc123"

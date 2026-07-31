"""Tests split by stable ownership concept from `test_cli.py`."""

from tests.fortran.source_preprocessing.preprocessing._support import (
    Path,
    PreprocessingConfig,
    expand_native_fortran_includes,
    preprocessing,
)


def test_linemarker_included_files_fortran_metadata_and_duplicate_entries(tmp_path: Path):
    root = tmp_path / "root.F90"
    source = "\n".join(
        [
            f'# 1 "{root}"',
            '# 1 "decls.inc" 1',
            "integer :: from_include",
            '# 1 "decls.inc" 1',
            '# 2 "unknown.inc" 2',
        ]
    )

    files = preprocessing._included_files_from_linemarkers(
        source,
        root_path=root,
        language="fortran",
        config=PreprocessingConfig(),
    )

    assert [item.to_dict() for item in files] == [
        {
            "path": str(root),
            "included_by": None,
            "include_line": None,
            "mechanism": "cpp_include",
            "dependency_kind": "root",
            "exposure": "public",
        },
        {
            "path": "decls.inc",
            "included_by": str(root),
            "include_line": 1,
            "mechanism": "cpp_include",
            "dependency_kind": "project",
            "exposure": "public",
        },
    ]


def test_linemarker_nested_returns_restore_parent_stack(tmp_path: Path):
    root = tmp_path / "root.F90"
    source = "\n".join(
        [
            f'# 1 "{root}"',
            '# 1 "one.inc" 1',
            '# 1 "two.inc" 1',
            '# 4 "one.inc" 2',
            '# 1 "sibling.inc" 1',
            "integer :: sibling_value",
        ]
    )

    mappings = preprocessing.parse_linemarker_mappings(source, filename=str(root))
    files = preprocessing._included_files_from_linemarkers(
        source,
        root_path=root,
        language="fortran",
        config=PreprocessingConfig(),
    )

    assert mappings == [
        preprocessing.SourceMapping(
            generated_line=6,
            original_path="sibling.inc",
            original_line=1,
            include_stack=[str(root), "one.inc", "sibling.inc"],
        )
    ]
    assert [(item.path, item.included_by) for item in files] == [
        (str(root), None),
        ("one.inc", str(root)),
        ("two.inc", "one.inc"),
        ("sibling.inc", "one.inc"),
    ]
    assert preprocessing._included_files_from_linemarkers(
        f'# 1 "{root}" 1',
        root_path=root,
        language="fortran",
        config=PreprocessingConfig(),
    ) == [
        preprocessing.IncludedFile(
            path=str(root),
            included_by=None,
            include_line=None,
            mechanism="cpp_include",
            dependency_kind="root",
            exposure="public",
        )
    ]
    direct_include = preprocessing._included_files_from_linemarkers(
        '# 1 "direct.inc" 1',
        root_path=root,
        language="fortran",
        config=PreprocessingConfig(),
    )[1]
    assert direct_include.included_by == str(root)
    assert direct_include.include_line == 1


def test_native_fortran_include_expansion_is_recursive_and_preserves_duplicates(tmp_path: Path):
    root = tmp_path / "src" / "root.F90"
    include = root.parent / "decls.inc"
    nested = root.parent / "nested.inc"
    root.parent.mkdir()
    root.write_text('module m\ninclude "decls.inc"\ninclude "decls.inc"\nend module m\n', encoding="utf-8")
    include.write_text('include "nested.inc"\ninteger :: from_decls\n', encoding="utf-8")
    nested.write_text("real :: from_nested\n", encoding="utf-8")

    expanded, included_files, mappings, diagnostics = expand_native_fortran_includes(
        root.read_text(encoding="utf-8"),
        root_path=root,
        include_dirs=[],
    )

    assert diagnostics == []
    root_abs = str(root.resolve())
    include_abs = str(include.resolve())
    nested_abs = str(nested.resolve())
    assert expanded == "\n".join(
        [
            "module m",
            f'# 1 "{include_abs}" 1',
            f'# 1 "{nested_abs}" 1',
            "real :: from_nested",
            f'# 2 "{include_abs}" 2',
            "integer :: from_decls",
            f'# 3 "{root_abs}" 2',
            f'# 1 "{include_abs}" 1',
            f'# 1 "{nested_abs}" 1',
            "real :: from_nested",
            f'# 2 "{include_abs}" 2',
            "integer :: from_decls",
            f'# 4 "{root_abs}" 2',
            "end module m",
            "",
        ]
    )
    assert [item.to_dict() for item in included_files] == [
        {
            "path": include_abs,
            "included_by": root_abs,
            "include_line": 2,
            "mechanism": "fortran_include",
            "dependency_kind": "project",
            "exposure": "public",
        },
        {
            "path": nested_abs,
            "included_by": include_abs,
            "include_line": 1,
            "mechanism": "fortran_include",
            "dependency_kind": "project",
            "exposure": "public",
        },
        {
            "path": include_abs,
            "included_by": root_abs,
            "include_line": 3,
            "mechanism": "fortran_include",
            "dependency_kind": "project",
            "exposure": "public",
        },
        {
            "path": nested_abs,
            "included_by": include_abs,
            "include_line": 1,
            "mechanism": "fortran_include",
            "dependency_kind": "project",
            "exposure": "public",
        },
    ]
    assert [
        (mapping.generated_line, mapping.original_path, mapping.original_line, mapping.include_stack)
        for mapping in mappings
    ] == [
        (1, root_abs, 1, [root_abs]),
        (2, root_abs, 2, [root_abs]),
        (3, include_abs, 1, [include_abs]),
        (4, nested_abs, 1, [nested_abs]),
        (5, include_abs, 1, [include_abs]),
        (6, include_abs, 2, [include_abs]),
        (7, root_abs, 2, [root_abs]),
        (8, root_abs, 3, [root_abs]),
        (9, include_abs, 1, [include_abs]),
        (10, nested_abs, 1, [nested_abs]),
        (11, include_abs, 1, [include_abs]),
        (12, include_abs, 2, [include_abs]),
        (13, root_abs, 3, [root_abs]),
        (14, root_abs, 4, [root_abs]),
    ]


def test_native_fortran_include_lookup_order_missing_and_cycle_diagnostics(tmp_path: Path):
    root = tmp_path / "src" / "root.F90"
    include_dir = tmp_path / "include"
    root.parent.mkdir()
    include_dir.mkdir()
    root.write_text('include "shared.inc"\n', encoding="utf-8")
    (root.parent / "shared.inc").write_text("integer :: relative_wins\n", encoding="utf-8")
    (include_dir / "shared.inc").write_text("integer :: include_dir_loses\n", encoding="utf-8")

    expanded, _included_files, _mappings, diagnostics = expand_native_fortran_includes(
        root.read_text(encoding="utf-8"),
        root_path=root,
        include_dirs=[str(include_dir)],
    )

    assert diagnostics == []
    assert "relative_wins" in expanded
    assert "include_dir_loses" not in expanded

    missing_source = 'include "absent.inc"\n'
    _expanded, _included_files, _mappings, diagnostics = expand_native_fortran_includes(
        missing_source,
        root_path=root,
        include_dirs=[str(include_dir)],
    )
    assert [diagnostic.to_dict() for diagnostic in diagnostics] == [
        {
            "category": "INCLUDE_NOT_FOUND",
            "message": 'Fortran INCLUDE file "absent.inc" was not found',
            "severity": "error",
            "path": str(root.resolve()),
            "line": 1,
            "command": [],
        }
    ]

    cycle_a = root.parent / "a.inc"
    cycle_b = root.parent / "b.inc"
    cycle_a.write_text('include "b.inc"\n', encoding="utf-8")
    cycle_b.write_text('include "a.inc"\n', encoding="utf-8")
    _expanded, _included_files, _mappings, diagnostics = expand_native_fortran_includes(
        'include "a.inc"\n',
        root_path=root,
        include_dirs=[],
    )
    assert [diagnostic.to_dict() for diagnostic in diagnostics] == [
        {
            "category": "INCLUDE_CYCLE",
            "message": (
                f"Fortran INCLUDE cycle detected: {root.resolve()} -> {cycle_a.resolve()} -> "
                f"{cycle_b.resolve()} -> {cycle_a.resolve()}"
            ),
            "severity": "error",
            "path": str(cycle_b.resolve()),
            "line": 1,
            "command": [],
        }
    ]


def test_native_fortran_include_reports_files_that_disappear_before_read(monkeypatch, tmp_path: Path):
    root = tmp_path / "root.F90"
    include = tmp_path / "vanished.inc"
    root.write_text('include "vanished.inc"\n', encoding="utf-8")
    include.write_text("integer :: vanished\n", encoding="utf-8")
    original_read_text = Path.read_text

    seen_encodings = []

    def fail_for_include(path: Path, *args, **kwargs):
        if path == include:
            seen_encodings.append(kwargs["encoding"])
            raise OSError("disappeared")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_for_include)

    expanded, included_files, _mappings, diagnostics = expand_native_fortran_includes(
        root.read_text(encoding="utf-8"),
        root_path=root,
        include_dirs=[],
    )

    assert expanded.startswith(f'# 1 "{include}" 1')
    assert [Path(item.path) for item in included_files] == [include]
    assert seen_encodings == ["utf-8"]
    assert [diagnostic.to_dict() for diagnostic in diagnostics] == [
        {
            "category": "INCLUDE_NOT_FOUND",
            "message": 'Fortran INCLUDE file "vanished.inc" could not be read: disappeared',
            "severity": "error",
            "path": str(root.resolve()),
            "line": 1,
            "command": [],
        }
    ]


def test_native_fortran_include_resolution_continues_after_oserror(monkeypatch, tmp_path: Path):
    root = tmp_path / "src" / "root.F90"
    include_dir = tmp_path / "include"
    root.parent.mkdir()
    include_dir.mkdir()
    include = include_dir / "decls.inc"
    include.write_text("integer :: from_include_dir\n", encoding="utf-8")
    first_candidate = root.parent / "decls.inc"
    original_is_file = Path.is_file

    def fail_first_candidate(path: Path):
        if path == first_candidate:
            raise OSError("lookup failed")
        return original_is_file(path)

    monkeypatch.setattr(Path, "is_file", fail_first_candidate)

    expanded, included_files, _mappings, diagnostics = expand_native_fortran_includes(
        'include "decls.inc"\n',
        root_path=root,
        include_dirs=[str(include_dir)],
    )

    assert diagnostics == []
    assert "from_include_dir" in expanded
    assert [Path(item.path) for item in included_files] == [include]


def test_native_fortran_include_uses_absolute_fallback_when_resolve_fails(monkeypatch, tmp_path: Path):
    root = tmp_path / "root.F90"
    include = tmp_path / "decls.inc"
    include.write_text("integer :: value\n", encoding="utf-8")
    original_resolve = Path.resolve

    def fail_include_resolve(path: Path):
        if path == include:
            raise OSError("cannot resolve include")
        return original_resolve(path)

    monkeypatch.setattr(Path, "resolve", fail_include_resolve)

    expanded, included_files, _mappings, diagnostics = expand_native_fortran_includes(
        'include "decls.inc"\n',
        root_path=root,
        include_dirs=[],
    )

    assert diagnostics == []
    assert f'# 1 "{include.absolute()}" 1' in expanded
    assert [item.path for item in included_files] == [str(include.absolute())]


def test_native_fortran_include_diagnostics_do_not_drop_following_lines(monkeypatch, tmp_path: Path):
    root = tmp_path / "root.F90"
    cycle = tmp_path / "cycle.inc"
    vanished = tmp_path / "vanished.inc"
    cycle.write_text('include "cycle.inc"\ninteger :: after_cycle\n', encoding="utf-8")
    vanished.write_text("integer :: vanished\n", encoding="utf-8")
    original_read_text = Path.read_text

    def fail_for_vanished(path: Path, *args, **kwargs):
        if path == vanished:
            raise OSError("disappeared")
        return original_read_text(path, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", fail_for_vanished)

    expanded, _included_files, _mappings, diagnostics = expand_native_fortran_includes(
        'include "cycle.inc"\ninclude "vanished.inc"\ninteger :: after_read_error\n',
        root_path=root,
        include_dirs=[],
    )

    assert "after_cycle" in expanded
    assert "after_read_error" in expanded
    assert [diagnostic.category for diagnostic in diagnostics] == ["INCLUDE_CYCLE", "INCLUDE_NOT_FOUND"]


def test_native_fortran_include_expansion_preserves_input_linemarkers_and_private_exposure(tmp_path: Path):
    root = tmp_path / "root.F90"
    include = tmp_path / "private.inc"
    include.write_text("integer :: from_include\n", encoding="utf-8")
    source = f'# 40 "{root}"\ninclude "private.inc"'

    expanded, included_files, mappings, diagnostics = expand_native_fortran_includes(
        source,
        root_path=root,
        include_dirs=[],
        config=PreprocessingConfig(private_includes=["private"]),
    )

    assert diagnostics == []
    assert expanded == "\n".join(
        [
            f'# 40 "{root}"',
            f'# 1 "{include}" 1',
            "integer :: from_include",
            f'# 41 "{root}" 2',
        ]
    )
    assert [item.to_dict() for item in included_files] == [
        {
            "path": str(include),
            "included_by": str(root),
            "include_line": 40,
            "mechanism": "fortran_include",
            "dependency_kind": "project",
            "exposure": "private",
        }
    ]
    assert [(mapping.generated_line, mapping.original_path, mapping.original_line) for mapping in mappings] == [
        (1, str(root), 1),
        (2, str(root), 40),
        (3, str(include), 1),
        (4, str(root), 40),
    ]

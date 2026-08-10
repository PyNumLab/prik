"""Documentation lane and navigation contracts."""

from pathlib import Path

import pytest

from tests.docs._structure_support import (
    ALLOWED_CONTEXTUAL_FORWARD_LINK_PREFIXES,
    ALLOWED_CONTEXTUAL_FORWARD_LINK_SOURCE_PREFIXES,
    DOCS_ROOT,
    DOCUMENTATION_CHECKLIST_PATH,
    EXAMPLE_DOCUMENTATION_PAGES,
    LEARNING_DOCUMENTATION_PATHS,
    MARKDOWN_LINK,
    REAL_LIBRARY_EXAMPLE_PAGES,
    REQUIRED_AREA_INDEXES,
    REQUIRED_GETTING_STARTED_PAGES,
    REQUIRED_REFERENCE_PAGES,
    REQUIRED_ROADMAP_PAGES,
    REQUIRED_USER_GUIDE_PAGES,
    ROOT,
    _front_matter,
    _instructional_body_without_next,
    _next_navigation_items,
    _site_navigation_positions,
    _user_guide_index_order,
    _visible_documentation_source,
)


def test_readme_follows_one_points_workflow_from_build_through_contract_rebuild() -> None:
    readme = _visible_documentation_source(ROOT / "README.md")
    quick_start = readme.split("## Installation & Quick Start", maxsplit=1)[1].split(
        "## How it works",
        maxsplit=1,
    )[0]
    installation_index = quick_start.index("python3 -m pip install prik")
    version_index = quick_start.index("prik --version", installation_index)
    help_index = quick_start.index("python3 -m prik --help")
    source_build_command_index = quick_start.index(
        "python3 -m prik points.f90 --out geometry",
        help_index,
    )
    source_build_tree_index = quick_start.index(
        ".\n  points.f90\n  geometry.so\n  __prik__/",
        source_build_command_index,
    )
    explicit_source_build_command_index = quick_start.index(
        "python3 -m prik points.f90 \\\n  --out geometry \\\n  --out-dir build/geometry",
        source_build_tree_index,
    )
    explicit_source_build_tree_index = quick_start.index(
        "build/geometry/\n    geometry.<extension-suffix>.so",
        explicit_source_build_command_index,
    )
    pyi_generation_command_index = quick_start.index(
        "python3 -m prik generate --pyi points.f90 --out contracts",
        explicit_source_build_tree_index,
    )
    pyi_contract_tree_index = quick_start.index(
        "contracts/\n  __init__.pyi\n  points.pyi",
        pyi_generation_command_index,
    )
    pyi_contract_body_index = quick_start.index(
        "class point:\n"
        "    def __init__(\n"
        "        self,\n"
        "        *,\n"
        "        x: Float64 = 0.0,\n"
        "        y: Float64 = 0.0",
        pyi_contract_tree_index,
    )
    move_contract_index = quick_start.index(
        "@native_call([Arg(0), Addr(Arg(1)), Addr(Arg(2))])\ndef move(",
        pyi_contract_body_index,
    )
    norm_contract_index = quick_start.index("def norm_squared(", move_contract_index)
    pyi_build_command_index = quick_start.index(
        "python3 -m prik contracts/__init__.pyi",
        norm_contract_index,
    )
    native_source_argument_index = quick_start.index("--native-fortran-sources points.f90", pyi_build_command_index)
    output_name_index = quick_start.index("--out geometry", native_source_argument_index)
    pyi_build_tree_index = quick_start.index("build/geometry_from_pyi/", output_name_index)
    import_index = quick_start.index("import geometry.points as points", pyi_build_tree_index)
    constructor_index = quick_start.index("item = points.point(", import_index)
    mutation_index = quick_start.index("points.move(item", constructor_index)
    runtime_output_index = quick_start.index("# 20.0", mutation_index)
    verbose_command_index = quick_start.index(
        "python3 -m prik points.f90 \\\n  --out geometry_debug",
        runtime_output_index,
    )
    verbose_fortran_flag_index = quick_start.index("--wrapper-fortran-flags=-O2", verbose_command_index)
    verbose_c_flag_index = quick_start.index("--wrapper-c-flags=-O2", verbose_fortran_flag_index)
    verbose_output_index = quick_start.index("generated Python binding", verbose_c_flag_index)

    assert installation_index < version_index < help_index < source_build_command_index
    assert source_build_command_index < source_build_tree_index < explicit_source_build_command_index
    assert explicit_source_build_command_index < explicit_source_build_tree_index < pyi_generation_command_index
    assert pyi_generation_command_index < pyi_contract_tree_index < pyi_contract_body_index
    assert pyi_contract_body_index < move_contract_index < norm_contract_index < pyi_build_command_index
    assert pyi_build_command_index < native_source_argument_index < output_name_index < pyi_build_tree_index
    assert pyi_build_tree_index < import_index < constructor_index < mutation_index < runtime_output_index
    assert runtime_output_index < verbose_command_index
    assert verbose_command_index < verbose_fortran_flag_index < verbose_c_flag_index < verbose_output_index
    assert "--parse" not in readme
    assert "--semantics" not in readme
    assert "scale.f90" not in readme
    assert "SCALE" not in readme
    assert "python3 -m prik solver.f90" not in quick_start
    assert "fruntime_abi_f90" not in readme
    assert "solver.f90" not in readme
    assert "add1" not in readme
    assert "distance2" not in readme
    assert "point_api" not in readme
    assert "build/points" not in readme
    assert "tests/data/fortran/general/basic_subroutine.f90" not in readme
    assert "contracts/basic_subroutine/basic_subroutine.pyi" not in readme


def test_installation_separates_pypi_users_from_editable_contributors() -> None:
    installation = _visible_documentation_source(DOCS_ROOT / "user/getting-started/installation.md")
    user_section = installation.split("## User Installation", maxsplit=1)[1].split(
        "## Contributor Installation",
        maxsplit=1,
    )[0]
    contributor_section = installation.split("## Contributor Installation", maxsplit=1)[1].split(
        "## Platform Support",
        maxsplit=1,
    )[0]

    assert "python3 -m pip install prik" in user_section
    assert "pip install -e" not in user_section
    assert "git clone https://github.com/PyNumLab/prik.git" in contributor_section
    assert 'python3 -m pip install -e ".[qa]"' in contributor_section


@pytest.mark.parametrize("relative_path", REQUIRED_AREA_INDEXES)
def test_required_documentation_area_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


def test_documentation_root_uses_three_audience_lanes() -> None:
    directories = {path.name for path in DOCS_ROOT.iterdir() if path.is_dir()}
    root_pages = {path.name for path in DOCS_ROOT.glob("*.md")}
    assert directories == {
        "user",
        "developer",
        "maintainer",
        "javascripts",
        "stylesheets",
        "old_docs",
    }
    assert root_pages == {"index.md"}


@pytest.mark.parametrize(
    ("lane", "audience_terms"),
    [
        ("user", ("users",)),
        ("developer", ("developers", "contributors")),
        ("maintainer", ("maintainers",)),
    ],
)
def test_documentation_lane_has_consistent_audience(lane: str, audience_terms: tuple[str, ...]) -> None:
    for path in (DOCS_ROOT / lane).rglob("*.md"):
        metadata, _ = _front_matter(path)
        assert any(term in metadata["audience"] for term in audience_terms)
        if lane != "maintainer":
            assert "maintainers" not in metadata["audience"]
        else:
            assert metadata["audience"] == "maintainers"


@pytest.mark.parametrize("path", LEARNING_DOCUMENTATION_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_website_documentation_does_not_link_to_maintainer_lane(path: Path) -> None:
    maintainer_root = (DOCS_ROOT / "maintainer").resolve()
    for target in MARKDOWN_LINK.findall(_visible_documentation_source(path)):
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        resolved = (path.parent / target).resolve()
        assert not resolved.is_relative_to(maintainer_root), (
            f"{path.relative_to(ROOT)}: website link enters maintainer lane: {target}"
        )


def test_readme_documentation_links_follow_site_navigation_order() -> None:
    readme = _visible_documentation_source(ROOT / "README.md")
    documentation = readme.split("## Documentation", maxsplit=1)[1].split(
        "## Development",
        maxsplit=1,
    )[0]
    positions = _site_navigation_positions()
    linked_positions = [
        positions[target.removeprefix("docs/")]
        for target in MARKDOWN_LINK.findall(documentation)
        if target.startswith("docs/")
    ]
    assert linked_positions == sorted(linked_positions)


@pytest.mark.parametrize("relative_path", REQUIRED_REFERENCE_PAGES)
def test_required_reference_page_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


@pytest.mark.parametrize("relative_path", REQUIRED_REFERENCE_PAGES)
def test_reference_page_is_in_site_navigation(relative_path: str) -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert relative_path in site_configuration


@pytest.mark.parametrize("relative_path", REQUIRED_ROADMAP_PAGES)
def test_required_roadmap_page_exists(relative_path: str) -> None:
    assert (DOCS_ROOT / relative_path).is_file()


def test_site_navigation_includes_all_publishable_lanes_and_excludes_archive() -> None:
    site_configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    assert "old_docs/**" in site_configuration
    positions = _site_navigation_positions()
    assert "user/index.md" in positions
    assert "developer/index.md" in positions
    assert "maintainer/README.md" in positions


def test_user_guide_navigation_follows_index_reading_order() -> None:
    positions = _site_navigation_positions()
    navigation_order = [
        path
        for path, _ in sorted(positions.items(), key=lambda item: item[1])
        if path.startswith("user/guide/") and path != "user/guide/index.md"
    ]

    assert navigation_order == _user_guide_index_order()


@pytest.mark.parametrize("relative_path", REQUIRED_GETTING_STARTED_PAGES)
def test_required_getting_started_page_is_maintained_and_navigable(relative_path: str) -> None:
    path = DOCS_ROOT / relative_path
    assert path.is_file()
    metadata, body = _front_matter(path)
    assert metadata["status"] == "maintained"
    assert relative_path in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        assert (path.parent / target).resolve().exists(), f"{relative_path}: missing link target {target}"


@pytest.mark.parametrize("relative_path", REQUIRED_GETTING_STARTED_PAGES)
def test_getting_started_page_is_completed_in_documentation_checklist(relative_path: str) -> None:
    checklist = DOCUMENTATION_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert f"- [x] `docs/{relative_path}`" in checklist


@pytest.mark.parametrize("relative_path", REQUIRED_USER_GUIDE_PAGES)
def test_required_user_guide_page_is_maintained_and_navigable(relative_path: str) -> None:
    path = DOCS_ROOT / relative_path
    assert path.is_file()
    metadata, body = _front_matter(path)
    assert metadata["status"] == "maintained"
    assert relative_path in (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    for target in MARKDOWN_LINK.findall(body):
        if target.startswith(("http://", "https://")):
            continue
        assert (path.parent / target).resolve().exists(), f"{relative_path}: missing link target {target}"


@pytest.mark.parametrize("relative_path", REQUIRED_USER_GUIDE_PAGES)
def test_user_guide_page_is_completed_in_documentation_checklist(relative_path: str) -> None:
    checklist = DOCUMENTATION_CHECKLIST_PATH.read_text(encoding="utf-8")
    assert f"- [x] `docs/{relative_path}`" in checklist


@pytest.mark.parametrize(
    "relative_path",
    [*REQUIRED_GETTING_STARTED_PAGES[1:], *REQUIRED_USER_GUIDE_PAGES[1:], *EXAMPLE_DOCUMENTATION_PAGES],
)
def test_sequential_user_pages_do_not_link_forward_from_instructional_prose(relative_path: str) -> None:
    path = DOCS_ROOT / relative_path
    _, body = _front_matter(path)
    body = _instructional_body_without_next(body)
    positions = _site_navigation_positions()
    if relative_path not in positions:
        pytest.skip(f"{relative_path}: not active in site navigation")
    source_position = positions[relative_path]
    for target in MARKDOWN_LINK.findall(body):
        target_path = (path.parent / target).resolve()
        if not target_path.is_relative_to(DOCS_ROOT):
            continue
        target_relative = target_path.relative_to(DOCS_ROOT).as_posix()
        if target_relative not in positions:
            continue
        if relative_path.startswith(ALLOWED_CONTEXTUAL_FORWARD_LINK_SOURCE_PREFIXES) and target_relative.startswith(
            ALLOWED_CONTEXTUAL_FORWARD_LINK_PREFIXES
        ):
            continue
        assert positions[target_relative] <= source_position, f"{relative_path}: forward link to {target_relative}"


@pytest.mark.parametrize(
    "relative_path",
    [*REQUIRED_GETTING_STARTED_PAGES[1:], *REQUIRED_USER_GUIDE_PAGES[1:]],
)
def test_next_sections_use_linked_bullet_destinations(relative_path: str) -> None:
    _, body = _front_matter(DOCS_ROOT / relative_path)
    for line_number, item, is_bullet in _next_navigation_items(body):
        assert is_bullet, f"{relative_path}:{line_number}: Next content must be a bullet item"
        assert MARKDOWN_LINK.search(item), f"{relative_path}:{line_number}: Next item must include a Markdown link"


@pytest.mark.parametrize("relative_path", REQUIRED_USER_GUIDE_PAGES)
def test_user_guide_commands_do_not_expose_fixture_paths(relative_path: str) -> None:
    page = (DOCS_ROOT / relative_path).read_text(encoding="utf-8")
    assert "python3 -m prik tests/" not in page


@pytest.mark.parametrize(
    "relative_path",
    [
        "index.md",
        "user/index.md",
        *REQUIRED_GETTING_STARTED_PAGES,
        *REQUIRED_USER_GUIDE_PAGES,
    ],
)
def test_reviewed_user_pages_do_not_expose_internal_evidence(relative_path: str) -> None:
    page = _visible_documentation_source(DOCS_ROOT / relative_path)
    assert "## Evidence" not in page
    assert "## Runtime Evidence" not in page
    assert "Runtime tests:" not in page
    assert "../../../tests/" not in page
    assert "../../tests/" not in page
    assert "../tests/" not in page


@pytest.mark.parametrize(
    "relative_path",
    [
        "index.md",
        "user/index.md",
        *REQUIRED_GETTING_STARTED_PAGES,
        *REQUIRED_USER_GUIDE_PAGES,
    ],
)
def test_reviewed_user_pages_do_not_contain_editorial_notes(relative_path: str) -> None:
    page = _visible_documentation_source(DOCS_ROOT / relative_path).casefold()
    for phrase in (
        "i kept your",
        "let me know if you want",
        "original content had",
        "restore/polish",
    ):
        assert phrase not in page


@pytest.mark.parametrize("relative_path", REAL_LIBRARY_EXAMPLE_PAGES)
def test_real_library_examples_share_a_user_facing_structure(relative_path: str) -> None:
    page = _visible_documentation_source(DOCS_ROOT / relative_path)
    common_sections = [
        "### What this example shows",
        "## Versions used",
        "## 1. Prepare the repository and toolchain",
        "## 4. Run the complete test suite",
        "## 5. See how results are validated",
        "## 6. Run focused examples",
        "## Troubleshooting",
        "## Source provenance",
    ]

    positions = [page.index(section) for section in common_sections]
    assert positions == sorted(positions)
    for internal_phrase in (
        "stopping after a successful import",
        "fail-closed",
        "authoritative public classification",
        "complete maintained suite",
        "machine constants",
    ):
        assert internal_phrase not in page

"""User-facing documentation journey and content contracts."""

import re

from tests.docs._structure_support import (
    CLI_REFERENCE_PATH,
    DOCS_ROOT,
    DOC_PATHS,
    MARKDOWN_LINK,
    REQUIRED_GETTING_STARTED_PAGES,
    REQUIRED_USER_GUIDE_PAGES,
    ROOT,
    _front_matter,
    _visible_documentation_source,
)


def test_getting_started_overview_uses_standalone_example() -> None:
    overview = (DOCS_ROOT / "user/getting-started/index.md").read_text(encoding="utf-8")
    introduction_index = overview.index("you will create\n`scale.f90`")
    import_index = overview.index("import scale")
    call_index = overview.index("scale.scale(np.float64(3.0), np.float64(2.5))")

    assert introduction_index < import_index < call_index
    assert "[Your First Function](first-wrapped-function.md)" in overview


def test_documentation_homepage_demonstrates_prik_before_getting_started() -> None:
    page = (DOCS_ROOT / "index.md").read_text(encoding="utf-8")
    introduction_index = page.index("Generate native Python bindings for Fortran")
    example_heading_index = page.index("## From Fortran to Python in one command")
    source_index = page.index("```fortran", example_heading_index)
    build_index = page.index("python3 -m prik scale.f90", source_index)
    import_index = page.index("import scale", build_index)
    call_index = page.index("scale.scale(np.float64(3.0), np.float64(2.5))", import_index)
    result_index = page.index("# 7.5", call_index)
    advantages_index = page.index("## Why PRIK", result_index)
    evidence_index = page.index("## Proven on real Fortran libraries", advantages_index)
    performance_index = page.index("## Measured against NumPy's f2py", evidence_index)
    runtime_chart_index = page.index("user/assets/performance-comparison.svg", performance_index)
    build_chart_index = page.index("user/assets/build-time-comparison.svg", runtime_chart_index)
    methodology_index = page.index("[See the benchmark machine, full results, and methodology →]", build_chart_index)
    install_index = page.index("[Install PRIK →]", methodology_index)
    getting_started_index = page.index("[Read Getting Started →]", install_index)

    assert introduction_index < example_heading_index < source_index < build_index
    assert build_index < import_index < call_index < result_index
    assert result_index < advantages_index < evidence_index < performance_index
    assert performance_index < runtime_chart_index < build_chart_index
    assert build_chart_index < methodology_index < install_index < getting_started_index
    assert "python3 -m pip install prik" in page
    assert "No manual binding code is required." in page
    assert "[BLAS](user/examples/blas-wrapper.md)" in page
    assert "[LAPACK](user/examples/lapack-wrapper.md)" in page
    assert "[FFTPACK](user/examples/fftpack-wrapper.md)" in page
    assert "[MINPACK](user/examples/minpack-wrapper.md)" in page
    assert "The charts show the current published snapshot" in page
    assert "specific to its machine and toolchain" in page
    assert "PRIK was faster in" not in page
    assert page.count("{ .prik-performance-chart }") == 2
    assert page.count("{ .prik-primary-cta }") == 2
    assert "developer/index.md" not in page
    assert "maintainer/README.md" not in page
    assert "user/guide/" not in page


def test_public_entrypoints_use_the_canonical_identity_and_description() -> None:
    homepage = _visible_documentation_source(DOCS_ROOT / "index.md")
    readme = _visible_documentation_source(ROOT / "README.md")
    mkdocs = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    pyproject = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    title = "PRIK — Python Runtime Interop Kit"
    subtitle = "Generate native Python bindings for Fortran, with editable `.pyi` contracts\nand Pythonic APIs."
    description = (
        "PRIK generates native Python bindings from Fortran projects, producing\n"
        "importable extensions and editable `.pyi` contracts for Pythonic APIs."
    )
    language_direction = (
        "**PRIK starts with Fortran-to-Python.** Its semantic contract model is designed\n"
        "to support more native languages over time."
    )
    metadata_description = description.replace("\n", " ").replace("`", "")

    assert readme.startswith(f"# {title}\n\n**{subtitle}**\n\n{description}\n")
    assert f"# {title}\n\n**{subtitle}**\n\n{description}\n" in homepage
    assert language_direction in readme
    assert language_direction in homepage
    assert f"site_name: {title}" in mkdocs
    assert f"site_description: {metadata_description}" in mkdocs
    assert f'description = "{metadata_description}"' in pyproject


def test_faq_routes_search_questions_to_authoritative_pages() -> None:
    metadata, page = _front_matter(DOCS_ROOT / "user/faq/index.md")
    question_targets = [
        (
            "How do I call Fortran from Python?",
            "how-do-i-call-fortran-from-python",
            "../getting-started/first-wrapped-function.md",
        ),
        (
            "How do I generate Python bindings for a Fortran module?",
            "how-do-i-generate-python-bindings-for-a-fortran-module",
            "../getting-started/first-wrapped-module.md",
        ),
        (
            "How do I wrap an existing Fortran library for Python?",
            "how-do-i-wrap-an-existing-fortran-library-for-python",
            "../guide/building-shared-library.md",
        ),
        (
            "How do I expose Fortran derived types as Python classes?",
            "how-do-i-expose-fortran-derived-types-as-python-classes",
            "../guide/wrapping-derived-types.md",
        ),
        (
            "How do I pass NumPy arrays to Fortran without unnecessary copies?",
            "how-do-i-pass-numpy-arrays-to-fortran-without-unnecessary-copies",
            "../guide/arrays.md",
        ),
        ("Should I use PRIK or f2py?", "should-i-use-prik-or-f2py", "../performance.md"),
    ]

    assert metadata["status"] == "maintained"
    assert metadata["publication"] == "reviewed"
    previous_start = -1
    for question, anchor_id, target in question_targets:
        start_marker = f'<details class="prik-faq-item" id="{anchor_id}" markdown="1">'
        start = page.index(start_marker)
        end = page.index("</details>", start)
        answer = page[start:end]
        assert previous_start < start
        assert f"<summary>{question}</summary>" in answer
        assert target in answer
        previous_start = start

    assert page.count('<details class="prik-faq-item"') == len(question_targets)
    assert "## Questions" not in page
    assert "## How do I" not in page
    assert "../examples/blas-wrapper.md" in page
    assert "../examples/fftpack-wrapper.md" in page
    assert "../examples/minpack-wrapper.md" in page
    assert "../reference/pyi-contracts/index.md" in page
    assert "../guide/allocatables.md" in page
    assert "../guide/pointers.md" in page
    assert "../guide/error-handling.md" in page
    assert "../guide/generic-interfaces.md" in page
    assert "PRIK is currently alpha" in " ".join(page.split())


def test_faq_accordion_is_styled_and_opens_direct_links() -> None:
    configuration = (ROOT / "mkdocs.yml").read_text(encoding="utf-8")
    stylesheet = (DOCS_ROOT / "stylesheets/site.css").read_text(encoding="utf-8")
    script = (DOCS_ROOT / "javascripts/faq.js").read_text(encoding="utf-8")

    assert "- md_in_html" in configuration
    assert "- javascripts/faq.js" in configuration
    assert ".prik-faq-item summary" in stylesheet
    assert ".prik-faq-item:target" in stylesheet
    assert 'target.matches("details.prik-faq-item")' in script
    assert "target.open = true" in script
    assert 'window.addEventListener("hashchange", openLinkedQuestion)' in script


def test_performance_page_bounds_the_prik_f2py_decision() -> None:
    page = _visible_documentation_source(DOCS_ROOT / "user/performance.md")
    start = page.index("## Should I use PRIK or f2py?")
    end = page.index("## Fair, Like-for-Like Setup", start)
    comparison = " ".join(page[start:end].split())

    assert "runtime-call overhead and clean build time" in comparison
    assert "They do not rank feature coverage" in comparison
    assert "https://numpy.org/doc/stable/f2py/" in comparison
    assert "https://numpy.org/doc/stable/f2py/signature-file.html" in comparison
    assert "design the Python API, not just generate a wrapper" in comparison
    assert "simpler, more Pythonic place to rename or hide exports, flatten modules" in comparison
    assert "reorder or hide native arguments, and return native outputs as Python results" in comparison
    assert "[NumPy arrays](guide/arrays.md) as complete API contracts" in comparison
    assert "dtype, rank, shape, memory layout, contiguity, strides, mutation, and copy behavior" in comparison
    assert "[supported positive-stride views](guide/arrays.md#strided-views) without copying" in comparison
    assert "[derived types](guide/wrapping-derived-types.md) as Python classes" in comparison
    assert "[allocatables](guide/allocatables.md)" in comparison
    assert "[pointer forms](guide/pointers.md)" in comparison
    assert "native errors as [Python exceptions](guide/error-handling.md)" in comparison
    assert "[overloaded procedures](guide/generic-interfaces.md)" in comparison
    assert "reference/pyi-contracts/index.md" in comparison
    assert "PRIK is currently alpha" in comparison


def test_documentation_links_to_documentation_stay_on_the_website() -> None:
    github_documentation_prefixes = (
        "https://github.com/PyNumLab/prik/blob/main/docs/",
        "https://github.com/PyNumLab/prik/tree/main/docs/",
    )

    for path in DOC_PATHS:
        prose_lines: list[str] = []
        fence: str | None = None
        for line in _visible_documentation_source(path).splitlines():
            marker = re.match(r"^\s*(`{3,}|~{3,})", line)
            if fence is not None:
                if line.strip() == fence:
                    fence = None
                continue
            if marker is not None:
                fence = marker.group(1)
                continue
            prose_lines.append(line)

        for target in MARKDOWN_LINK.findall("\n".join(prose_lines)):
            if "/" not in target and "." not in target:
                continue
            assert not target.startswith(github_documentation_prefixes), (
                f"{path.relative_to(ROOT)}: documentation link points to GitHub: {target}"
            )
            if target.startswith(("http://", "https://", "mailto:")):
                continue
            resolved = (path.parent / target).resolve()
            assert resolved != (ROOT / "README.md").resolve(), (
                f"{path.relative_to(ROOT)}: documentation workflow points to the repository README"
            )
            if resolved.is_relative_to(DOCS_ROOT.resolve()):
                assert resolved.is_file(), (
                    f"{path.relative_to(ROOT)}: documentation link must target a website page or asset: {target}"
                )


def test_first_wrapped_function_shows_contract_and_mentions_later_support_boundaries() -> None:
    page = (DOCS_ROOT / "user/getting-started/first-wrapped-function.md").read_text(encoding="utf-8")
    source_index = page.index("scale.f90")
    build_index = page.index("python3 -m prik scale.f90")
    command_index = page.index("python3 -m prik generate --pyi scale.f90")
    contract_index = page.index(
        "@standalone\n@native_call([Addr(Arg(0)), Addr(Arg(1))])\ndef scale(\n"
        "    value: Float64,\n    factor: Float64\n) -> Float64: ..."
    )
    docstring_index = page.index("## Inspect the Generated Docstring")
    call_index = page.index("## Call the Function")

    assert source_index < command_index < contract_index < build_index
    assert build_index < docstring_index < call_index
    assert "editable description of the\nPython interface" in page
    assert "scale(value, factor) -> float64" in page
    assert "assert result == 7.5" in page
    assert "isinstance(result, float)" not in page
    assert "## Current Limitations" not in page


def test_first_wrapped_module_shows_local_input_and_generated_contract() -> None:
    page = (DOCS_ROOT / "user/getting-started/first-wrapped-module.md").read_text(encoding="utf-8")
    source_index = page.index("module_state.f90")
    build_index = page.index("python3 -m prik module_state.f90")
    docstring_index = page.index("## Inspect the Generated Docstring")
    usage_index = page.index("## Usage Example")
    inspect_index = page.index("python3 -m prik generate --pyi module_state.f90")
    contract_index = page.index("## Key Rules")

    assert source_index < build_index < docstring_index < usage_index < inspect_index < contract_index
    assert "print(mod.__doc__)" in page
    assert "module_state\n\nModule Attributes" in page
    assert "summarize() -> int32" in page
    assert "scaled_counter() -> float64" in page
    assert "next_local() -> int32" in page
    assert "nmax : int32\n    Read-only constant." in page
    assert "counter : int32" in page
    assert "scale : float64" in page
    assert "saved_counter : int32" in page
    assert "Assignment writes through to native storage." not in page
    assert "fmodule_vars_f90" not in page
    assert "## Current Limitations" not in page


def test_beginner_workflow_reuses_scale_example_without_renaming_it() -> None:
    page = (DOCS_ROOT / "user/getting-started/beginner-workflow.md").read_text(encoding="utf-8")
    source_reference_index = page.index("scale.f90")
    layout_index = page.index("src/")
    contract_index = page.index("python3 -m prik generate --pyi src/scale.f90")
    build_index = page.index("python3 -m prik src/scale.f90")
    smoke_index = page.index("result = scale.scale(np.float64(3.0), np.float64(2.5))")
    editing_index = page.index("## 4. Optionally Edit the Contract")
    edited_contract_index = page.index("contracts/scale/__init__.pyi", editing_index)
    diagnosis_index = page.index("## 5. Diagnose a Failure")

    assert source_reference_index < layout_index < contract_index < build_index
    assert build_index < smoke_index < editing_index < edited_contract_index < diagnosis_index
    assert "[First Wrapped Function](first-wrapped-function.md)" in page
    assert "scale_api" not in page


def test_user_guide_teaches_small_contract_edits_in_context() -> None:
    arrays = _visible_documentation_source(DOCS_ROOT / "user/guide/arrays.md")
    strings = _visible_documentation_source(DOCS_ROOT / "user/guide/strings.md")
    functions = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-functions.md")
    modules = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-modules.md")
    generics = _visible_documentation_source(DOCS_ROOT / "user/guide/generic-interfaces.md")
    derived = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-derived-types.md")
    errors = _visible_documentation_source(DOCS_ROOT / "user/guide/error-handling.md")

    assert "Edit the semantic `.pyi` and add `ORDER_C`" in arrays
    assert "Edit the declarations in `contracts/strings/strings_api.pyi`" in strings
    assert '@bind("scale")' in functions
    assert "## Shape the Module API With the Contract" in modules
    assert "nmax: Final[Int32] = 12" in modules
    assert "counter: Int32 = 9" in modules
    assert "scale: Float64 = 2.0" in modules
    assert "saved_counter: private[Int32]" in modules
    assert "It does not turn a writable Fortran variable into a read-only" in modules
    assert "## Flatten Module Namespaces" in modules
    assert "from .module1 import *" in modules
    assert "from .module2 import *" in modules
    assert "library.func1()" in modules
    assert "library.module1` and `library.module2` are no longer exported" in modules
    assert "the wrapper build fails and asks for an explicit" in modules
    assert "## Extend an Overload Set" in generics
    assert '@overload("convert_logical")' in generics
    assert "## Custom Constructor" in derived
    assert '@bind("initialize_point")' in derived
    assert "### Expose a Module Procedure as a Method" in derived
    assert "def move(self, dx: Float64, dy: Float64)" in derived
    assert '@raises(status="status", message="message", success=0)' in errors


def test_array_guide_routes_advanced_shape_expressions_to_reference() -> None:
    guide = _visible_documentation_source(DOCS_ROOT / "user/guide/arrays.md")
    reference = _visible_documentation_source(DOCS_ROOT / "user/reference/pyi-contracts/calls-and-results.md")

    assert "Generated contracts may describe a shape with visible arguments" in guide
    assert "../reference/pyi-contracts/calls-and-results.md#advanced-array-shape-expressions" in guide
    assert "## Advanced Array Shape Expressions" in reference
    assert "Native relationship" in reference
    assert "extent_for(n)" in reference

    assert "The bridge emits the signature as an abstract Fortran interface" not in guide
    assert "A specification function must be pure" not in guide
    assert "compiler-produced `.mod` interfaces" not in guide


def test_user_guide_keeps_generated_docstrings_with_new_overload_and_class_features() -> None:
    modules = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-modules.md")
    generics = _visible_documentation_source(DOCS_ROOT / "user/guide/generic-interfaces.md")
    derived = _visible_documentation_source(DOCS_ROOT / "user/guide/wrapping-derived-types.md")

    assert "## Inspect the Module" not in modules
    assert "print(mod.__doc__)" not in modules

    assert "## Inspect the Overloads" in generics
    assert "print(conversions.__doc__)" in generics
    assert "print(conversions.convert.__doc__)" in generics
    assert "convert(value: int32) -> int32" in generics
    assert "convert(value: float64) -> float64" in generics

    assert "## Inspect the Class" in derived
    assert "print(points.point.__doc__)" in derived
    assert "print(points.point.__init__.__doc__)" in derived
    assert "`points.point.move.__doc__`" in derived
    assert "print(points.point.__add__.__doc__)" in derived
    assert "__add__(right: point) -> point" in derived


def test_getting_started_pages_keep_advanced_stage_flags_out_of_beginner_path() -> None:
    content = "\n".join(
        _visible_documentation_source(DOCS_ROOT / relative_path) for relative_path in REQUIRED_GETTING_STARTED_PAGES
    )

    assert "--parse" not in content
    assert "--semantics" not in content
    assert "--json" not in content


def test_user_guide_shows_direct_shared_library_build() -> None:
    content = "\n".join(
        _visible_documentation_source(DOCS_ROOT / relative_path) for relative_path in REQUIRED_USER_GUIDE_PAGES
    )
    shared_library = _visible_documentation_source(DOCS_ROOT / "user/guide/building-shared-library.md")

    assert "python3 -m prik src/scale.f90 --out-dir build/scale" in content
    assert "[Common Beginner Workflow](../getting-started/beginner-workflow.md)" in shared_library


def test_user_compiler_docs_distinguish_runtime_evidence_from_configured_profiles() -> None:
    installation = _visible_documentation_source(DOCS_ROOT / "user/getting-started/installation.md")
    shared_library = _visible_documentation_source(DOCS_ROOT / "user/guide/building-shared-library.md")

    for compiler_pair in (
        "| `gfortran` | `gcc` | Default; tested on Linux and macOS |",
        "| `ifx` | `icx` | Tested on Linux with version 2026.1.1 |",
        "| `flang` | `clang` | Tested on Linux and macOS with version 22.1.8 |",
    ):
        assert compiler_pair in installation

    assert "| `ifort` | `icx` | Recognized; not routinely tested |" in installation
    assert "| `nvfortran` | `nvc` | Recognized; not yet tested |" in installation
    assert "| `pgfortran` | `pgcc` | Legacy option; not yet tested |" in installation
    assert "For the best-tested experience, use GNU, IFX, or Flang." in installation
    assert "--compiler ifx" in shared_library
    assert "--compiler flang" in shared_library
    assert "keeps both compilers in the same family" in shared_library


def test_cli_reference_reuses_the_derived_type_points_example() -> None:
    content = _visible_documentation_source(CLI_REFERENCE_PATH)

    assert "`points.f90` and `geometry` naming" in content
    assert "../guide/wrapping-derived-types.md#complete-example" in content
    assert "python3 -m prik parse points.f90" in content
    assert "python3 -m prik generate --pyi points.f90 --out contracts" in content
    assert "scale.f90" not in content


def test_fortran_wrapper_reference_shows_every_common_shared_library_build_input() -> None:
    content = _visible_documentation_source(DOCS_ROOT / "user/reference/fortran-wrapper.md")
    example = content.split("For example, this command supplies every common build input", maxsplit=1)[1].split(
        "`--compiler` selects", maxsplit=1
    )[0]

    for value in (
        "python3 -m prik solver.f90",
        "--out solver",
        "--out-dir build/solver",
        "--compiler gfortran",
        "-I include",
        "--native-compile-flags=-O3",
        "--native-library openblas",
        "--verbose",
    ):
        assert value in example


def test_array_handle_docs_keep_views_copies_and_handles_distinct() -> None:
    allocatables = _visible_documentation_source(DOCS_ROOT / "user/guide/allocatables.md")
    pointers = _visible_documentation_source(DOCS_ROOT / "user/guide/pointers.md")
    memory = _visible_documentation_source(DOCS_ROOT / "user/guide/memory-management.md")

    assert "Reading the Python attribute" in allocatables
    assert "returns an `Allocatable[T[...]]` handle, not `ndarray | None`." in allocatables
    assert "never creates an automatic detached snapshot" in allocatables
    assert "A NumPy view reflects current native storage." in allocatables
    assert "A pointer-array function result becomes a returned `PointerArray`." in pointers
    assert "has persistent descriptor storage, but the target can belong to another" in pointers
    assert "`associate(other)` makes two pointer handles refer to the same target" in pointers
    assert "If `p2` is unassociated, `p1` becomes" in pointers
    assert "Do Not Return A Pointer To Expired Local Storage" in pointers
    assert "Derived module variables remain live objects" in memory
    assert "Fortran module owns their storage" in memory


def test_parameter_array_references_document_read_only_snapshots() -> None:
    references = [
        _visible_documentation_source(DOCS_ROOT / "user/reference/fortran-wrapper.md"),
        _visible_documentation_source(DOCS_ROOT / "user/reference/generated-modules.md"),
    ]

    for reference in references:
        normalized_reference = " ".join(reference.split())
        assert "Python-owned" in normalized_reference
        assert "read-only NumPy snapshots" in normalized_reference
        assert "no native setter" in normalized_reference

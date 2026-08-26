"""Target-specific datatype mapping report tests."""

import json
import shutil

import pytest

import prik.pipeline.type_mapping_report as type_mapping_report


def _mapping_markdown(language, **options):
    builder = (
        type_mapping_report.c_type_mapping_report
        if language == "c"
        else type_mapping_report.fortran_type_mapping_report
    )
    return type_mapping_report.type_mapping_markdown(builder(**options))


@pytest.mark.parametrize(
    ("language", "compiler", "native_header", "representative"),
    [
        ("c", "cc", "| C type |", "| `long double` |"),
        (
            "fortran",
            "gfortran",
            "| Fortran type |",
            "| `real(kind(1.0d0))` | 64-bit storage | `Float64` |",
        ),
    ],
)
def test_type_mapping_markdown_covers_target_native_semantic_and_numpy_types(
    language,
    compiler,
    native_header,
    representative,
):
    if shutil.which(compiler) is None:
        pytest.skip(f"{compiler} is required for the target-specific mapping report")

    report = _mapping_markdown(language, compiler=compiler)

    assert report.startswith(f"Target profile: `{type_mapping_report.target_profile()}`")
    assert native_header in report
    assert representative in report
    assert "Semantic dtype | NumPy dtype" in report


@pytest.mark.parametrize(("language", "compiler"), [("c", "cc"), ("fortran", "gfortran")])
def test_type_mapping_markdown_renders_only_from_the_serialized_report(language, compiler):
    """Markdown must be a pure conversion of the JSON record, not a second measurement."""
    if shutil.which(compiler) is None:
        pytest.skip(f"{compiler} is required for the target-specific mapping report")

    builder = (
        type_mapping_report.c_type_mapping_report
        if language == "c"
        else type_mapping_report.fortran_type_mapping_report
    )
    report = builder(compiler=compiler)
    round_tripped = json.loads(json.dumps(report))

    assert type_mapping_report.type_mapping_markdown(round_tripped) == type_mapping_report.type_mapping_markdown(report)


@pytest.mark.parametrize(("language", "compiler"), [("c", "cc"), ("fortran", "gfortran")])
def test_type_mapping_report_records_structured_measurements(language, compiler):
    """JSON consumers read measured numbers instead of parsing the display text."""
    if shutil.which(compiler) is None:
        pytest.skip(f"{compiler} is required for the target-specific mapping report")

    builder = (
        type_mapping_report.c_type_mapping_report
        if language == "c"
        else type_mapping_report.fortran_type_mapping_report
    )
    report = builder(compiler=compiler)

    assert report["report"] == "type_mapping"
    assert report["language"] == language
    assert report["recipe"]["compiler"] == compiler
    entry = next(item for item in report["types"] if item["native"] in {"int", "integer"})
    assert entry["target_fact"]["bits"] == 32
    assert str(entry["target_fact"]["bits"]) in entry["native_fact"]


def test_type_mapping_report_main_selects_language(monkeypatch, capsys):
    monkeypatch.setattr(
        type_mapping_report,
        "c_type_mapping_report",
        lambda *, compiler, compiler_args, **options: f"C:{compiler}:{','.join(compiler_args)}:{options['refresh']}",
    )
    monkeypatch.setattr(
        type_mapping_report,
        "fortran_type_mapping_report",
        lambda *, compiler, compiler_args, **options: f"F:{compiler}:{','.join(compiler_args)}:{options['refresh']}",
    )
    monkeypatch.setattr(type_mapping_report, "type_mapping_markdown", lambda report: report)

    assert type_mapping_report.main(["--language", "c", "--compiler", "clang", "--compiler-arg=-m32", "--refresh"]) == 0
    assert capsys.readouterr().out == "C:clang:-m32:True\n"

    assert type_mapping_report.main(["--language", "fortran"]) == 0
    assert capsys.readouterr().out == "F:gfortran::False\n"


def test_fortran_type_mapping_uses_compiler_dependent_defaults():
    if shutil.which("gfortran") is None:
        pytest.skip("gfortran is required for the target-specific mapping report")

    report = _mapping_markdown("fortran", compiler_args=["-fdefault-integer-8", "-fdefault-real-8"])

    assert "| `integer` | 64-bit storage | `Int64` | `numpy.int64` |" in report
    assert "| `real` | 64-bit storage | `Float64` | `numpy.float64` |" in report
    assert "| `complex` | 128-bit storage | `Complex128` | `numpy.complex128` |" in report
    assert "| `double precision` | 128-bit storage | `Float128` | `numpy.longdouble` |" in report
    assert "| `double complex` | 256-bit storage | `Complex256` | `numpy.clongdouble` |" in report
    assert "| `complex*16` | 128-bit storage | `Complex128` | `numpy.complex128` |" in report


def test_fortran_type_mapping_includes_legacy_and_modern_spellings():
    if shutil.which("gfortran") is None:
        pytest.skip("gfortran is required for the target-specific mapping report")

    report = _mapping_markdown("fortran")

    assert "| `complex(kind=8)` | 128-bit storage | `Complex128` | `numpy.complex128` |" in report
    assert "| `complex*8` | 64-bit storage | `Complex64` | `numpy.complex64` |" in report
    assert "| `double precision` | 64-bit storage | `Float64` | `numpy.float64` |" in report
    assert "| `double complex` | 128-bit storage | `Complex128` | `numpy.complex128` |" in report
    assert "| `character*8` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |" in report


def test_target_profile_normalizes_common_machine_names(monkeypatch):
    monkeypatch.setattr(type_mapping_report.platform, "system", lambda: "Linux")
    monkeypatch.setattr(type_mapping_report.platform, "machine", lambda: "AMD64")

    assert type_mapping_report.target_profile() == "linux-x86_64"


def test_character_mapping_fact_is_modeled_without_compiler_probe_metadata():
    semantic_type = type("SemanticType", (), {"metadata": {}})()

    fact = type_mapping_report._fortran_target_fact(semantic_type, ("character", "c_char"))

    assert fact == {"bits": 8}
    assert type_mapping_report._fortran_fact_text(fact) == "8-bit storage"


def test_expression_probe_markdown_renders_measured_values():
    if shutil.which("gfortran") is None:
        pytest.skip("gfortran is required for the Fortran expression probe")

    from prik.preprocessing import PreprocessingConfig
    from prik.preprocessing.probes.fortran_types import probe_fortran_type_expressions_cached

    report = probe_fortran_type_expressions_cached(
        PreprocessingConfig(mode="compiler", compiler="gfortran"),
        ["kind(1.0d0)", "storage_size(0)"],
    )

    markdown = type_mapping_report.expression_probe_markdown(report)

    assert markdown.startswith("Compiler: `gfortran`")
    assert "| Fortran expression | Measured value |" in markdown
    assert "| `kind(1.0d0)` | 8 |" in markdown
    assert "| `storage_size(0)` | 32 |" in markdown

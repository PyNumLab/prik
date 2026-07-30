"""Target-specific datatype mapping report tests."""

import shutil

import pytest

import x2py.probes.report as type_mapping_report


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

    report = (
        type_mapping_report.c_type_mapping_markdown(compiler=compiler)
        if language == "c"
        else type_mapping_report.fortran_type_mapping_markdown(compiler=compiler)
    )

    assert report.startswith(f"Target profile: `{type_mapping_report.target_profile()}`")
    assert native_header in report
    assert representative in report
    assert "Semantic dtype | NumPy dtype" in report


def test_type_mapping_report_main_selects_language(monkeypatch, capsys):
    monkeypatch.setattr(
        type_mapping_report,
        "c_type_mapping_markdown",
        lambda *, compiler, compiler_args, **options: f"C:{compiler}:{','.join(compiler_args)}:{options['refresh']}",
    )
    monkeypatch.setattr(
        type_mapping_report,
        "fortran_type_mapping_markdown",
        lambda *, compiler, compiler_args, **options: f"F:{compiler}:{','.join(compiler_args)}:{options['refresh']}",
    )

    assert type_mapping_report.main(["--language", "c", "--compiler", "clang", "--compiler-arg=-m32", "--refresh"]) == 0
    assert capsys.readouterr().out == "C:clang:-m32:True\n"

    assert type_mapping_report.main(["--language", "fortran"]) == 0
    assert capsys.readouterr().out == "F:gfortran::False\n"


def test_fortran_type_mapping_uses_compiler_dependent_defaults():
    if shutil.which("gfortran") is None:
        pytest.skip("gfortran is required for the target-specific mapping report")

    report = type_mapping_report.fortran_type_mapping_markdown(
        compiler_args=["-fdefault-integer-8", "-fdefault-real-8"]
    )

    assert "| `integer` | 64-bit storage | `Int64` | `numpy.int64` |" in report
    assert "| `real` | 64-bit storage | `Float64` | `numpy.float64` |" in report
    assert "| `complex` | 128-bit storage | `Complex128` | `numpy.complex128` |" in report
    assert "| `double precision` | 128-bit storage | `Float128` | `numpy.longdouble` |" in report
    assert "| `double complex` | 256-bit storage | `Complex256` | `numpy.clongdouble` |" in report
    assert "| `complex*16` | 128-bit storage | `Complex128` | `numpy.complex128` |" in report


def test_fortran_type_mapping_includes_legacy_and_modern_spellings():
    if shutil.which("gfortran") is None:
        pytest.skip("gfortran is required for the target-specific mapping report")

    report = type_mapping_report.fortran_type_mapping_markdown()

    assert "| `complex(kind=8)` | 128-bit storage | `Complex128` | `numpy.complex128` |" in report
    assert "| `complex*8` | 64-bit storage | `Complex64` | `numpy.complex64` |" in report
    assert "| `double precision` | 64-bit storage | `Float64` | `numpy.float64` |" in report
    assert "| `double complex` | 128-bit storage | `Complex128` | `numpy.complex128` |" in report
    assert "| `character*8` | 8-bit storage | `String` | `numpy.str_ / ABI bytes` |" in report


def test_target_profile_normalizes_common_machine_names(monkeypatch):
    monkeypatch.setattr(type_mapping_report.platform, "system", lambda: "Linux")
    monkeypatch.setattr(type_mapping_report.platform, "machine", lambda: "AMD64")

    assert type_mapping_report.target_profile() == "linux-x86_64"

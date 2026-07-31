"""Tests split by stable ownership concept from `test_properties.py`."""

from tests.fortran._support.parser_properties import (
    FortranParseError,
    Path,
    PreprocessingConfig,
    TemporaryDirectory,
    _FORTRAN_IDENTIFIER_STEMS,
    given,
    parse_fortran_file,
    patch,
    preprocess_source,
    preprocessing,
    pytest,
    st,
    sys,
)


@pytest.mark.property
@given(include_stem=_FORTRAN_IDENTIFIER_STEMS)
def test_generated_fortran_native_includes_do_not_change_public_signature(include_stem):
    target = f"{include_stem}.inc"
    baseline = "subroutine generated_include(value)\n  integer, intent(in) :: value\nend subroutine generated_include\n"
    with_include = (
        f"subroutine generated_include(value)\n"
        f"  include '{target}'\n"
        "  integer, intent(in) :: value\n"
        "end subroutine generated_include\n"
    )

    baseline_parsed = parse_fortran_file(baseline, filename="generated_include.f90")
    included_parsed = parse_fortran_file(with_include, filename="generated_include.f90")

    assert included_parsed.diagnostics == []
    assert included_parsed.procedures == baseline_parsed.procedures


@pytest.mark.property
@given(feature_stem=_FORTRAN_IDENTIFIER_STEMS)
def test_generated_fortran_raw_preprocessor_directives_require_preprocessing(feature_stem):
    feature = f"feature_{feature_stem}"
    source = f"#ifdef {feature}\nsubroutine generated_conditional()\nend subroutine generated_conditional\n#endif\n"

    with pytest.raises(FortranParseError, match="require compiler preprocessing") as exc_info:
        parse_fortran_file(source, filename="generated_conditional.F90")

    assert exc_info.value.code == "PARSE_PREPROCESSING_REQUIRED"


@pytest.mark.property
@given(feature_stem=_FORTRAN_IDENTIFIER_STEMS, select_feature=st.booleans())
def test_generated_fortran_compiler_preprocessing_selects_macro_branch(feature_stem, select_feature):
    feature = f"feature_{feature_stem}"
    with TemporaryDirectory() as tmp_dir:
        source_path = Path(tmp_dir) / "generated_conditional.F90"
        source_path.write_text(
            f"#ifdef {feature}\n"
            "subroutine selected_path()\n"
            "end subroutine selected_path\n"
            "#else\n"
            "subroutine fallback_path()\n"
            "end subroutine fallback_path\n"
            "#endif\n",
            encoding="utf-8",
        )
        captured_argv = []

        def run_compiler(argv, **_kwargs):
            captured_argv.extend(argv)
            selected = f"-D{feature}" in argv
            procedure_name = "selected_path" if selected else "fallback_path"
            stdout = f"subroutine {procedure_name}()\nend subroutine {procedure_name}\n"
            return type("Done", (), {"returncode": 0, "stdout": stdout, "stderr": ""})()

        defines = [feature] if select_feature else []
        with patch.object(preprocessing.subprocess, "run", run_compiler):
            result = preprocess_source(
                source_path,
                language="fortran",
                config=PreprocessingConfig(mode="compiler", compiler=sys.executable, defines=defines),
            )
        parsed = parse_fortran_file(result.source, filename=str(source_path))

    assert "-cpp" in captured_argv
    assert (f"-D{feature}" in captured_argv) is select_feature
    assert result.recipe["defines"] == defines
    assert [procedure.name for procedure in parsed.procedures] == [
        "selected_path" if select_feature else "fallback_path"
    ]

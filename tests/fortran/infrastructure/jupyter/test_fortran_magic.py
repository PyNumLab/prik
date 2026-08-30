"""Notebook magic contracts shared by Fortran source cells."""

from __future__ import annotations

import hashlib
from pathlib import Path
from types import ModuleType

from IPython.core.error import UsageError
import pytest

import prik.jupyter.contracts as contract_cells
import prik.jupyter.magic as magic_module
from prik.jupyter import load_ipython_extension
from prik.jupyter.magic import PrikMagics
from prik.pipeline.build import WrapperBuildResult


class _Shell:
    def __init__(self) -> None:
        self.user_ns: dict[str, object] = {}
        self.next_inputs: list[tuple[str, bool]] = []

    def push(self, values: dict[str, object]) -> None:
        self.user_ns.update(values)

    def set_next_input(self, text: str, *, replace: bool = False) -> None:
        self.next_inputs.append((text, replace))


def _mock_build_result(
    source: Path,
    kwargs: dict[str, object],
    modules: dict[str, ModuleType],
    *,
    public_name: str,
) -> WrapperBuildResult:
    output_dir = Path(kwargs["output_dir"])
    output_dir.mkdir(parents=True, exist_ok=True)
    module_name = str(kwargs["output_name"])
    shared_library = output_dir / f"{module_name}.so"
    shared_library.write_bytes(b"mock extension")

    extension = ModuleType(module_name)
    namespace = ModuleType(f"{module_name}.{public_name}")
    setattr(extension, public_name, namespace)
    modules[module_name] = extension
    return WrapperBuildResult(
        sources=(source,),
        module_name=module_name,
        output_dir=output_dir,
        shared_library=shared_library,
        build_makefile=None,
        compiled=True,
        generated_sources=(),
        generated_files=(),
    )


def test_fortran_magic_routes_options_publishes_declared_namespace_and_reuses_exact_cell(
    tmp_path: Path,
    monkeypatch,
    capsys,
):
    modules: dict[str, ModuleType] = {}
    calls: list[tuple[Path, dict[str, object]]] = []

    def build(source: Path, **kwargs) -> WrapperBuildResult:
        calls.append((source, kwargs))
        return _mock_build_result(source, kwargs, modules, public_name="maths")

    monkeypatch.setattr(magic_module, "build_fortran_extension", build)
    monkeypatch.setattr(WrapperBuildResult, "import_module", lambda self: modules[self.module_name])
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")
    cell = "module maths\ncontains\nend module\n"
    line = (
        "--compiler ifx --compiler-arg=-fpp "
        '--native-compile-flags="-O3 -xHost" '
        "--wrapper-fortran-flags=-O2 --wrapper-c-flags=-O1"
    )

    magic.fortran(line, cell)

    first_namespace = shell.user_ns["maths"]
    source, kwargs = calls[0]
    digest = hashlib.sha256(f"fortran{cell}".encode()).hexdigest()
    assert source == tmp_path / "cache" / digest / "cell.f90"
    assert source.read_text(encoding="utf-8") == cell
    assert kwargs["preprocessing"].compiler == "ifx"
    assert kwargs["preprocessing"].compiler_args == ["-fpp"]
    assert kwargs["native_fortran_flags"] == ("-O3", "-xHost")
    assert kwargs["wrapper_fortran_flags"] == ("-O2",)
    assert kwargs["wrapper_c_flags"] == ("-O1",)
    assert kwargs["_public_root"] == ""
    assert kwargs["verbose"] is False
    assert len(shell.user_ns) == 1

    magic.fortran(f"{line} --verbose", cell)

    assert len(calls) == 1
    assert shell.user_ns["maths"] is first_namespace
    assert f">> Reuse cached PRIK cell: {digest}" in capsys.readouterr().out

    magic.fortran(f"{line} --force", cell)

    assert len(calls) == 2
    assert shell.user_ns["maths"] is not first_namespace
    assert calls[1][1]["output_name"] != calls[0][1]["output_name"]


def test_same_source_digest_rebuilds_when_compiler_configuration_changes(tmp_path: Path, monkeypatch):
    modules: dict[str, ModuleType] = {}
    calls: list[dict[str, object]] = []

    def build(source: Path, **kwargs) -> WrapperBuildResult:
        calls.append(kwargs)
        return _mock_build_result(source, kwargs, modules, public_name="maths")

    monkeypatch.setattr(magic_module, "build_fortran_extension", build)
    monkeypatch.setattr(WrapperBuildResult, "import_module", lambda self: modules[self.module_name])
    magic = PrikMagics(_Shell(), cache_dir=tmp_path / "cache")
    cell = "module maths\nend module\n"

    magic.fortran("--compiler gfortran", cell)
    magic.fortran("--compiler ifx", cell)

    digest = hashlib.sha256(f"fortran{cell}".encode()).hexdigest()
    assert len(calls) == 2
    assert [path.name for path in (tmp_path / "cache").iterdir() if path.is_dir()] == [digest]


def test_generate_pyi_persists_source_and_inserts_module_and_standalone_contract_cells(
    tmp_path: Path,
    monkeypatch,
):
    source = "module maths\nend module\n"
    digest = hashlib.sha256(f"fortran{source}".encode()).hexdigest()

    def generate(path: Path, *, source_digest: str, options) -> contract_cells.GeneratedContracts:
        assert path.read_text(encoding="utf-8") == source
        assert source_digest == digest
        assert options.compiler == "ifx"
        return contract_cells.GeneratedContracts(
            language="fortran",
            source_digest=source_digest,
            module_contracts={
                "maths.pyi": "def square() -> None: ...",
                "stats.pyi": "def mean() -> None: ...",
            },
            direct_contract=("from prik.contracts import standalone\n\n@standalone\ndef reset() -> None: ..."),
            dependency_contracts={},
        )

    monkeypatch.setattr(contract_cells, "generate_contracts_from_source", generate)
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")

    magic.fortran("--pyi --compiler ifx", source)

    assert (tmp_path / "cache" / digest / "cell.f90").read_text(encoding="utf-8") == source
    assert len(shell.next_inputs) == 3
    maths, stats, standalone = (text for text, replace in shell.next_inputs if not replace)
    assert maths.startswith("%%pyi --compiler ifx\n")
    assert f"# prik: file=maths.pyi source-sha256={digest}" in maths
    assert f"# prik: file=stats.pyi source-sha256={digest}" in stats
    assert f"# prik: source-sha256={digest}" in standalone
    assert "file=__init__.pyi" not in standalone
    assert "@standalone" in standalone


def test_generated_module_contract_builds_against_cached_source_and_reuses_exact_edit(
    tmp_path: Path,
    monkeypatch,
):
    modules: dict[str, ModuleType] = {}
    calls: list[tuple[Path, dict[str, object]]] = []

    def generate(path: Path, *, source_digest: str, options) -> contract_cells.GeneratedContracts:
        return contract_cells.GeneratedContracts(
            language="fortran",
            source_digest=source_digest,
            module_contracts={"maths.pyi": "def square() -> None: ..."},
            direct_contract=None,
            dependency_contracts={},
        )

    def build(contract: Path, **kwargs) -> WrapperBuildResult:
        calls.append((contract, kwargs))
        return _mock_build_result(contract, kwargs, modules, public_name="maths")

    monkeypatch.setattr(contract_cells, "generate_contracts_from_source", generate)
    monkeypatch.setattr(magic_module, "build_pyi_extension", build)
    monkeypatch.setattr(WrapperBuildResult, "import_module", lambda self: modules[self.module_name])
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")
    source = "module maths\nend module\n"

    magic.fortran(
        '--pyi --compiler ifx --native-compile-flags="-O3 -xHost"',
        source,
    )
    inserted = shell.next_inputs[0][0]
    magic_line, editable_cell = inserted.split("\n", 1)
    line = magic_line.removeprefix("%%pyi").strip()
    editable_cell = "# user note\n" + editable_cell.replace("def square()", "def square(value: int)")

    magic.pyi(line, editable_cell)
    first_namespace = shell.user_ns["maths"]
    contract, kwargs = calls[0]
    assert contract.name == "__init__.pyi"
    assert contract.read_text(encoding="utf-8") == "from . import maths\n"
    assert "def square(value: int)" in (contract.parent / "maths.pyi").read_text(encoding="utf-8")
    assert "# user note" in (contract.parent / "maths.pyi").read_text(encoding="utf-8")
    source_path = tmp_path / "cache" / hashlib.sha256(f"fortran{source}".encode()).hexdigest() / "cell.f90"
    assert kwargs["native_language"] == "fortran"
    assert kwargs["input_compiler"] == "ifx"
    assert kwargs["native_fortran_sources"] == (source_path,)
    assert kwargs["native_fortran_flags"] == ("-O3", "-xHost")
    assert kwargs["_public_root"] == ""

    magic.pyi(line, editable_cell)

    assert len(calls) == 1
    assert shell.user_ns["maths"] is first_namespace

    magic.pyi(f"{line} --force", editable_cell)

    assert len(calls) == 2
    assert shell.user_ns["maths"] is not first_namespace


def test_generated_standalone_contract_publishes_direct_declarations(tmp_path: Path, monkeypatch):
    modules: dict[str, ModuleType] = {}
    calls: list[Path] = []

    def generate(path: Path, *, source_digest: str, options) -> contract_cells.GeneratedContracts:
        return contract_cells.GeneratedContracts(
            language="fortran",
            source_digest=source_digest,
            module_contracts={},
            direct_contract="@standalone\ndef square() -> None: ...",
            dependency_contracts={},
        )

    def build(contract: Path, **kwargs) -> WrapperBuildResult:
        calls.append(contract)
        output_dir = Path(kwargs["output_dir"])
        output_dir.mkdir(parents=True, exist_ok=True)
        module_name = str(kwargs["output_name"])
        shared_library = output_dir / f"{module_name}.so"
        shared_library.write_bytes(b"mock extension")
        extension = ModuleType(module_name)
        extension.square = lambda: 4
        modules[module_name] = extension
        return WrapperBuildResult(
            sources=(contract,),
            module_name=module_name,
            output_dir=output_dir,
            shared_library=shared_library,
            build_makefile=None,
            compiled=True,
            generated_sources=(),
            generated_files=(),
        )

    monkeypatch.setattr(contract_cells, "generate_contracts_from_source", generate)
    monkeypatch.setattr(magic_module, "build_pyi_extension", build)
    monkeypatch.setattr(WrapperBuildResult, "import_module", lambda self: modules[self.module_name])
    shell = _Shell()
    magic = PrikMagics(shell, cache_dir=tmp_path / "cache")

    magic.fortran("--pyi", "subroutine square()\nend subroutine\n")
    inserted = shell.next_inputs[0][0]
    magic_line, editable_cell = inserted.split("\n", 1)
    assert magic_line == "%%pyi"
    assert " file=" not in editable_cell

    magic.pyi(magic_line.removeprefix("%%pyi").strip(), editable_cell)

    assert calls[0].read_text(encoding="utf-8").endswith("@standalone\ndef square() -> None: ...\n")
    assert shell.user_ns["square"]() == 4
    assert "cell" not in shell.user_ns


def test_multiple_generated_contracts_use_distinct_jupyter_payloads():
    writes: list[tuple[dict[str, object], bool]] = []

    class _PayloadManager:
        def write_payload(self, payload: dict[str, object], *, single: bool = True) -> None:
            writes.append((payload, single))

    class _PayloadShell:
        payload_manager = _PayloadManager()

        def set_next_input(self, text: str, *, replace: bool = False) -> None:
            raise AssertionError("multiple contract cells must not replace one set_next_input payload")

    contract_cells.insert_editable_cells(_PayloadShell(), ["first", "second"])

    assert writes == [
        ({"source": "set_next_input", "text": "first", "replace": False}, False),
        ({"source": "set_next_input", "text": "second", "replace": False}, False),
    ]


def test_editable_contract_requires_its_exact_cached_source(tmp_path: Path):
    magic = PrikMagics(_Shell(), cache_dir=tmp_path / "cache")
    digest = "a" * 64
    cell = f"# prik: file=maths.pyi source-sha256={digest}\n\ndef square(): ...\n"

    with pytest.raises(UsageError, match="execute its %%fortran --pyi or %%c --pyi source cell again"):
        magic.pyi("", cell)


def test_magic_reports_usage_without_terminating_ipython(tmp_path: Path, capsys):
    magic = PrikMagics(_Shell(), cache_dir=tmp_path / "cache")

    magic.fortran("--help", "")
    assert "usage: %%fortran" in capsys.readouterr().out

    with pytest.raises(UsageError, match="non-empty"):
        magic.fortran("", "\n")
    with pytest.raises(UsageError, match="only generates editable cells"):
        magic.fortran("--pyi --force", "source")
    with pytest.raises(UsageError, match="metadata comment"):
        magic.pyi("", "def square(): ...\n")
    with pytest.raises(UsageError, match="full lowercase source-sha256"):
        magic.pyi(
            "",
            "# prik: file=maths.pyi source-sha256=short\ndef square(): ...\n",
        )


def test_ipython_extension_hook_registers_the_magic_class():
    registered = []

    class _RegistrationShell:
        def register_magics(self, magic_class) -> None:
            registered.append(magic_class)

    load_ipython_extension(_RegistrationShell())

    assert registered == [PrikMagics]


def test_ipython_extension_refuses_to_replace_an_existing_cell_magic():
    class _ConflictingShell:
        def find_cell_magic(self, name: str):
            return (lambda: None) if name == "c" else None

        def register_magics(self, magic_class) -> None:
            raise AssertionError("conflicting magics must be reported before registration")

    with pytest.raises(UsageError, match=r"already registered: %%c"):
        load_ipython_extension(_ConflictingShell())

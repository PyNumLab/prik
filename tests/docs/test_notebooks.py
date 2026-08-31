"""Shipped example notebooks execute and keep the results they advertise.

A notebook is the one documented artifact a reader runs unedited, and its
cells embed a digest of the exact source they were generated from. Executing
it here keeps both honest: a magic that stops working, or a source cell that
drifts away from its contract cell, fails the suite instead of the reader.
"""

from __future__ import annotations

import hashlib
import os
import shutil
from pathlib import Path

import pytest


nbformat = pytest.importorskip("nbformat")
nbclient = pytest.importorskip("nbclient")

NOTEBOOK_DIR = Path(__file__).parents[2] / "examples/notebooks"
# The Colab setup cell installs a toolchain and PRIK itself, which the suite
# already has; every other cell runs.
SETUP_TAG = "prik-colab-setup"


def _notebooks() -> list[Path]:
    return sorted(NOTEBOOK_DIR.glob("*.ipynb"))


def test_example_notebooks_are_present():
    assert _notebooks(), f"No example notebooks found in {NOTEBOOK_DIR}"


@pytest.mark.parametrize("notebook_path", _notebooks(), ids=lambda path: path.stem)
def test_notebook_is_shipped_without_stored_output(notebook_path: Path):
    """Stored output would go stale silently; the test is what proves the cells."""
    notebook = nbformat.read(notebook_path, as_version=4)

    stored = [index for index, cell in enumerate(notebook.cells) if cell.get("outputs")]

    assert not stored, f"{notebook_path.name} ships stored output in cells {stored}"


@pytest.mark.parametrize("notebook_path", _notebooks(), ids=lambda path: path.stem)
def test_editable_contract_cells_match_their_source_cell(notebook_path: Path):
    """A `# prik:` digest must name a source cell that is still in the notebook."""
    notebook = nbformat.read(notebook_path, as_version=4)
    available = {
        hashlib.sha256(f"{language}{_magic_body(cell.source)}".encode()).hexdigest()
        for cell in notebook.cells
        for language in ("fortran", "c")
        if cell.cell_type == "code" and cell.source.startswith(f"%%{language}")
    }

    for index, cell in enumerate(notebook.cells):
        for line in cell.source.splitlines():
            if not line.strip().startswith("# prik:"):
                continue
            digest = next(
                (field.split("=", 1)[1] for field in line.split() if field.startswith("source-sha256=")),
                None,
            )
            assert digest in available, (
                f"{notebook_path.name} cell {index} names source-sha256={digest}, "
                "which no source cell in the notebook produces"
            )


def _magic_body(source: str) -> str:
    """Return the cell body a magic receives, without its own `%%` line."""
    _line, _, body = source.partition("\n")
    return body


@pytest.mark.skipif(shutil.which("gfortran") is None, reason="requires gfortran")
@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
@pytest.mark.parametrize("notebook_path", _notebooks(), ids=lambda path: path.stem)
def test_notebook_executes_and_publishes_its_documented_results(notebook_path: Path, tmp_path: Path):
    notebook = nbformat.read(notebook_path, as_version=4)
    notebook.cells = [cell for cell in notebook.cells if SETUP_TAG not in cell.get("metadata", {}).get("tags", [])]

    # An isolated cache makes the run prove a real compile rather than reuse
    # whatever this machine built earlier.
    environment = dict(os.environ, PRIK_CACHE_DIR=str(tmp_path / "cache"))
    nbclient.NotebookClient(
        notebook,
        timeout=600,
        kernel_name="python3",
        resources={"metadata": {"path": str(tmp_path)}},
    ).execute(env=environment)

    printed = "\n".join(text for cell in notebook.cells for text in _cell_text(cell))

    # Every documented result is asserted inside the notebook, so a passing run
    # shows one tick per claim.
    assert printed.count("\u2705") == 3, printed
    assert "\U0001f389 All checks passed." in printed
    # The same C routine, reached through a hand-written count and then through
    # a contract that derives it.
    assert printed.count("(expected [2. 4. 6.])") == 2, printed


def _cell_text(cell) -> list[str]:
    texts = []
    for output in cell.get("outputs", []):
        assert output.get("output_type") != "error", f"cell raised {output.get('ename')}: {output.get('evalue')}"
        text = output.get("text") or (output.get("data") or {}).get("text/plain")
        if text:
            texts.append(text.strip())
    return texts

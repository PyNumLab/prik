"""Generated Fortran `.pyi` fixture-package comparison helpers."""

import os
import shutil
from pathlib import Path

UPDATE_PYI_PACKAGE_FIXTURES = os.getenv("WRAPPER_UPDATE_PYI_FIXTURES", "0") == "1"


def pyi_package_texts(root: Path) -> dict[Path, str]:
    return {
        path.relative_to(root): path.read_text(encoding="utf-8")
        for path in sorted(root.rglob("*.pyi"))
        if path.is_file()
    }


def assert_generated_pyi_package_matches_fixture(generated_root: Path, expected_root: Path) -> None:
    """Compare a generated `.pyi` package with its checked fixture."""
    generated = pyi_package_texts(generated_root)
    assert generated, f"No generated .pyi files found under {generated_root}"

    if UPDATE_PYI_PACKAGE_FIXTURES:
        if expected_root.exists():
            shutil.rmtree(expected_root)
        for relpath, text in generated.items():
            target = expected_root / relpath
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(text, encoding="utf-8")
        return

    assert expected_root.is_dir(), f"Missing expected .pyi fixture package: {expected_root}"
    assert generated == pyi_package_texts(expected_root)

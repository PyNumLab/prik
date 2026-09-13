"""Which installation answers for the PRIK that is running.

A build integration hands the reported prefix straight to another tool, so it
has to belong to this PRIK. Two installations can hold ``share/prik`` at once
-- a global one beside a ``pip install --user`` -- and the prefix that answers
must be the one whose record covers the running package, not whichever root is
searched first.
"""

from importlib import metadata
import json
from pathlib import Path
import site
import sys
import sysconfig

import pytest

import prik
from prik.installation import data_roots, install_dir


PACKAGE_DIR = Path(prik.__file__).resolve().parent
RECORDED_CONFIG = "../../../share/prik/cmake/PRIKConfig.cmake"


class _FakeDistribution:
    """Stand in for the metadata one installed PRIK distribution records."""

    def __init__(self, *, package_dir: Path, prefix: Path | None = None, editable_source: Path | None = None) -> None:
        self._package_dir = package_dir
        self._prefix = prefix
        self._editable_source = editable_source

    @property
    def files(self) -> list[metadata.PackagePath]:
        return [metadata.PackagePath(RECORDED_CONFIG)] if self._prefix is not None else []

    def locate_file(self, path: object) -> Path:
        if str(path) == "prik":
            return self._package_dir
        assert self._prefix is not None
        return self._prefix / "lib" / "python3" / "site-packages" / str(path)

    def read_text(self, name: str) -> str | None:
        if name != "direct_url.json" or self._editable_source is None:
            return None
        return json.dumps({"dir_info": {"editable": True}, "url": self._editable_source.as_uri()})


def _installed_prefix(root: Path) -> Path:
    """Write the data files and package directory a wheel installs under one prefix."""
    (root / "share" / "prik" / "cmake").mkdir(parents=True)
    (root / "share" / "prik" / "cmake" / "PRIKConfig.cmake").write_text("", encoding="utf-8")
    (root / "lib" / "python3" / "site-packages").mkdir(parents=True)
    return root


@pytest.fixture
def other_installation(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Put a complete, unrelated PRIK installation on every searchable root."""
    other = _installed_prefix(tmp_path / "other installation")
    monkeypatch.setattr(sysconfig, "get_path", lambda name, *arguments, **options: str(other))
    monkeypatch.setattr(sys, "prefix", str(other))
    return other


def test_data_roots_include_the_user_base_of_a_user_install(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(site, "ENABLE_USER_SITE", True)

    assert Path(site.getuserbase()) in data_roots()


def test_data_roots_drop_the_user_base_when_the_user_site_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """A venv, -s, and -I cannot import from the user site, so its data is not PRIK's."""
    monkeypatch.setattr(site, "ENABLE_USER_SITE", False)

    assert Path(site.getuserbase()) not in data_roots()


@pytest.mark.usefixtures("other_installation")
def test_install_dir_reports_the_prefix_its_own_installation_recorded(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second PRIK under a searchable prefix must never answer for this one."""
    prefix = _installed_prefix(tmp_path / "user base")
    monkeypatch.setattr(
        metadata, "distribution", lambda name: _FakeDistribution(package_dir=PACKAGE_DIR, prefix=prefix)
    )

    assert install_dir() == prefix


def test_install_dir_refuses_an_installation_of_another_package_copy(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    prefix = _installed_prefix(tmp_path / "other prefix")
    elsewhere = prefix / "lib" / "python3" / "site-packages" / "prik"
    monkeypatch.setattr(metadata, "distribution", lambda name: _FakeDistribution(package_dir=elsewhere, prefix=prefix))

    with pytest.raises(FileNotFoundError, match="does not provide"):
        install_dir()


def test_install_dir_accepts_an_editable_installation_of_the_running_tree(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An editable install provides this package but records no data files."""
    elsewhere = tmp_path / "site-packages" / "prik"
    monkeypatch.setattr(
        metadata,
        "distribution",
        lambda name: _FakeDistribution(package_dir=elsewhere, editable_source=PACKAGE_DIR.parent),
    )

    with pytest.raises(FileNotFoundError, match="editable install writes none"):
        install_dir()


def test_install_dir_reports_no_prefix_when_prik_is_not_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    def missing(name: str) -> metadata.Distribution:
        raise metadata.PackageNotFoundError(name)

    monkeypatch.setattr(metadata, "distribution", missing)

    with pytest.raises(FileNotFoundError, match="not installed"):
        install_dir()

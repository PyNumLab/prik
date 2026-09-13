"""Where PRIK looks for the data files an installation carries.

A build integration asks PRIK for an installation prefix and hands it straight
to another tool, so the searched roots have to match what an install actually
wrote -- including a ``pip install --user``, whose data files land under the
user base rather than under ``sys.prefix``.
"""

from pathlib import Path
import site
import sys
import sysconfig

import pytest

from prik.installation import data_roots, install_dir


@pytest.fixture
def only_empty_prefixes(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Point every non-user root at a prefix that installs nothing."""
    empty = tmp_path / "empty prefix"
    empty.mkdir()
    monkeypatch.setattr(sysconfig, "get_path", lambda name, *arguments, **options: str(empty))
    monkeypatch.setattr(sys, "prefix", str(empty))
    return empty


def test_data_roots_include_the_user_base_of_a_user_install(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(site, "ENABLE_USER_SITE", True)

    assert Path(site.getuserbase()) in data_roots()


def test_data_roots_drop_the_user_base_when_the_user_site_is_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    """A venv, -s, and -I cannot import from the user site, so its data is not PRIK's."""
    monkeypatch.setattr(site, "ENABLE_USER_SITE", False)

    assert Path(site.getuserbase()) not in data_roots()


@pytest.mark.usefixtures("only_empty_prefixes")
def test_install_dir_reports_the_user_base_of_a_user_install(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    user_base = tmp_path / "user base"
    (user_base / "share" / "prik" / "cmake").mkdir(parents=True)
    monkeypatch.setattr(site, "ENABLE_USER_SITE", True)
    monkeypatch.setattr(site, "getuserbase", lambda: str(user_base))

    assert install_dir() == user_base


@pytest.mark.usefixtures("only_empty_prefixes")
def test_install_dir_reports_no_prefix_when_nothing_is_installed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(site, "ENABLE_USER_SITE", False)

    with pytest.raises(FileNotFoundError, match="not installed"):
        install_dir()

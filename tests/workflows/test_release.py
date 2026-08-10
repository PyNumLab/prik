"""Release workflow safety contracts."""

from pathlib import Path


REPOSITORY_ROOT = Path(__file__).parents[2]
PUBLISH_WORKFLOW = REPOSITORY_ROOT / ".github/workflows/publish-to-pypi.yml"


def test_pypi_publication_uses_protected_token_free_release_job() -> None:
    workflow = PUBLISH_WORKFLOW.read_text(encoding="utf-8")
    build_job, publish_job = workflow.split("  publish:\n", maxsplit=1)

    assert "id-token: write" not in build_job
    assert "needs: build" in publish_job
    assert "name: pypi" in publish_job
    assert "id-token: write" in publish_job
    assert "uses: pypa/gh-action-pypi-publish@release/v1" in publish_job
    assert "secrets." not in workflow
    assert "password:" not in workflow

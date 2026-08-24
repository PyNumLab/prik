"""Documentation metadata and visibility contracts."""

from pathlib import Path

import pytest

from tests.docs._structure_support import (
    ALLOWED_PUBLICATION_STATES,
    ALLOWED_STATUSES,
    DOC_PATHS,
    REQUIRED_METADATA,
    ROOT,
    _front_matter,
)


@pytest.mark.parametrize("path", DOC_PATHS, ids=lambda path: str(path.relative_to(ROOT)))
def test_documentation_page_metadata(path: Path) -> None:
    metadata, _ = _front_matter(path)
    missing = REQUIRED_METADATA - metadata.keys()
    assert not missing, f"{path.relative_to(ROOT)}: missing metadata fields: {sorted(missing)}"

    for key in REQUIRED_METADATA:
        assert metadata[key], f"{path.relative_to(ROOT)}: metadata field {key!r} is empty"

    assert metadata["status"] in ALLOWED_STATUSES, f"{path.relative_to(ROOT)}: unknown status {metadata['status']!r}"
    assert metadata["publication"] in ALLOWED_PUBLICATION_STATES, (
        f"{path.relative_to(ROOT)}: unknown publication state {metadata['publication']!r}"
    )

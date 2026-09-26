"""Documentation metadata and visibility contracts."""

from tests.docs._structure_support import (
    ALLOWED_PUBLICATION_STATES,
    ALLOWED_STATUSES,
    DOC_PATHS,
    DOCS_ROOT,
    REQUIRED_METADATA,
    ROOT,
    _front_matter,
)


LANE_AUDIENCE_TERMS = {
    "user": ("users",),
    "developer": ("developers", "maintainers", "contributors"),
}


def test_documentation_pages_declare_valid_publication_metadata() -> None:
    problems: list[str] = []
    for path in DOC_PATHS:
        page = path.relative_to(ROOT)
        metadata, _ = _front_matter(path)
        missing = REQUIRED_METADATA - metadata.keys()
        if missing:
            problems.append(f"{page}: missing metadata fields: {sorted(missing)}")
        problems.extend(
            f"{page}: metadata field {key!r} is empty"
            for key in sorted(REQUIRED_METADATA)
            if key in metadata and not metadata[key]
        )
        if metadata.get("status") not in ALLOWED_STATUSES:
            problems.append(f"{page}: unknown status {metadata.get('status')!r}")
        if metadata.get("publication") not in ALLOWED_PUBLICATION_STATES:
            problems.append(f"{page}: unknown publication state {metadata.get('publication')!r}")

        lane = path.relative_to(DOCS_ROOT).parts[0]
        audience = metadata.get("audience", "")
        if lane in LANE_AUDIENCE_TERMS and not any(term in audience for term in LANE_AUDIENCE_TERMS[lane]):
            problems.append(f"{page}: audience {audience!r} does not name the {lane} lane's readers")
        if lane == "user" and "maintainers" in audience:
            problems.append(f"{page}: user-lane page addresses maintainers")

    assert not problems, "\n".join(problems)

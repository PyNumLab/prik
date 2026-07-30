"""Regenerate C semantic `.pyi` fixtures from their native source projects."""

from tests.c._support.fixture_outputs import (
    C_PYI_FIXTURE_DIR,
    c_pyi_text_for_fixture_project,
    iter_general_c_fixture_projects,
)


def main() -> None:
    C_PYI_FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    for project_key, fixtures in iter_general_c_fixture_projects():
        output = (C_PYI_FIXTURE_DIR / project_key).with_suffix(".pyi")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(
            c_pyi_text_for_fixture_project(project_key, fixtures) + "\n",
            encoding="utf-8",
        )
        print(f"updated {output}")


if __name__ == "__main__":
    main()

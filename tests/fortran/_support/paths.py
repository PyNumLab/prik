"""Directory anchors for tests that read a file owned by another directory.

Computing `Path(__file__).parents[N]` couples a test to its own depth in the
tree, so moving it silently resolves the path to the wrong directory instead of
failing. Import the anchor that names what is wanted.
"""

from pathlib import Path

FORTRAN_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = FORTRAN_ROOT.parents[1]
PARSER_FIXTURE_ROOT = FORTRAN_ROOT / "infrastructure" / "parsing" / "fixtures"
GENERAL_FORTRAN_DIR = PARSER_FIXTURE_ROOT / "general"

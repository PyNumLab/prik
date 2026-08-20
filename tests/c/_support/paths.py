"""Directory anchors for tests that read a file owned by another directory.

Computing `Path(__file__).parents[N]` couples a test to its own depth in the
tree, so moving it silently resolves the path to the wrong directory instead of
failing. Import the anchor that names what is wanted.
"""

from pathlib import Path

C_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = C_ROOT.parents[1]
C_DATA_DIR = C_ROOT / "fixtures" / "native"
PARSER_FIXTURE_ROOT = C_ROOT / "fixtures" / "parser"

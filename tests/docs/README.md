# Documentation Tests

This top-level feature owns repository documentation metadata, visibility,
navigation, executable examples, publication, user-content journeys, and
public reference/source-map synchronization.

Each pytest module owns one documentation invariant family. Shared parsing
facts live in `_structure_support.py`; unrelated repository architecture,
workflow, and product behavior tests do not belong here.

Run this owner independently with:

```bash
python3 -m pytest -q tests/docs
```

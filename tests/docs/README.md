# Documentation Tests

This top-level feature owns documentation publication metadata, visibility,
link integrity, executable examples, and synchronization with public CLI,
Python API, and feature-support contracts.

Developer package-guide commands are discovered with their displayed results.
The page is the sole expected-output source; there is no parallel test-file
inventory to update when an example is added, removed, or reworded.

The suite does not freeze prose, headings, reading order, page inventories,
private names, or the source-tree layout. Those are review concerns unless a
tool consumes the structure directly. Shared parsing facts live in
`_structure_support.py`; workflow and product behavior tests remain with their
own owners.

Run this owner independently with:

```bash
python3 -m pytest -q tests/docs
```

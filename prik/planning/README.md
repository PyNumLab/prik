# Planning Package

This package projects policy-completed semantic IR into one editable,
backend-neutral wrapper plan.

| File | Owns |
| --- | --- |
| `models.py` | Typed wrapper-plan records shared by all generated backends. |
| `planner.py` | Mechanical projection from completed policy into those records. |

Planning must not infer semantic policy or render output text. Python-facing
docstrings, C, Fortran, headers, and the generated Python class facade are
rendered by `../codegen/` from the completed plan.

For cross-stage navigation, see `docs/developer/source-map.md` and
`docs/developer/feature-to-code-map.md`.

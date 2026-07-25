---
title: Error Handling & Diagnostics
description: How x2py reports errors at different stages and how to diagnose them
audience: users, advanced users
prerequisites: common beginner workflow, data types
related: ../reference/diagnostic-codes.md, ../troubleshooting/index.md, callbacks.md
status: maintained
publication: reviewed
---

# Error Handling & Diagnostics

x2py reports failures at several distinct stages. Understanding which stage failed helps you know where to look and what to fix.

---

## Failure Stages

| Stage                        | Typical Cause                                      | What to do |
|-----------------------------|----------------------------------------------------|----------|
| Preprocessing / Parsing     | Syntax x2py can't model, missing include           | Check the diagnostic code and source location |
| Semantic Conversion         | Unresolved types, missing contract facts           | Fix source or edit the generated `.pyi` |
| Policy Completion & Planning| Unsupported ownership, layout, callback, etc.      | Read the full error message — it points to the problematic declaration |
| Compilation / Linking       | Compiler issues, missing modules/libraries         | Run with `--verbose` to see native commands |
| Import                      | Missing shared library, ABI mismatch               | Check paths and environment |
| Python Call                 | Wrong dtype, shape, layout, class, etc.            | Match the generated contract |
| Native Execution            | Application-level status (e.g. error code)         | Use `@raises` projection or handle manually |
| Callback / Fatal            | Exception in callback, `stop`, `error stop`        | Process usually aborts |

---

## Status Projection Example

You can turn Fortran status codes into Python exceptions using the `@raises` decorator in an edited contract.

**Example:**

```fortran
subroutine solve(value, status, message)
  integer(4), intent(in) :: value
  integer(4), intent(out) :: status
  character(len=32), intent(out) :: message
  ...
end subroutine
```

In your edited `.pyi`:

```python
@raises(status="status", message="message", success=0)
def solve(value: Int32) -> None: ...
```

Then:

```python
try:
    api.solve(np.int32(-1))
except RuntimeError as e:
    print(e)          # "negative input"
```

---

## Common Python Exceptions

- `TypeError` — Wrong dtype, rank, shape, layout, class, or callback
- `ValueError` — Invalid options or contract values
- `RuntimeError` — Native status projected as exception
- `ImportError` / `OSError` — Extension loading problems

---

## Best Practices

- Always start with the **full error message** — it usually tells you exactly what went wrong.
- Use `--verbose` when investigating build failures.
- For complex contracts, generate the `.pyi` first and inspect it.
- Run risky or untrusted callbacks in a subprocess if you need the main process to survive failures.

---

## Next

- [Editing Semantic `.pyi` Contracts](editing-semantic-pyi-contracts.md)
- Check the [Diagnostic Codes](../reference/diagnostic-codes.md) reference for detailed error categories

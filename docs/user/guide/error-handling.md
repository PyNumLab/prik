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
| Parsing                     | Syntax x2py cannot model, missing include           | Check the diagnostic code and source location |
| Interface conversion        | Unresolved types or missing interface details       | Fix the source or edit the generated `.pyi` |
| Wrapper planning            | Unsupported storage, layout, or callback combination | Read the full error message; it points to the declaration |
| Compilation / Linking       | Compiler issues, missing modules/libraries         | Run with `--verbose` to see native commands |
| Import                      | Missing library or incompatible build tools        | Check paths and environment |
| Python Call                 | Wrong dtype, shape, layout, class, etc.            | Match the generated contract |
| Native Execution            | Application-level status, such as an error code    | Convert it with `@raises` or handle it manually |
| Callback / Fatal            | Exception in callback, `stop`, `error stop`        | Process usually aborts |

---

## Verbose Output And Tracebacks

Use the two diagnostic flags for different problems:

| Flag | Use it when |
| --- | --- |
| `--verbose` | A build or link fails and you need the generated files, build steps, timings, or compiler commands. |
| `--debug` | x2py fails unexpectedly and you need the full Python traceback. |

`--verbose` keeps the normal concise error message. `--debug` exposes x2py's
internal call stack, so it is mainly useful when reporting or investigating an
x2py bug.

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
import numpy as np

try:
    api.solve(np.int32(-1))
except RuntimeError as e:
    print(e)
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
- Use `--debug` only when an unexpected x2py failure requires a Python
  traceback.
- For complex contracts, generate the `.pyi` first and inspect it.
- Run risky or untrusted callbacks in a subprocess if you need the main process to survive failures.

---

## Next

- Finish with [Building the Shared Library](building-shared-library.md).
- [Editing Semantic `.pyi` Contracts](../reference/editing-semantic-pyi-contracts.md)
- Check the [Diagnostic Codes](../reference/diagnostic-codes.md) reference for
  detailed error categories.

---
title: Error Handling & Diagnostics
description: How prik reports errors at different stages and how to diagnose them
audience: users, advanced users
prerequisites: common beginner workflow, data types
related: callbacks.md
status: maintained
publication: reviewed
---

# Error Handling & Diagnostics

prik reports failures at several distinct stages. Understanding which stage failed helps you know where to look and what to fix.

---

## Failure Stages

| Stage                        | Typical Cause                                      | What to do |
|-----------------------------|----------------------------------------------------|----------|
| Parsing                     | Syntax prik cannot model, missing include           | Check the diagnostic code and source location |
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
| `--debug` | prik fails unexpectedly and you need the full Python traceback. |

`--verbose` keeps the normal concise error message. `--debug` exposes prik's
internal call stack, so it is mainly useful when reporting or investigating an
prik bug.

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

In your edited `.pyi`, project the hidden native outputs and then name those
projected results in `@raises`:

```python
from prik.contracts import Addr, Arg, Int32, Return, String, native_call, raises

@raises(status="status", message="message", success=0)
@native_call([Addr(Arg(0)), Return("status", 0), Return("message", 1)])
def solve(value: Int32) -> tuple[Int32, String[32]]: ...
```

Then:

```python
import numpy as np

try:
    api.solve(np.int32(-1))
except RuntimeError as e:
    print(e)
```

prik uses the projected status and message to determine the Python result: a
successful call returns `None`, while a non-success status raises
`RuntimeError` with the native message instead of returning either hidden
output.

For the complete status and message rules, see
[Translate Status Results into Exceptions](../reference/pyi-contracts/calls-and-results.md#translate-status-results-into-exceptions).

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
- Use `--debug` only when an unexpected prik failure requires a Python
  traceback.
- For complex contracts, generate the `.pyi` first and inspect it.
- Run risky or untrusted callbacks in a subprocess if you need the main process to survive failures.

---

## Next

- Finish with [Building the Shared Library](building-shared-library.md).

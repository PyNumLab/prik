# C Library Examples

These maintained projects generate Python bindings from public C declarations
and link the extension to an existing compiled library. The library's
implementation source files are not inputs to the PRIK wrapper build.

| Project | Declaration input | Linked implementation | Validated surface |
| --- | --- | --- | --- |
| [libm](libm/README.md) | Platform `<math.h>` | Platform math library | 60 target-generated ISO C99 functions |
| [TA-Lib](ta_lib/README.md) | TA-Lib `ta_libc.h` | Pinned `libta-lib` v0.7.1 | All 322 double and float-input indicators |

Each project README explains how the declaration inventory, reviewed contract,
native library, and numerical checks fit together. Run commands from the
repository root.

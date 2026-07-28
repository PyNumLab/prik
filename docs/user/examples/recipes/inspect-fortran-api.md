---
title: Inspect A Fortran API
audience: users, developers
prerequisites: basic wrapper tutorial
related: ../../reference/semantic-pyi-format.md
status: maintained
publication: draft
---

# Inspect A Fortran API

Use this recipe when you want to understand a Fortran declaration before
building a wrapper.

## Input

<!-- x2py-doc-source: tests/data/fortran/general/basic_subroutine.f90 -->
```fortran
module m1
contains
subroutine add1(n, x)
  integer, intent(in) :: n
  real(kind=8), intent(inout), dimension(n) :: x
end subroutine add1
end module m1
```

## Parse Source Facts

<!-- x2py-doc-test: exact -->
```bash
python3 -m x2py parse tests/data/fortran/general/basic_subroutine.f90
```

Expected output:

<!-- x2py-doc-test-output -->
```text
File: tests/data/fortran/general/basic_subroutine.f90
  Modules: 1
    - module m1 (vars=0, uses=0)
      Procedures: 1
        - subroutine add1(n:integer[0], x:real(8)[1])
```

## Generate Semantic `.pyi`

<!-- x2py-doc-test: exact -->
```bash
python3 -m x2py generate --pyi tests/data/fortran/general/basic_subroutine.f90
```

Expected output:

<!-- x2py-doc-test-output -->
```python
File: tests/data/fortran/general/basic_subroutine.f90
Root contract: basic_subroutine/basic_subroutine.pyi
from . import m1

Module contract: m1.pyi
from x2py.contracts import Addr, Arg, Float64, Int32, native_call

@native_call([Addr(Arg(0)), Arg(1)])
def add1(
    n: Int32,
    x: Float64[n]
) -> None: ...
```

## Notes

- Parser output is source facts, not wrapper policy.
- `.pyi` output is the editable semantic contract.
- The default wrapper build reports unsupported completed policies while it
  builds the wrapper plan.

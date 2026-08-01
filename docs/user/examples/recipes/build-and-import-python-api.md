---
title: Build And Import With The Python API
audience: users, developers
prerequisites: basic wrapper tutorial, supported compiler toolchain
related: ../../reference/python-api.md
status: maintained
publication: draft
---

# Build And Import With The Python API

Use this recipe when a Python script needs to build a wrapper and load the
generated extension directly.

`build_fortran_extension` returns a result object with the module name, shared
library path, generated source paths, and other build artifacts.

<!-- prik-doc-test: exact -->
```python
from importlib.util import module_from_spec, spec_from_file_location
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np

from prik import build_fortran_extension

source = Path("tests/fortran/building_shared_library/end_to_end/fixtures/native/fruntime_abi_f90.f90")
with TemporaryDirectory() as output_dir:
    build = build_fortran_extension(source, output_dir=output_dir)
    spec = spec_from_file_location(build.module_name, build.shared_library)
    module = module_from_spec(spec)
    spec.loader.exec_module(module)
    native_module = module.fruntime_abi_f90

    print(build.module_name)
    print(native_module.scale(np.float64(3.0), np.float64(2.5)))
```

Expected output:

<!-- prik-doc-test-output -->
```text
fruntime_abi_f90
7.5
```

## Notes

- This pattern avoids editing `sys.path`.
- `TemporaryDirectory` keeps documentation and tests from leaving build
  artifacts in the checkout.
- Use the returned artifact paths when debugging generated code.

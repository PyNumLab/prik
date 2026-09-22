# Wrap PRIMA with PRIK

Build the bundled modern [libPRIMA](https://github.com/libprima/prima)
implementation as a static library, extract a reviewed five-solver contract,
and link one Python extension without compiling any PRIMA source twice.

## Requirements

Install CMake and GNU Fortran. On Ubuntu:

```console
sudo apt-get update
sudo apt-get install --yes cmake gfortran
```

Run the remaining commands from the PRIK repository root.

## Build and test

```bash
source examples/fortran/prima/build_all.sh
python3 -m pytest -q examples/fortran/prima/tests
```

The example publishes `bobyqa`, `cobyla`, `lincoa`, `newuoa`, and `uobyqa`
in their native module namespaces. Required objective callbacks, optional
progress callbacks, and optional arguments inside progress callbacks are
preserved in the generated contract.

## How the build works

CMake compiles all 55 implementation sources once into position-independent
`libprimaf.a`. PRIK analyzes the same source universe with
[`export_symbols.txt`](export_symbols.txt), generating contracts only for the
five selected solvers and their shared callback prototypes. The wrapper build
then reads those contracts and links the existing archive.

```text
55 Fortran sources -> libprimaf.a
                  \
                   -> selected .pyi contract -> PRIK wrapper -> prik_prima
```

`PRIMA_REAL_PRECISION=64` and `PRIMA_INTEGER_KIND=0` are used for both native
compilation and contract extraction, so the contract and archive describe the
same ABI.

## Sources and license

The files under `native/` match the maintained Fortran target at
[libprima/prima commit `1d76fb88aeffb427cd17ed1e9d0d3b34f414913f`](https://github.com/libprima/prima/tree/1d76fb88aeffb427cd17ed1e9d0d3b34f414913f).
See [`LICENCE.txt`](LICENCE.txt) for the upstream BSD 3-Clause license.

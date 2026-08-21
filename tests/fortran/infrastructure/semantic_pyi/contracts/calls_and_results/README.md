# `.pyi` Calls and Results

This feature owns the executable contract for
[`.pyi` Calls and Results](../../../../../../docs/user/reference/pyi-contracts/calls-and-results.md).
It covers direct native-order arguments, reordered and hidden native slots,
projected scalar/string/array/derived results, immutable replacement returns,
and runtime shape checks selected by edited contracts.

Evidence is split by the stage that establishes it:

- `policy/` checks that projection, mutation, storage, and GIL decisions are
  complete before wrapper planning;
- `codegen/` checks that reordered slots, hidden results, and
  replacement writeback dispatch through their selected plan paths; and
- `end_to_end/` builds source-free edited contracts against explicit native
  objects and verifies native-order calls, projections, immutable
  replacements, and hidden array allocation.

The complete `@native_call` grammar and its loader diagnostics remain with
`semantic_pyi_format/`. Dtype, rank, layout, writeability, byte-order,
alignment, zero-size, and optional-state matrices remain with Arrays and
Optional Arguments. Status-to-exception and GIL behavior reuse Error Handling;
descriptor, pointer, and callback projections reuse their respective feature
owners.

Run the focused feature with:

```bash
python3 -m pytest -q tests/fortran/infrastructure/semantic_pyi/contracts/calls_and_results
```

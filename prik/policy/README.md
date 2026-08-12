# Policy Package

This package owns every post-IR semantic decision required before wrapper
planning begins. It may consume semantic IR and raw contract metadata, but it
must not construct wrapper plans or render backend output.

| File | Owns |
| --- | --- |
| `models.py` | Immutable backend-neutral completed-policy vocabulary. |
| `ownership.py` | Ownership, transfer, destruction, storage, and strict lowering-action resolution. |
| `exports.py` | Completed Python export policy. |
| `construction.py` | Wrapper-policy construction rules and completed-policy accessors. |
| `completion.py` | Ordered completion and attachment of policy to semantic IR. |
| `native_array_handles.py` | Completed descriptor-handle policy, ABI dispatch records, and selected build requirements. |

Raw ownership and pointer-contract metadata belongs to
`../semantics/ownership_metadata.py`. Planning consumes completed records from
this package through `../planning/planner.py`.

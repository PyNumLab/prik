---
title: Contributing Workflow
audience: developers, maintainers, contributors
prerequisites: repository checkout, Python 3.10 or newer
related: ../architecture.md, quality-assurance.md, ../testing-strategy.md, documentation.md
status: maintained
publication: reviewed
---

# Contributing Workflow

This is the practical workflow for changing PRIK. The root
[`CONTRIBUTING.md`](../../../CONTRIBUTING.md) is the short public entrypoint;
this page supplies the complete contributor sequence without duplicating
package architecture.

## Prepare The Checkout

```bash
python3 -m pip install -e ".[qa]"
git config core.hooksPath .githooks
```

Create a focused branch and begin with the smallest test owner for the
behavior. Do not start with the full suite while discovering the change.

## Change Workflow

1. Identify the public behavior, limitation, or internal invariant.
2. Use the [architecture guide](../architecture.md),
   [source map](../source-map.md), or
   [feature-to-code map](../feature-to-code-map.md) to find its owner.
3. Read the owning package guide and relevant user contract before editing.
4. Update the documentation contract first when public behavior, ownership,
   or limitations change.
5. Add or update focused tests at the earliest stage that proves the behavior.
6. Implement the change in the owning stage and extend downstream stages only
   when their representation or mechanism genuinely changes.
7. Run focused verification, then the required static and broader checks.
8. Add a concise **Unreleased** changelog entry for visible behavior,
   workflows, examples, supported features, or limitations.

For policy-sensitive wrapper work, semantic decisions must be complete before
planning. A binding or bridge change should implement a newly selected plan
mechanism, not infer a new policy from datatype, intent, aliases, or storage.

## Support Evidence Rule

Documentation may claim support only when current implementation and evidence
prove it. Acceptable evidence includes:

- a focused test for the contract;
- a maintained golden that proves exact generated representation;
- a checked repository command using a maintained fixture; or
- a compiled/imported/called runtime test for wrapper behavior.

Parser support does not establish semantic or wrapper support. Compilation
alone does not establish runtime behavior. Unsupported cases should fail at
the earliest stage with enough facts to report a stable diagnostic.

## Documentation Examples

Important production files expose small public-API examples under
`if __name__ == "__main__"`; package guides document their exact commands and
outputs. Their centralized execution owner is
[`test_execution_examples.py`](../../../tests/fortran/infrastructure/execution_examples/test_execution_examples.py).

Markdown snippets use the repository's checked markers:

````markdown
<!-- prik-doc-test: exact -->
```bash
python3 -m prik parse path/to/example.f90
```

<!-- prik-doc-test-output -->
```text
File: path/to/example.f90
...
```
````

Use `prik-doc-test: run` when only successful execution is stable. Use
`prik-doc-source` for fixture-backed source blocks. Do not mark placeholder,
checkout-modifying, compiler-environment-dependent, or intentionally failing
commands as executable documentation.

Run the example documentation checks with:

```bash
python3 -m pytest -q tests/docs/test_examples.py
```

## Selecting Tests

Use the [testing strategy](../testing-strategy.md) for the authoritative
placement rules. Common starting points are:

```bash
python3 -m pytest -q tests/fortran/source_parsing/parsing/
python3 -m pytest -q tests/fortran/semantic_ir/semantics/
python3 -m pytest -q tests/fortran/infrastructure/semantics/
python3 -m pytest -q tests/fortran/infrastructure/codegen/
python3 -m pytest -q tests/fortran/command_line_interface/pipeline/
python3 -m pytest -q tests/docs
```

Use a feature-local `policy/`, `codegen/`, `runtime/`, or `end_to_end/` owner
when the behavior belongs to a documented feature. Compiled tests must import
and call the generated API; build success alone is insufficient.

## Common Change Routes

### Add A Fortran Construct

1. Add the smallest parser example under
   `tests/fortran/source_parsing/parsing/` or the feature's parsing owner.
2. Preserve the new source fact in `prik/parsers/fortran/`; add model fields
   only when downstream consumers need them.
3. Extend `prik/semantics/fortran2ir.py` and semantic tests only if the
   language-neutral contract changes.
4. Complete any new ownership, projection, setter, or support decision in
   `prik/policy/` before planning.
5. Extend the plan and named binding/bridge lowering mechanisms only when the
   completed behavior needs a new representation.
6. Add feature-local codegen and end-to-end evidence, then update the user
   guide and feature matrix.

Regenerate only an intentionally changed Fortran parser fixture:

```bash
python3 tests/fortran/source_parsing/parsing/generate_parser_goldens.py \
  tests/fortran/source_parsing/parsing/fixtures/general/basic_subroutine.f90
```

### Add Semantic `.pyi` Syntax Or Projection

1. Add syntax tests under `tests/fortran/semantic_pyi_format/parsing/`.
2. Change `prik/parsers/pyi/parser.py` only if raw Python AST parsing changes;
   otherwise interpret the syntax in `prik/semantics/pyi2ir.py`.
3. Update `prik/printers/pyi.py` and round-trip tests for emitted syntax.
4. Update semantic models only when the IR needs a new contract fact.
5. Complete new behavior in policy, project it through planning, and add
   runtime evidence when the edit affects wrappers.
6. Update the semantic `.pyi` user reference.

### Add A Code-Generation Backend Or Mechanism

A new backend is not accepted merely because it prints source. It must consume
the completed shared plan without importing construction rules, define its own
typed representation and printer boundary, fail closed on unsupported action
combinations, preserve shared native slots and lifecycle ordering, and provide
focused generation plus compiled/runtime evidence. Add a backend only after
the shared plan can express its requirements without backend-specific semantic
policy.

For a mechanism inside an existing backend, start in the narrow specialized
emitter named by the package guide. Do not replace specialized methods with a
flag-driven generic emitter or move semantic decisions down to make the
mechanism easier to generate.

### Add A Stage-Owned Error

Report a failure at the first stage with enough facts to explain it. Syntax and
source-processing failures belong to preprocessing/parsing; invalid contracts
belong to semantic conversion; unsafe ownership, ABI, projection, or support
belongs to completed policy; inconsistent plan projection belongs to planning;
an unavailable emitted mechanism belongs to backend preflight. Assert the
stable owner path and reason at that stage rather than forcing a known failure
through native compilation.

## Pull Request And Review

Before opening a pull request:

- keep the change focused and remove superseded implementation/tests/docs;
- explain the problem, stage ownership, solution, and verification;
- identify user-visible behavior and limitations;
- run the applicable focused tests and the required checks from
  [Quality Assurance](quality-assurance.md); and
- ensure all required GitHub checks pass before merge.

Review should verify dependency direction, completed-policy authority,
diagnostic ownership, focused and end-to-end evidence, generated ABI stability,
documentation consistency, and removal of obsolete paths. Reviewers should not
accept a compatibility alias for an intentionally moved internal API unless
the change explicitly requires one.

## Contribution License

PRIK is distributed under the MIT License. By submitting a contribution, a
contributor agrees to license it under the same terms and confirms they have
the right to do so, including any required employer authorization.

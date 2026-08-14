---
title: Contributing Workflow
audience: developers, maintainers, contributors
prerequisites: repository checkout, Python 3.10 or newer
related: ../architecture.md, ../codebase-map.md, ../testing-strategy.md, quality-assurance.md, documentation.md
status: maintained
publication: reviewed
---

# Contributing Workflow

This page is the practical path for changing PRIK. The root
[`CONTRIBUTING.md`](../../../CONTRIBUTING.md) is the short public entrypoint.

## Prepare The Checkout

```bash
python3 -m pip install -e ".[qa]"
git config core.hooksPath .githooks
```

Create a focused branch. Start with the smallest test owner for the behavior,
not the full suite.

## Change Workflow

1. Define the behavior, limitation, diagnostic, or internal invariant.
2. Find its owner through the [architecture guide](../architecture.md),
   [codebase map](../codebase-map.md), or
   [feature-to-code map](../feature-to-code-map.md). Read the owning package
   guide and any relevant user contract.
3. Update the documentation contract first when public behavior, ownership, or
   limitations change.
4. Add or update focused evidence at the earliest stage that can prove the
   behavior.
5. Change the owning stage. Extend later stages only when their representation
   or mechanism must change.
6. Run focused verification, then the checks required by
   [Quality Assurance](quality-assurance.md).
7. Add an **Unreleased** changelog entry for visible behavior, supported
   features, examples, workflows, or limitations.

For wrapper work, policy must complete every semantic decision before planning.
Binding and bridge code implement the selected plan; they do not infer policy
from datatype, intent, aliases, or storage.

## Evidence And Documentation

Documentation may claim support only when implementation and evidence prove it.
Parser evidence does not establish semantic or wrapper support, and compilation
does not establish runtime behavior. A public wrapper claim needs a build,
import, call, and observable result. Unsupported input should fail at the first
stage with enough facts for a stable diagnostic.

Architecture component guides may show a production-file command and
representative result.
The documentation suite runs those pairs and uses the page as the expected
output. Stable output is exact; excerpts and target-dependent output are
checked only for the facts shown. See
[Documentation maintenance](documentation.md) when adding executable Markdown
examples.

Use the [testing strategy](../testing-strategy.md) for test ownership. Keep
user-visible behavior in its feature owner, not `infrastructure/`. A compiled
test must import and call the generated API; build success alone is not enough.

## Stage Boundaries

Add a source fact in parsing, its language-neutral meaning in semantics, and
ownership or support decisions in policy. Planning projects completed policy;
code generation, printing, and compilation implement that projection. Put a
new diagnostic at the first stage that can explain it. The architecture and
architecture component guides describe these boundaries in detail.

## Pull Request

Keep the pull request focused. Describe the problem, owner, behavior change,
and verification; identify user-visible limitations. Remove superseded code,
tests, and documentation. The hosted checks are summarized in
[Pull request checks](ci.md).

## Contribution License

PRIK is distributed under the MIT License. By submitting a contribution, a
contributor agrees to license it under the same terms and confirms they have
the right to do so, including any required employer authorization.

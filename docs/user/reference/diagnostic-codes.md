---
title: Diagnostic Codes
audience: users, developers
prerequisites: error handling
related: index.md, ../troubleshooting/index.md
status: maintained
publication: draft
---

# Diagnostic Codes

Diagnostic codes are stable category identifiers for users, tests, and tooling.
They are not source line numbers, occurrence counters, or process exit statuses.

Categories use explicit symbolic names such as `PARSE_INVALID_SYNTAX` and
`C_UNRESOLVED_INCLUDE`. The name describes the failure class directly.

## Fatal Parser Errors

Fatal parser errors stop parsing and are rendered by the CLI without a Python
traceback unless `--debug` is used.

| Code | Frontend | Meaning |
| --- | --- | --- |
| `PARSE_ERROR` | Fortran | Fallback for a manually constructed or defensive Fortran parse error without a narrower category. |
| `PARSE_INVALID_SYNTAX` | Fortran | Syntax cannot be consumed in a modeled Fortran grammar region. |
| `PARSE_WRONG_ENTRYPOINT` | Fortran | A singular public parser API was called for a different source-unit kind. |
| `PARSE_AMBIGUOUS_ENTRYPOINT` | Fortran | A singular public parser API matched more than one source unit. |
| `PARSE_EXPECTED_UNIT` | Fortran | An internal unit visitor received the wrong source-unit kind. |
| `PARSE_MISSING_UNIT_END` | Fortran | A source unit has no closing statement. |
| `PARSE_MISMATCHED_UNIT_END` | Fortran | A named source-unit closing statement does not match its opener. |
| `PARSE_UNEXPECTED_UNIT_END` | Fortran | A closing statement appears while another nested unit is active. |
| `PARSE_DUPLICATE_UNIT` | Fortran | A scope contains duplicate named source units of the same kind. |
| `PARSE_DUPLICATE_PROCEDURE` | Fortran | A scope contains duplicate procedure names. |
| `PARSE_MALFORMED_HEADER` | Fortran | A module or procedure header is unsupported or malformed. |
| `PARSE_UNSUPPORTED_RESULT_TYPE` | Fortran | A function header contains an unsupported result-type prefix. |
| `PARSE_DUPLICATE_DECLARATION` | Fortran | A procedure symbol is declared more than once. |
| `PARSE_UNKNOWN_PARAMETER_TYPE` | Fortran | A `PARAMETER` symbol has no declared type where one is required. |
| `PARSE_DUPLICATE_PARAMETER` | Fortran | A procedure contains duplicate `PARAMETER` declarations. |
| `PARSE_DUPLICATE_SYMBOL` | Fortran | A file or project scope contains a duplicate symbol. |
| `PARSE_UNSUPPORTED_OPENMP_DIRECTIVE` | Fortran | A modeled specification region contains an unsupported OpenMP directive. |
| `PARSE_MISSING_DERIVED_TYPE_END` | Fortran | A derived-type declaration has no matching closing statement. |
| `PARSE_EXECUTABLE_IN_SPECIFICATION` | Fortran | An executable statement appears in a non-executable specification region. |
| `PARSE_UNSUPPORTED_DECLARATION` | Fortran | A declaration-shaped line uses an unsupported datatype form. |
| `PARSE_UNSUPPORTED_TYPE_BOUND_DECLARATION` | Fortran | A derived-type `contains` region has an unsupported binding declaration. |
| `PARSE_UNRESOLVED_ARGUMENT_TYPE` | Fortran | A defensive invariant could not apply a declared argument type. |
| `PARSE_UNKNOWN_FUNCTION_RESULT_TYPE` | Fortran | A function result has no resolvable datatype. |
| `PARSE_IMPLICIT_NONE_UNDECLARED_SYMBOL` | Fortran | `implicit none` requires a missing argument or result declaration. |
| `PARSE_MISSING_FUNCTION_RESULT` | Fortran | A defensive invariant found a function without a result variable. |
| `PARSE_RESULT_SHADOWS_ARGUMENT` | Fortran | A function result name shadows an argument. |
| `PARSE_DUPLICATE_VARIABLE` | Fortran | A module-like scope contains conflicting duplicate variable declarations. |
| `PARSE_UNKNOWN_VARIABLE_TYPE` | Fortran | A module variable still has an unknown datatype after parsing. |
| `PARSE_DUPLICATE_FIELD` | Fortran | A derived type contains duplicate fields. |
| `PARSE_UNKNOWN_FIELD_TYPE` | Fortran | A derived-type field still has an unknown datatype after parsing. |
| `PARSE_DUPLICATE_ARGUMENT` | Fortran | A procedure argument list repeats a name. |
| `PARSE_PREPROCESSING_REQUIRED` | Fortran | Raw CPP directives require compiler preprocessing before parser entry. |
| `PARSE_INTERNAL_STATE` | Fortran | A defensive internal parser invariant was violated. |

<!-- X2PY_C_DOCS_START
| `CPARSE_ERROR` | C | Fallback for a manually constructed or defensive C parse error without a narrower category. |
| `CPARSE_PREPROCESSING_REQUIRED` | C | Raw preprocessing directives require compiler preprocessing before parser entry. |
| `CPARSE_UNSUPPORTED_KNR_DEFINITION` | C | Unsupported K&R-style function definition. |
| `CPARSE_INVALID_SPECIFIER_SEQUENCE` | C | Invalid C primitive-specifier sequence. |
| `CPARSE_INVALID_SYNTAX` | C | Syntax cannot be consumed in a modeled C grammar region. |
X2PY_C_DOCS_END -->

## Preprocessing Diagnostics

Compiler-backed preprocessing failures are rendered by the CLI without a
Python traceback unless `--debug` is used. They occur before the parser consumes
the expanded source.

| Code | Meaning |
| --- | --- |
| `PREPROCESSOR_NOT_FOUND` | The configured compiler/preprocessor executable could not be started. |
| `PREPROCESSOR_FAILED` | The compiler/preprocessor returned a non-zero status, timed out, or could not be executed. Compiler stderr is preserved. |
| `INVALID_COMPILER_ARGUMENTS` | The preprocessing configuration is invalid, such as a malformed macro name or unusable compile database entry. |
| `UNSUPPORTED_COMPILER_CAPABILITY` | The selected adapter was asked for metadata it cannot provide. |
| `PROVENANCE_UNAVAILABLE` | Expanded source was produced, but the adapter cannot provide accurate source mappings. |
| `INCLUDE_NOT_FOUND` | A native Fortran `include "..."` target could not be resolved or read. |
| `INCLUDE_CYCLE` | Recursive native Fortran INCLUDE expansion found a cycle. |

## Wrapper Planning Errors

Wrapper planning errors are emitted by the default wrapper build after semantic
policy completion. The owner path identifies the declaration whose completed
policy has no supported lowering.

Reasons identify a missing completed policy or an unsupported
completed-policy combination. These are build-stage diagnostics rather than a
separate inspection report; see
[Error Handling](../guide/error-handling.md#wrapper-planning-errors) for the
repair workflow.

<!-- X2PY_C_DOCS_START
## C Report Diagnostics
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
The C parser can preserve partial metadata and attach `CDiagnostic` records.
These records do not necessarily stop parsing; inspect each diagnostic's
`severity`.
X2PY_C_DOCS_END -->

<!-- X2PY_C_DOCS_START
| Code | Meaning |
| &#45;&#45;- | &#45;&#45;- |
| `C_UNRESOLVED_INCLUDE` | A local include could not be resolved. |
| `C_UNMODELED_COMPILER_EXTENSION` | Compiler syntax was accepted for declaration extraction, but ABI-, layout-, type-, or symbol-relevant extension semantics remain unmodeled. |
| `C_UNSUPPORTED_DECLARATION` | Recognized declaration form is outside the modeled subset. |
| `C_UNSUPPORTED_DECLARATOR` | Declarator form is outside the modeled subset. |
| `C_UNSUPPORTED_FIELD_DECLARATION` | Aggregate field form is outside the modeled subset. |
| `C_INVALID_FLEXIBLE_ARRAY_MEMBER` | Flexible array member placement is invalid. |
| `C_UNION_BY_VALUE` | A function uses a union by value and needs wrapper policy review. |
| `C_TYPEDEF_CYCLE` | Typedef resolution found a cycle. |
| `C_CONFLICTING_FUNCTION_DECLARATION` | Function declarations conflict. |
| `C_DUPLICATE_FUNCTION_DEFINITION` | Function has more than one definition. |
| `C_CONFLICTING_VARIABLE_DECLARATION` | File-scope variable declarations conflict. |
| `C_DUPLICATE_VARIABLE_DEFINITION` | File-scope variable has more than one definition. |
| `C_CONFLICTING_TYPEDEF` | Typedef declarations conflict. |
| `C_DUPLICATE_TAG_DEFINITION` | Struct, union, or enum tag has more than one definition. |
X2PY_C_DOCS_END -->

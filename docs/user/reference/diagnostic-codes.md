---
title: Diagnostic Codes
audience: users, developers
prerequisites: error handling
related: index.md, ../troubleshooting/index.md
status: maintained
publication: draft
---

# Diagnostic Codes

When prik rejects your source, it prints a stable code in brackets. Look that
code up here to find out what class of problem it is.

```text
points.f90:5:1: error[PARSE_MISSING_UNIT_END]: Missing end module for module 'points'.
  |
5 | module points
  | ^
```

The code is a category identifier — not a line number, a counter, or an exit
status. Codes are stable across releases, so you can match on them in scripts
and tests.

Add `--debug` to any command to re-raise the failure with a Python traceback.
Add `--no-color` if the highlighting is hard to read.

## Parser errors

These stop parsing. All are Fortran-frontend codes.

### Unit and block structure

A source unit or block is not closed correctly, or contains something that
cannot appear where it does.

| Code | Meaning |
| --- | --- |
| `PARSE_INVALID_SYNTAX` | Syntax cannot be consumed in a modeled grammar region. |
| `PARSE_MISSING_UNIT_END` | A source unit has no closing statement. |
| `PARSE_MISMATCHED_UNIT_END` | A named closing statement does not match its opener. |
| `PARSE_UNEXPECTED_UNIT_END` | A closing statement appears while another nested unit is active. |
| `PARSE_MISSING_DERIVED_TYPE_END` | A derived-type declaration has no matching closing statement. |
| `PARSE_EXECUTABLE_IN_SPECIFICATION` | An executable statement appears in a specification region. |

### Duplicate names

The same name is declared twice where prik needs one definition.

| Code | Meaning |
| --- | --- |
| `PARSE_DUPLICATE_UNIT` | A scope contains duplicate named source units of the same kind. |
| `PARSE_DUPLICATE_PROCEDURE` | A scope contains duplicate procedure names. |
| `PARSE_DUPLICATE_DECLARATION` | A procedure symbol is declared more than once. |
| `PARSE_DUPLICATE_SYMBOL` | A file or project scope contains a duplicate symbol. |
| `PARSE_DUPLICATE_PARAMETER` | A procedure contains duplicate `PARAMETER` declarations. |
| `PARSE_DUPLICATE_VARIABLE` | A module-like scope contains conflicting duplicate variable declarations. |
| `PARSE_DUPLICATE_FIELD` | A derived type contains duplicate fields. |
| `PARSE_DUPLICATE_ARGUMENT` | A procedure argument list repeats a name. |

### Unresolved types

prik could not determine a datatype it needs. Adding an explicit declaration
usually fixes these.

| Code | Meaning |
| --- | --- |
| `PARSE_IMPLICIT_NONE_UNDECLARED_SYMBOL` | `implicit none` requires a missing argument or result declaration. |
| `PARSE_UNKNOWN_PARAMETER_TYPE` | A `PARAMETER` symbol has no declared type where one is required. |
| `PARSE_UNKNOWN_VARIABLE_TYPE` | A module variable still has an unknown datatype after parsing. |
| `PARSE_UNKNOWN_FIELD_TYPE` | A derived-type field still has an unknown datatype after parsing. |
| `PARSE_UNKNOWN_FUNCTION_RESULT_TYPE` | A function result has no resolvable datatype. |
| `PARSE_UNRESOLVED_ARGUMENT_TYPE` | A declared argument type could not be applied. |

### Unsupported forms

The syntax is valid Fortran, but outside the modeled subset. Check the
[language feature matrix](../language-support/feature-matrix.md).

| Code | Meaning |
| --- | --- |
| `PARSE_MALFORMED_HEADER` | A module or procedure header is unsupported or malformed. |
| `PARSE_UNSUPPORTED_DECLARATION` | A declaration-shaped line uses an unsupported datatype form. |
| `PARSE_UNSUPPORTED_RESULT_TYPE` | A function header contains an unsupported result-type prefix. |
| `PARSE_UNSUPPORTED_TYPE_BOUND_DECLARATION` | A derived-type `contains` region has an unsupported binding declaration. |
| `PARSE_UNSUPPORTED_OPENMP_DIRECTIVE` | A modeled specification region contains an unsupported OpenMP directive. |
| `PARSE_MISSING_FUNCTION_RESULT` | A function has no result variable. |
| `PARSE_RESULT_SHADOWS_ARGUMENT` | A function result name shadows an argument. |

### Preprocessing required

| Code | Meaning |
| --- | --- |
| `PARSE_PREPROCESSING_REQUIRED` | Raw CPP directives need compiler preprocessing before the parser runs. |

### API misuse and internal invariants

You will normally see these only when calling the parser API directly.

| Code | Meaning |
| --- | --- |
| `PARSE_WRONG_ENTRYPOINT` | A singular parser API was called for a different source-unit kind. |
| `PARSE_AMBIGUOUS_ENTRYPOINT` | A singular parser API matched more than one source unit. |
| `PARSE_EXPECTED_UNIT` | An internal unit visitor received the wrong source-unit kind. |
| `PARSE_INTERNAL_STATE` | A defensive internal parser invariant was violated. |
| `PARSE_ERROR` | Fallback for a parse error with no narrower category. |

<!-- PRIK_C_DOCS_START
### C parser errors
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
| Code | Meaning |
| &#45;&#45;- | &#45;&#45;- |
| `CPARSE_INVALID_SYNTAX` | Syntax cannot be consumed in a modeled C grammar region. |
| `CPARSE_PREPROCESSING_REQUIRED` | Raw preprocessing directives require compiler preprocessing before parser entry. |
| `CPARSE_UNSUPPORTED_KNR_DEFINITION` | Unsupported K&R-style function definition. |
| `CPARSE_INVALID_SPECIFIER_SEQUENCE` | Invalid C primitive-specifier sequence. |
| `CPARSE_ERROR` | Fallback for a C parse error with no narrower category. |
PRIK_C_DOCS_END -->

## Preprocessing errors

These happen before the parser sees the source, while running the compiler as a
preprocessor. Compiler stderr is preserved in the message.

```text
<preprocessor>: error[PREPROCESSOR_NOT_FOUND]: preprocessor not found: nosuchcompiler
```

| Code | Meaning |
| --- | --- |
| `PREPROCESSOR_NOT_FOUND` | The configured compiler or preprocessor could not be started. |
| `PREPROCESSOR_FAILED` | The preprocessor returned a non-zero status, timed out, or could not run. |
| `INVALID_COMPILER_ARGUMENTS` | The preprocessing configuration is invalid, such as a malformed macro name. |
| `UNSUPPORTED_COMPILER_CAPABILITY` | The selected adapter was asked for metadata it cannot provide. |
| `PROVENANCE_UNAVAILABLE` | Source expanded, but the adapter cannot provide accurate source mappings. |
| `INCLUDE_NOT_FOUND` | A Fortran `include "..."` target could not be resolved or read. |
| `INCLUDE_CYCLE` | Recursive Fortran `INCLUDE` expansion found a cycle. |

## Wrapper planning errors

These come from the wrapper build, after the source parsed and its semantic
policy completed. **They do not carry a bracketed code.** Instead they name the
declaration and the specific policy that has no supported lowering:

```text
prik: error: Semantic function 'm3.make' has unsupported wrapper policy:
result is an unsupported array of derived values; result has no completed
bridge data action
```

The quoted owner path locates the declaration. The reasons after the colon
identify a missing completed policy or an unsupported combination of completed
policies. Either reshape the native declaration, or check whether the form is
supported at all in the
[language feature matrix](../language-support/feature-matrix.md).

See [Error Handling](../guide/error-handling.md) for the repair workflow and
how these map to Python exceptions at runtime.

<!-- PRIK_C_DOCS_START
## C report diagnostics
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
The C parser can preserve partial metadata and attach `CDiagnostic` records.
These do not necessarily stop parsing; inspect each diagnostic's `severity`.
PRIK_C_DOCS_END -->

<!-- PRIK_C_DOCS_START
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
PRIK_C_DOCS_END -->

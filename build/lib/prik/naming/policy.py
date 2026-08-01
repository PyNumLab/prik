"""Own Python-facing names and native symbols used by generated wrappers."""

from __future__ import annotations

from dataclasses import dataclass
import keyword
import re
import warnings

from prik.utilities.strings import create_incremented_string

_NON_IDENTIFIER = re.compile(r"[^0-9A-Za-z_]")
_SYMBOL_CONTEXTS = frozenset({"module", "function", "class", "variable", "wrapper"})
_PARENT_CONTEXTS = frozenset({"module", "function", "class", "loop", "program"})


@dataclass(frozen=True)
class NormalizedPublicName:
    """A source spelling converted to a valid Python-visible identifier."""

    name: str
    needs_fix: bool


@dataclass(frozen=True)
class PublicNameRecord:
    """The owner of a reserved name in one public Python namespace."""

    raw_name: str
    category: str
    owner: str


@dataclass(frozen=True)
class GeneratedSymbolRules:
    """Constraints used while selecting a generated target-language symbol."""

    language: str
    keywords: frozenset[str]
    case_sensitive: bool = True
    prefix_module_members: bool = False
    destructor_name: str = "free"
    module_constructor_prefix: bool = False
    rewrite_python_special_names: bool = False
    max_length: int | None = None

    def has_clash(self, name: object, symbols: set[object]) -> bool:
        """Return whether a symbol is reserved or already occupied."""
        text = str(name)
        if self.case_sensitive:
            return text in self.keywords or text in symbols
        folded = text.casefold()
        return folded in self.keywords or any(folded == str(symbol).casefold() for symbol in symbols)


def normalize_public_name(raw_name: object) -> NormalizedPublicName:
    """Convert a source spelling into a valid, lower-case Python identifier."""
    source = str(raw_name).strip()
    folded = source.casefold()
    normalized = _NON_IDENTIFIER.sub("_", folded) or "_"
    if not (normalized[0].isalpha() or normalized[0] == "_"):
        normalized = f"_{normalized}"
    if keyword.iskeyword(normalized):
        normalized = f"{normalized}_"
    return NormalizedPublicName(normalized, needs_fix=normalized != folded)


class NamingPolicy:
    """Allocate Python exports and language-safe generated symbols."""

    def __init__(self, *, strict_public_names: bool = False):
        self.strict_public_names = strict_public_names
        self._public_names: dict[tuple[str, ...], dict[str, PublicNameRecord]] = {}

    def reserve_public_name(
        self,
        namespace: tuple[str, ...],
        raw_name: object,
        *,
        category: str,
        owner: object | None = None,
    ) -> str:
        """Reserve one public Python name within its namespace."""
        normalized = normalize_public_name(raw_name)
        raw_text = str(raw_name)
        namespace_key = tuple(str(part) for part in namespace)
        namespace_text = ".".join(namespace_key) or "<module>"

        if self.strict_public_names and normalized.needs_fix:
            raise ValueError(
                f"Public {category} name {raw_text!r} in {namespace_text} normalizes to "
                f"{normalized.name!r}; strict wrapper naming does not fix Python names"
            )

        reserved = self._public_names.setdefault(namespace_key, {})
        existing = reserved.get(normalized.name)
        if existing is None:
            reserved[normalized.name] = PublicNameRecord(raw_text, category, str(owner or raw_name))
            return normalized.name
        if self.strict_public_names:
            raise ValueError(
                f"Public {category} name {raw_text!r} in {namespace_text} collides with "
                f"{existing.category} {existing.raw_name!r} ({existing.owner}) as Python name "
                f"{normalized.name!r}; strict wrapper naming does not fix collisions"
            )

        suffix = 2
        while f"{normalized.name}_{suffix}" in reserved:
            suffix += 1
        name = f"{normalized.name}_{suffix}"
        reserved[name] = PublicNameRecord(raw_text, category, str(owner or raw_name))
        return name

    def has_generated_symbol_clash(self, name: object, symbols: set[object], *, language: str) -> bool:
        """Return whether ``name`` is unusable in the selected language."""
        return generated_symbol_rules(language).has_clash(name, symbols)

    def generated_symbol(
        self,
        name: object,
        symbols: set[object],
        *,
        language: str,
        prefix: str,
        context: str,
        parent_context: str,
    ) -> str:
        """Return a generated symbol that satisfies target-language rules."""
        rules = generated_symbol_rules(language)
        candidate = _native_symbol_spelling(str(name), rules, prefix, context, parent_context)
        symbol = _available_symbol(candidate, symbols, rules)
        if rules.max_length is not None and len(symbol) > rules.max_length:
            warnings.warn(
                f"Name {symbol} is too long for {rules.language}. This may cause compiler errors",
                stacklevel=2,
            )
        return symbol


def generated_symbol_rules(language: str) -> GeneratedSymbolRules:
    """Return the fixed rule set for Python, C, or Fortran."""
    try:
        return _SYMBOL_RULES[language.casefold()]
    except KeyError as exc:
        raise ValueError(f"Unsupported generated-symbol language: {language!r}") from exc


def _native_symbol_spelling(
    name: str,
    rules: GeneratedSymbolRules,
    prefix: str,
    context: str,
    parent_context: str,
) -> str:
    """Translate Python special names before testing target-language clashes."""
    if context not in _SYMBOL_CONTEXTS:
        raise ValueError(f"Unsupported generated-symbol context: {context!r}")
    if parent_context not in _PARENT_CONTEXTS:
        raise ValueError(f"Unsupported generated-symbol parent context: {parent_context!r}")
    if context == "wrapper" or not rules.rewrite_python_special_names:
        return name
    if name == "__init__":
        name = f"{prefix}init" if rules.module_constructor_prefix and parent_context == "module" else "init"
    elif name == "__del__":
        name = rules.destructor_name
    elif len(name) > 4 and name.startswith("__") and name.endswith("__"):
        name = f"operator{name[1:-2]}"
    elif name.startswith("_"):
        name = f"private{name}"
    if rules.prefix_module_members and (context == "function" or (parent_context == "module" and context != "module")):
        return f"{prefix}{name}"
    return name


def _available_symbol(name: str, symbols: set[object], rules: GeneratedSymbolRules) -> str:
    """Return a readable non-reserved, non-duplicate generated symbol."""
    if not rules.has_clash(name, symbols):
        return name
    if rules.has_clash(name, set()):
        name = f"{name}_prik"
        if not rules.has_clash(name, symbols):
            return name
    return create_incremented_string(symbols, prefix=name, counter=2, naming_rules=rules)[0]


_C_LANGUAGE_KEYWORDS = frozenset(
    {
        "auto",
        "break",
        "case",
        "char",
        "const",
        "continue",
        "default",
        "do",
        "double",
        "else",
        "enum",
        "extern",
        "float",
        "for",
        "goto",
        "if",
        "inline",
        "int",
        "long",
        "register",
        "restrict",
        "return",
        "short",
        "signed",
        "sizeof",
        "static",
        "struct",
        "switch",
        "typedef",
        "union",
        "unsigned",
        "void",
        "volatile",
        "while",
        "_Alignas",
        "_Alignof",
        "_Atomic",
        "_Bool",
        "_Complex",
        "_Decimal32",
        "_Decimal64",
        "Decimal128",
        "_Generic",
        "_Imaginary",
        "_Noreturn",
        "_Static_assert",
        "_Thread_local",
        "alignas",
        "alignof",
        "bitint",
        "bool",
        "constexpr",
        "decimal128",
        "decimal32",
        "decimal64",
        "false",
        "nullptr",
        "static_assert",
        "thread_local",
        "true",
        "typeof",
        "typeof_unqual",
    }
)
_C_SPECIAL_NAMES = frozenset({"I", "main"})
_FORTRAN_WORDS = frozenset(
    {
        "abstract",
        "allocatable",
        "allocate",
        "assign",
        "associate",
        "asynchronous",
        "backspace",
        "bind",
        "block",
        "blockdata",
        "call",
        "case",
        "class",
        "close",
        "codimension",
        "common",
        "complex",
        "concurrent",
        "contains",
        "continue",
        "critical",
        "cycle",
        "data",
        "deallocate",
        "deferred",
        "dimension",
        "do",
        "else",
        "elseif",
        "elsewhere",
        "elemental",
        "end",
        "endfile",
        "endif",
        "endfunction",
        "endmodule",
        "endprogram",
        "endsubroutine",
        "entry",
        "enum",
        "enumerator",
        "equivalence",
        "error",
        "exit",
        "extends",
        "external",
        "final",
        "flush",
        "forall",
        "format",
        "function",
        "generic",
        "goto",
        "if",
        "implicit",
        "import",
        "include",
        "interface",
        "intrinsic",
        "lock",
        "module",
        "namelist",
        "non_overridable",
        "nopass",
        "nullify",
        "only",
        "open",
        "operator",
        "optional",
        "parameter",
        "pass",
        "pause",
        "pointer",
        "print",
        "private",
        "procedure",
        "program",
        "protected",
        "public",
        "pure",
        "read",
        "recursive",
        "result",
        "return",
        "rewind",
        "rewrite",
        "save",
        "select",
        "sequence",
        "stop",
        "submodule",
        "subroutine",
        "sync",
        "target",
        "then",
        "unlock",
        "use",
        "value",
        "volatile",
        "wait",
        "where",
        "while",
        "write",
    }
)
_FORTRAN_INTRINSICS = frozenset(
    {
        "abs",
        "acos",
        "asin",
        "atan",
        "c_associated",
        "c_f_pointer",
        "c_loc",
        "c_malloc",
        "c_ptr",
        "c_size_t",
        "contiguous",
        "count",
        "exp",
        "floor",
        "fraction",
        "int",
        "log",
        "max",
        "mod",
        "nint",
        "numpy_sign",
        "pack",
        "real",
        "sin",
        "sqrt",
        "storage_size",
        "tan",
    }
)

_SYMBOL_RULES = {
    "python": GeneratedSymbolRules(language="Python", keywords=frozenset()),
    "c": GeneratedSymbolRules(
        language="C",
        keywords=_C_LANGUAGE_KEYWORDS | _C_SPECIAL_NAMES,
        prefix_module_members=True,
        destructor_name="drop",
        rewrite_python_special_names=True,
    ),
    "fortran": GeneratedSymbolRules(
        language="Fortran",
        keywords=frozenset(word.casefold() for word in _FORTRAN_WORDS | _FORTRAN_INTRINSICS),
        case_sensitive=False,
        module_constructor_prefix=True,
        rewrite_python_special_names=True,
        max_length=96,
    ),
}

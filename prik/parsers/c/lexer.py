from __future__ import annotations

from dataclasses import dataclass, field
import re


@dataclass(frozen=True)
class CLogicalRecord:
    """A comment-stripped logical C source record with original line mapping."""

    text: str
    filename: str | None = None
    original_start_line: int = 1
    original_end_line: int = 1
    original_source_lines: tuple[str, ...] = field(default_factory=tuple)

    @property
    def source_line(self) -> str | None:
        return self.original_source_lines[0] if self.original_source_lines else None


@dataclass(frozen=True)
class NormalizedCSource:
    filename: str | None
    records: list[CLogicalRecord]


@dataclass(frozen=True)
class CToken:
    text: str
    kind: str
    filename: str | None = None
    line: int = 1
    column: int = 1
    source_line: str | None = None


@dataclass(frozen=True)
class CLineMapping:
    """Mapping from one preprocessed physical line to its original source line."""

    filename: str | None
    line: int
    source_line: str | None = None


@dataclass(frozen=True)
class CTopLevelSegment:
    """A top-level C declaration or function-definition header."""

    text: str
    terminator: str
    filename: str | None = None
    original_start_line: int = 1
    original_end_line: int = 1
    original_start_column: int = 1
    original_end_column: int = 1
    original_source_line: str | None = None
    original_end_source_line: str | None = None
    original_source_lines: tuple[str, ...] = field(default_factory=tuple)
    original_filenames: tuple[str | None, ...] = field(default_factory=tuple)
    original_line_numbers: tuple[int, ...] = field(default_factory=tuple)


_TWO_CHAR_OPERATORS = {
    "++",
    "--",
    "->",
    "==",
    "!=",
    "<=",
    ">=",
    "&&",
    "||",
    "+=",
    "-=",
    "*=",
    "/=",
    "%=",
    "&=",
    "|=",
    "^=",
    "<<",
    ">>",
}

_BRACKET_PAIRS = {"(": ")", "[": "]", "{": "}"}
_BRACKET_CLOSERS = {")": "(", "]": "[", "}": "{"}
_GCC_LINEMARKER_RE = re.compile(r'^\s*#\s+(?P<line>\d+)\s+(?:"(?P<quoted>(?:[^"\\]|\\.)*)"|(?P<bare>\S+))')
_LINE_DIRECTIVE_RE = re.compile(r'^\s*#\s*line\s+(?P<line>\d+)(?:\s+(?:"(?P<quoted>(?:[^"\\]|\\.)*)"|(?P<bare>\S+)))?')
_AGGREGATE_HEADER_ATTRIBUTE_RE = re.compile(r"\b(?:__attribute__?|__declspec(?:__)?)\b")


def _source_line(lines: list[str], line_number: int) -> str | None:
    if 1 <= line_number <= len(lines):
        return lines[line_number - 1]
    return None


def _source_lines(lines: list[str], start_line: int, end_line: int) -> tuple[str, ...]:
    return tuple(lines[start_line - 1 : end_line])


def _unescape_linemarker_filename(text: str) -> str:
    """Unescape the filename fragment from a compiler linemarker."""
    result: list[str] = []
    escaped = False
    for char in text:
        if escaped:
            result.append(
                {
                    "n": "\n",
                    "r": "\r",
                    "t": "\t",
                    "\\": "\\",
                    '"': '"',
                }.get(char, char)
            )
            escaped = False
        elif char == "\\":
            escaped = True
        else:
            result.append(char)
    if escaped:
        result.append("\\")
    return "".join(result)


def _parse_linemarker(line: str) -> tuple[int, str | None] | None:
    """Parse GCC/Clang `# N "file"` and standard `#line N "file"` markers."""
    stripped = line.strip()
    match = _LINE_DIRECTIVE_RE.match(stripped)
    if match is None:
        match = _GCC_LINEMARKER_RE.match(stripped)
    if match is None:
        return None

    line_number = int(match.group("line"))
    filename = match.group("quoted") or match.group("bare")
    if filename is not None:
        filename = _unescape_linemarker_filename(filename)
    return line_number, filename


def line_mappings_for_source(
    source: str,
    filename: str | None = None,
    *,
    use_linemarkers: bool = False,
) -> list[CLineMapping]:
    """Return one original-source mapping per physical source line.

    In ordinary raw mode each physical line maps to itself. In preprocessed
    mode, compiler linemarkers describe the original file and line for the
    next physical line. Linemarker lines themselves are mapped defensively but
    are normally blanked before parsing.
    """
    mappings: list[CLineMapping] = []
    current_filename = filename
    current_line = 1

    for physical_line, source_line in enumerate(source.splitlines(), start=1):
        marker = _parse_linemarker(source_line) if use_linemarkers else None
        if marker is not None:
            marker_line, marker_filename = marker
            if marker_filename is not None:
                current_filename = marker_filename
            current_line = marker_line
            mappings.append(CLineMapping(current_filename, current_line, source_line))
            continue

        if use_linemarkers:
            mappings.append(CLineMapping(current_filename, current_line, source_line))
            current_line += 1
        else:
            mappings.append(CLineMapping(filename, physical_line, source_line))

    return mappings


def _line_mapping(
    mappings: list[CLineMapping],
    physical_line: int,
    default_filename: str | None,
) -> CLineMapping:
    """Return the mapping for `physical_line` with safe fallback defaults."""
    if 1 <= physical_line <= len(mappings):
        return mappings[physical_line - 1]
    return CLineMapping(default_filename, physical_line, None)


def _mapped_source_lines(
    mappings: list[CLineMapping],
    start_line: int,
    end_line: int,
) -> tuple[str, ...]:
    """Return source-line text for a physical line range."""
    return tuple(mapping.source_line or "" for mapping in mappings[start_line - 1 : end_line])


def _mapped_filenames(
    mappings: list[CLineMapping],
    start_line: int,
    end_line: int,
) -> tuple[str | None, ...]:
    """Return mapped filenames for a physical line range."""
    return tuple(mapping.filename for mapping in mappings[start_line - 1 : end_line])


def _mapped_line_numbers(
    mappings: list[CLineMapping],
    start_line: int,
    end_line: int,
) -> tuple[int, ...]:
    """Return mapped line numbers for a physical line range."""
    return tuple(mapping.line for mapping in mappings[start_line - 1 : end_line])


def _advance_position(char: str, line: int, column: int) -> tuple[int, int]:
    if char == "\n":
        return line + 1, 1
    return line, column + 1


def _blank_preprocessor_directives(source: str) -> str:
    """Replace preprocessor directive logical lines with spaces."""
    out_lines: list[str] = []
    in_directive = False
    for line in source.splitlines(keepends=True):
        stripped = line.lstrip()
        starts_directive = stripped.startswith("#")
        if in_directive or starts_directive:
            newline = "\n" if line.endswith("\n") else ""
            body = line[:-1] if newline else line
            out_lines.append(" " * len(body) + newline)
            in_directive = body.rstrip().endswith("\\")
            continue
        out_lines.append(line)
        in_directive = False
    return "".join(out_lines)


def _scan_code_states(text: str):
    state = "normal"
    quote = ""
    escaped = False
    stack: list[str] = []

    for index, char in enumerate(text):
        if state in {"string", "char"}:
            yield index, char, tuple(stack), state
            if escaped:
                escaped = False
                continue
            if char == "\\":
                escaped = True
                continue
            if char == quote:
                state = "normal"
                quote = ""
            continue

        yield index, char, tuple(stack), state

        if char in {'"', "'"}:
            state = "string" if char == '"' else "char"
            quote = char
            escaped = False
        elif char in _BRACKET_PAIRS:
            stack.append(char)
        elif char in _BRACKET_CLOSERS and stack and stack[-1] == _BRACKET_CLOSERS[char]:
            stack.pop()


def top_level_split_with_offsets(text: str, delimiter: str = ",") -> list[tuple[str, int]]:
    """Split outside nested syntax and preserve each trimmed fragment offset."""
    if len(delimiter) != 1:
        raise ValueError("top_level_split_with_offsets delimiter must be a single character")

    parts: list[tuple[str, int]] = []
    start = 0
    for index, char, stack, state in _scan_code_states(text):
        if state == "normal" and not stack and char == delimiter:
            raw_part = text[start:index]
            part = raw_part.strip()
            if part:
                parts.append((part, start + len(raw_part) - len(raw_part.lstrip())))
            start = index + 1

    raw_tail = text[start:]
    tail = raw_tail.strip()
    if tail:
        parts.append((tail, start + len(raw_tail) - len(raw_tail.lstrip())))
    return parts


def top_level_split(text: str, delimiter: str = ",") -> list[str]:
    """Split on a delimiter that appears outside brackets and literals."""
    return [part for part, _offset in top_level_split_with_offsets(text, delimiter)]


def top_level_partition(text: str, delimiter: str = "=") -> tuple[str, str | None]:
    """Partition once on a top-level delimiter outside brackets and literals."""
    if len(delimiter) != 1:
        raise ValueError("top_level_partition delimiter must be a single character")

    for index, char, stack, state in _scan_code_states(text):
        if state == "normal" and not stack and char == delimiter:
            return text[:index].strip(), text[index + 1 :].strip()
    return text.strip(), None


def _balanced_invocation_end(text: str, open_index: int) -> int | None:
    """Return the offset after one balanced parenthesized invocation."""
    depth = 0
    quote = ""
    escaped = False
    for index in range(open_index, len(text)):
        char = text[index]
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return index + 1
    return None


def _strip_aggregate_header_attributes(header: str) -> str:
    """Blank attributes that can appear between an aggregate keyword and tag."""
    characters = list(header)
    for match in _AGGREGATE_HEADER_ATTRIBUTE_RE.finditer(header):
        end = match.end()
        open_index = end
        while open_index < len(header) and header[open_index].isspace():
            open_index += 1
        if open_index < len(header) and header[open_index] == "(":
            end = _balanced_invocation_end(header, open_index) or end
        for index in range(match.start(), end):
            if characters[index] != "\n":
                characters[index] = " "
    return "".join(characters)


def _is_aggregate_definition_header(
    header: str,
    *,
    tolerate_compiler_extensions: bool = False,
) -> bool:
    """Identify a tag definition before deciding that a brace starts a body."""
    if tolerate_compiler_extensions:
        header = _strip_aggregate_header_attributes(header)
    compact = " ".join(header.split())
    if "(" in compact or "=" in compact:
        return False
    words = compact.split()
    return any(word in {"struct", "union", "enum"} for word in words)


def _is_braced_declaration_header(
    header: str,
    *,
    tolerate_compiler_extensions: bool = False,
) -> bool:
    """Return whether a brace belongs to a declaration preserved through `;`."""
    return (
        _is_aggregate_definition_header(
            header,
            tolerate_compiler_extensions=tolerate_compiler_extensions,
        )
        or top_level_partition(header, "=")[1] is not None
    )


def split_top_level_c_source(
    source: str,
    filename: str | None = None,
    *,
    skip_preprocessor: bool = True,
    use_linemarkers: bool = False,
    tolerate_compiler_extensions: bool = False,
) -> list[CTopLevelSegment]:
    """Split C source into top-level declarations and definition headers."""
    stripped = strip_c_comments(source)
    if skip_preprocessor:
        stripped = _blank_preprocessor_directives(stripped)

    line_mappings = line_mappings_for_source(
        source,
        filename=filename,
        use_linemarkers=use_linemarkers,
    )
    segments: list[CTopLevelSegment] = []
    start_index: int | None = None
    start_line = 1
    start_column = 1
    line = 1
    column = 1
    i = 0
    paren_depth = 0
    bracket_depth = 0
    brace_depth = 0
    state = "normal"
    quote = ""
    escaped = False
    block_header: str | None = None
    block_start_line = 1
    block_start_column = 1
    block_source_line: str | None = None
    braced_declaration = False

    while i < len(stripped):
        char = stripped[i]

        if state in {"string", "char"}:
            if brace_depth == 0 and start_index is None and not char.isspace():
                start_index = i
                start_line = line
                start_column = column
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                state = "normal"
                quote = ""
            line, column = _advance_position(char, line, column)
            i += 1
            continue

        if char in {'"', "'"}:
            if brace_depth == 0 and start_index is None and not char.isspace():
                start_index = i
                start_line = line
                start_column = column
            state = "string" if char == '"' else "char"
            quote = char
            escaped = False
            line, column = _advance_position(char, line, column)
            i += 1
            continue

        if brace_depth == 0 and start_index is None and not char.isspace():
            start_index = i
            start_line = line
            start_column = column

        if char == "(":
            paren_depth += 1
        elif char == ")" and paren_depth:
            paren_depth -= 1
        elif char == "[":
            bracket_depth += 1
        elif char == "]" and bracket_depth:
            bracket_depth -= 1
        elif char == "{" and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0:
            if start_index is not None:
                header = stripped[start_index:i].strip()
                if header:
                    start_mapping = _line_mapping(line_mappings, start_line, filename)
                    block_header = header
                    block_start_line = start_line
                    block_start_column = start_column
                    block_source_line = start_mapping.source_line
                    braced_declaration = _is_braced_declaration_header(
                        header,
                        tolerate_compiler_extensions=tolerate_compiler_extensions,
                    )
            brace_depth = 1
            if not braced_declaration:
                start_index = None
        elif char == "{" and brace_depth:
            brace_depth += 1
        elif char == "}" and brace_depth:
            brace_depth -= 1
            if brace_depth == 0 and block_header and not braced_declaration:
                start_mapping = _line_mapping(line_mappings, block_start_line, filename)
                end_mapping = _line_mapping(line_mappings, line, filename)
                segments.append(
                    CTopLevelSegment(
                        text=block_header,
                        terminator="block",
                        filename=start_mapping.filename,
                        original_start_line=start_mapping.line,
                        original_end_line=end_mapping.line,
                        original_start_column=block_start_column,
                        original_end_column=column,
                        original_source_line=block_source_line,
                        original_end_source_line=end_mapping.source_line,
                        original_source_lines=_mapped_source_lines(line_mappings, block_start_line, line),
                        original_filenames=_mapped_filenames(line_mappings, block_start_line, line),
                        original_line_numbers=_mapped_line_numbers(line_mappings, block_start_line, line),
                    )
                )
                block_header = None
                block_source_line = None
        elif char == ";" and paren_depth == 0 and bracket_depth == 0 and brace_depth == 0 and start_index is not None:
            text = stripped[start_index:i].strip()
            if text:
                start_mapping = _line_mapping(line_mappings, start_line, filename)
                end_mapping = _line_mapping(line_mappings, line, filename)
                segments.append(
                    CTopLevelSegment(
                        text=text,
                        terminator=";",
                        filename=start_mapping.filename,
                        original_start_line=start_mapping.line,
                        original_end_line=end_mapping.line,
                        original_start_column=start_column,
                        original_end_column=column,
                        original_source_line=start_mapping.source_line,
                        original_end_source_line=end_mapping.source_line,
                        original_source_lines=_mapped_source_lines(line_mappings, start_line, line),
                        original_filenames=_mapped_filenames(line_mappings, start_line, line),
                        original_line_numbers=_mapped_line_numbers(line_mappings, start_line, line),
                    )
                )
            start_index = None
            block_header = None
            block_source_line = None
            braced_declaration = False

        line, column = _advance_position(char, line, column)
        i += 1

    if start_index is not None and brace_depth == 0:
        text = stripped[start_index:].strip()
        if text:
            start_mapping = _line_mapping(line_mappings, start_line, filename)
            end_mapping = _line_mapping(line_mappings, line, filename)
            segments.append(
                CTopLevelSegment(
                    text=text,
                    terminator="eof",
                    filename=start_mapping.filename,
                    original_start_line=start_mapping.line,
                    original_end_line=end_mapping.line,
                    original_start_column=start_column,
                    original_end_column=column,
                    original_source_line=start_mapping.source_line,
                    original_end_source_line=end_mapping.source_line,
                    original_source_lines=_mapped_source_lines(line_mappings, start_line, line),
                    original_filenames=_mapped_filenames(line_mappings, start_line, line),
                    original_line_numbers=_mapped_line_numbers(line_mappings, start_line, line),
                )
            )

    return segments


def strip_c_comments(source: str) -> str:
    """Remove C comments while preserving line and column accounting."""
    out: list[str] = []
    i = 0
    state = "normal"
    quote = ""

    while i < len(source):
        char = source[i]
        nxt = source[i + 1] if i + 1 < len(source) else ""

        if state == "line_comment":
            if char == "\n":
                out.append(char)
                state = "normal"
            else:
                out.append(" ")
            i += 1
            continue

        if state == "block_comment":
            if char == "*" and nxt == "/":
                out.extend((" ", " "))
                i += 2
                state = "normal"
                continue
            out.append("\n" if char == "\n" else " ")
            i += 1
            continue

        if state in {"string", "char"}:
            out.append(char)
            if char == "\\" and nxt:
                out.append(nxt)
                i += 2
                continue
            if char == quote:
                state = "normal"
                quote = ""
            i += 1
            continue

        if char == "/" and nxt == "/":
            out.extend((" ", " "))
            i += 2
            state = "line_comment"
            continue
        if char == "/" and nxt == "*":
            out.extend((" ", " "))
            i += 2
            state = "block_comment"
            continue
        if char in {'"', "'"}:
            state = "string" if char == '"' else "char"
            quote = char
            out.append(char)
            i += 1
            continue

        out.append(char)
        i += 1

    return "".join(out)


def normalize_c_source(source: str, filename: str | None = None) -> NormalizedCSource:
    """Fold C logical records after safe comment removal."""
    stripped = strip_c_comments(source)
    stripped_lines = stripped.splitlines()
    original_lines = source.splitlines()

    records: list[CLogicalRecord] = []
    pending_text: str | None = None
    pending_start_line = 1
    pending_source_lines: list[str] = []

    for index, stripped_line in enumerate(stripped_lines, start=1):
        original_line = original_lines[index - 1] if index - 1 < len(original_lines) else ""
        line = stripped_line.rstrip()
        continued = line.endswith("\\")
        part = line[:-1].rstrip() if continued else line

        if pending_text is None:
            pending_text = part
            pending_start_line = index
            pending_source_lines = [original_line]
        else:
            pending_text = f"{pending_text} {part.lstrip()}"
            pending_source_lines.append(original_line)

        if continued:
            continue

        if pending_text.strip():
            records.append(
                CLogicalRecord(
                    text=pending_text.strip(),
                    filename=filename,
                    original_start_line=pending_start_line,
                    original_end_line=index,
                    original_source_lines=tuple(pending_source_lines),
                )
            )
        pending_text = None
        pending_source_lines = []

    if pending_text is not None and pending_text.strip():
        records.append(
            CLogicalRecord(
                text=pending_text.strip(),
                filename=filename,
                original_start_line=pending_start_line,
                original_end_line=len(stripped_lines),
                original_source_lines=tuple(pending_source_lines),
            )
        )

    return NormalizedCSource(filename=filename, records=records)


def lex_c_source(source: str, filename: str | None = None) -> list[CToken]:
    """Tokenize a small C lexical subset for parser staging tests."""
    stripped = strip_c_comments(source)
    source_lines = source.splitlines()
    tokens: list[CToken] = []
    i = 0
    line = 1
    column = 1

    while i < len(stripped):
        char = stripped[i]
        nxt = stripped[i + 1] if i + 1 < len(stripped) else ""

        if char == "\n":
            line += 1
            column = 1
            i += 1
            continue
        if char.isspace():
            column += 1
            i += 1
            continue

        start_line = line
        start_column = column
        source_line = _source_line(source_lines, start_line)

        if char in {'"', "'"}:
            quote = char
            text = [char]
            i += 1
            column += 1
            while i < len(stripped):
                current = stripped[i]
                text.append(current)
                i += 1
                column += 1
                if current == "\\" and i < len(stripped):
                    text.append(stripped[i])
                    i += 1
                    column += 1
                    continue
                if current == quote:
                    break
            tokens.append(
                CToken(
                    text="".join(text),
                    kind="string" if quote == '"' else "char",
                    filename=filename,
                    line=start_line,
                    column=start_column,
                    source_line=source_line,
                )
            )
            continue

        if char.isalpha() or char == "_":
            start = i
            while i < len(stripped) and (stripped[i].isalnum() or stripped[i] == "_"):
                i += 1
                column += 1
            tokens.append(
                CToken(
                    text=stripped[start:i],
                    kind="identifier",
                    filename=filename,
                    line=start_line,
                    column=start_column,
                    source_line=source_line,
                )
            )
            continue

        if char.isdigit():
            start = i
            while i < len(stripped) and (stripped[i].isalnum() or stripped[i] in "._"):
                i += 1
                column += 1
            tokens.append(
                CToken(
                    text=stripped[start:i],
                    kind="number",
                    filename=filename,
                    line=start_line,
                    column=start_column,
                    source_line=source_line,
                )
            )
            continue

        text = char + nxt if char + nxt in _TWO_CHAR_OPERATORS else char
        i += len(text)
        column += len(text)
        tokens.append(
            CToken(
                text=text,
                kind="punctuation",
                filename=filename,
                line=start_line,
                column=start_column,
                source_line=source_line,
            )
        )

    return tokens


__all__ = (
    "CLineMapping",
    "CLogicalRecord",
    "CToken",
    "CTopLevelSegment",
    "NormalizedCSource",
    "lex_c_source",
    "line_mappings_for_source",
    "normalize_c_source",
    "split_top_level_c_source",
    "strip_c_comments",
    "top_level_partition",
    "top_level_split",
    "top_level_split_with_offsets",
)

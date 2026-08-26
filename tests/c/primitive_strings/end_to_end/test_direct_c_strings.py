"""Compiled evidence for the adopted rank-zero C character contracts."""

import shutil
from pathlib import Path

import numpy as np
import pytest

from prik import build_pyi_extension
from tests.c._support.runtime import sole_native_module

SOURCE = """#include <stddef.h>
#include <string.h>

int name_length(const char *text) { return (int)strlen(text); }

void shout(const char *text, char *out) {
    size_t index = 0;
    for (; text[index]; ++index) {
        char value = text[index];
        out[index] = (value >= 'a' && value <= 'z') ? (char)(value - 32) : value;
    }
    out[index] = '\\0';
}
"""


def _build(tmp_path: Path, contract_text: str, name: str):
    contract = tmp_path / f"{name}.pyi"
    contract.write_text(contract_text, encoding="utf-8")
    source = tmp_path / f"{name}.c"
    source.write_text(SOURCE, encoding="utf-8")
    return build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / f"build_{name}",
        output_name=name,
    )


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_string_input_borrows_the_python_payload_as_a_const_char_pointer(tmp_path: Path):
    """``String`` states a read-only input, so the prototype keeps ``const``."""
    result = _build(
        tmp_path,
        "from prik.contracts import Int32, String\n\ndef name_length(text: String) -> Int32: ...\n",
        "text_in",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "int32_t name_length(const char * text);" in binding
    assert module.name_length("hello") == np.int32(5)
    assert module.name_length("") == np.int32(0)
    with pytest.raises(TypeError, match="type str"):
        module.name_length(b"bytes")
    assert module.name_length("a\0b") == np.int32(1)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_rank_zero_string_storage_is_written_in_place_at_any_declared_capacity(tmp_path: Path):
    """``String[...][()]`` passes the caller's bytes through untouched."""
    result = _build(
        tmp_path,
        "from prik.contracts import String\n\ndef shout(text: String, out: String[...][()]) -> None: ...\n",
        "text_assumed",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "void shout(const char * text, char * out);" in binding
    for width in ("S8", "S32"):
        buffer = np.array(b"", dtype=width)
        assert module.shout("hello", buffer) is None
        assert buffer[()] == b"HELLO"
    with pytest.raises(TypeError, match=r"rank-zero numpy\.ndarray"):
        module.shout("hi", np.array([1.0]))


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_declared_string_capacity_validates_the_caller_itemsize(tmp_path: Path):
    """``String[n][()]`` is the form that asks PRIK to check the width."""
    result = _build(
        tmp_path,
        "from prik.contracts import String\n\ndef shout(text: String, out: String[32][()]) -> None: ...\n",
        "text_fixed",
    )
    module = sole_native_module(result.import_module())

    buffer = np.array(b"", dtype="S32")
    assert module.shout("hello", buffer) is None
    assert buffer[()] == b"HELLO"
    with pytest.raises(TypeError, match="itemsize 32"):
        module.shout("hello", np.array(b"", dtype="S8"))


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_string_arrays_stay_outside_the_direct_c_lane(tmp_path: Path):
    """Only rank-zero character contracts have a completed C lowering."""
    with pytest.raises(ValueError, match="C_DIRECT_UNSUPPORTED_STRING_CONTRACT:text"):
        _build(
            tmp_path,
            "from prik.contracts import Int32, String\n\ndef name_length(text: String[8][:]) -> Int32: ...\n",
            "text_array",
        )


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_raises_message_uses_a_binding_owned_buffer_without_an_adapter(tmp_path: Path):
    """Direct C owns the message buffer; only a bridged route allocates one."""
    contract = tmp_path / "checked.pyi"
    contract.write_text(
        """from prik.contracts import Arg, Float64, Hidden, Int32, Return, Returns, String, bind, native_call, raises

@bind("checked_sqrt")
@raises(status="status", message="message", success=0)
@native_call([Arg(0), Return("root", 0), Hidden("status", Int32), Hidden("message", String[64])])
def checked_sqrt(value: Float64) -> Returns["root", Float64]: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "checked.c"
    source.write_text(
        """#include <string.h>

void checked_sqrt(double value, double *root, int *status, char *message) {
    if (value < 0.0) {
        *status = -1;
        *root = 0.0;
        strcpy(message, "value must not be negative");
        return;
    }
    *status = 0;
    message[0] = '\\0';
    *root = value == 4.0 ? 2.0 : value;
}
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build_message",
        output_name="checked",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    # The callee receives the buffer itself, never the adapter's ``char **``.
    assert "void checked_sqrt(double value, double * root, int32_t * status, char * message);" in binding
    assert "char message[65]" in binding
    assert "free(message)" not in binding

    assert module.checked_sqrt(np.float64(4.0)) == np.float64(2.0)
    with pytest.raises(RuntimeError, match="value must not be negative"):
        module.checked_sqrt(np.float64(-1.0))


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
@pytest.mark.parametrize("declaration", ["String", "String[...]", "String[:]"])
def test_raises_message_without_a_declared_capacity_stays_fail_closed(tmp_path: Path, declaration: str):
    """An assumed or deferred width leaves the binding no buffer size to emit.

    C has no adapter to allocate one, so every form that omits a fixed capacity
    is refused by the language-neutral status-error rule before planning.
    """
    contract = f"""from prik.contracts import Arg, Float64, Hidden, Int32, String, bind, native_call, raises

@bind("checked")
@raises(status="status", message="message", success=0)
@native_call([Arg(0), Hidden("status", Int32), Hidden("message", {declaration})])
def checked(value: Float64) -> None: ...
"""
    with pytest.raises(ValueError, match="native status error message requires a fixed positive character length"):
        _build(tmp_path, contract, "message")


CHECKED_SOURCE = """#include <stdio.h>

void checked(double value, char *message, int *status) {
    if (value < 0.0) {
        *status = -1;
        snprintf(message, 64, "bad value %g", value);
        return;
    }
    *status = 0;
    message[0] = '\\0';
}
"""


def _build_checked(tmp_path: Path, declaration: str, name: str):
    contract = tmp_path / f"{name}.pyi"
    contract.write_text(
        f"""from prik.contracts import Arg, Float64, Hidden, Int32, String, bind, native_call, raises

@bind("checked")
@raises(status="status", message="message", success=0)
@native_call([Arg(0), Arg(1), Hidden("status", Int32)])
def checked(value: Float64, message: {declaration}) -> None: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / f"{name}.c"
    source.write_text(CHECKED_SOURCE, encoding="utf-8")
    return build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / f"build_{name}",
        output_name=name,
    )


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_raises_message_reads_a_caller_supplied_buffer(tmp_path: Path):
    """A visible ``String[n][()]`` message carries its own capacity."""
    result = _build_checked(tmp_path, "String[64][()]", "visible")
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    # The caller owns the buffer, so the binding neither NULL-checks nor frees it.
    assert "free(bound_message)" not in binding
    assert "void checked(double value, char * message, int32_t * status);" in binding

    buffer = np.array(b"", dtype="S64")
    assert module.checked(np.float64(9.0), buffer) is None
    assert buffer[()] == b""
    with pytest.raises(RuntimeError, match="bad value -1"):
        module.checked(np.float64(-1.0), buffer)
    # Raising does not consume the buffer; the caller can still inspect it.
    assert buffer[()] == b"bad value -1"


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_raises_message_accepts_a_borrowed_string_payload(tmp_path: Path):
    """``String`` states ``const char *``; PRIK does not police what C writes."""
    result = _build_checked(tmp_path, "String", "borrowed")
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "void checked(double value, const char * message, int32_t * status);" in binding

    scratch = "\0" * 64
    assert module.checked(np.float64(9.0), scratch) is None
    with pytest.raises(RuntimeError, match="bad value -1"):
        module.checked(np.float64(-1.0), scratch)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_visible_message_needs_no_declared_capacity(tmp_path: Path):
    """The caller's storage supplies the width a hidden message must declare."""
    result = _build_checked(tmp_path, "String[...][()]", "assumed")
    module = sole_native_module(result.import_module())

    buffer = np.array(b"", dtype="S64")
    with pytest.raises(RuntimeError, match="bad value -2"):
        module.checked(np.float64(-2.0), buffer)


PADDED_SOURCE = """void checked(double value, char *message, int *status) {
    int index = 0;
    const char *text = "padded failure";
    if (value >= 0.0) { *status = 0; message[0] = '\\0'; return; }
    *status = -1;
    /* Fill the whole buffer with blanks, exactly as fixed-length native
       character storage does, and leave no terminator. */
    for (; index < 64; ++index) { message[index] = ' '; }
    for (index = 0; text[index]; ++index) { message[index] = text[index]; }
}
"""


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_visible_message_never_reads_past_the_caller_capacity(tmp_path: Path):
    """An unterminated buffer is read as padded storage, not scanned for a NUL."""
    contract = tmp_path / "padded.pyi"
    contract.write_text(
        """from prik.contracts import Arg, Float64, Hidden, Int32, String, bind, native_call, raises

@bind("checked")
@raises(status="status", message="message", success=0)
@native_call([Arg(0), Arg(1), Hidden("status", Int32)])
def checked(value: Float64, message: String[64][()]) -> None: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "padded.c"
    source.write_text(PADDED_SOURCE, encoding="utf-8")
    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build_padded",
        output_name="padded",
    )
    module = sole_native_module(result.import_module())

    buffer = np.array(b"", dtype="S64")
    with pytest.raises(RuntimeError, match=r"^padded failure$"):
        module.checked(np.float64(-1.0), buffer)


@pytest.mark.skipif(shutil.which("cc") is None, reason="requires a C compiler")
def test_hidden_message_read_is_bounded_by_the_declared_capacity(tmp_path: Path):
    """The binding reads at most the width the contract declared."""
    contract = tmp_path / "wide.pyi"
    contract.write_text(
        """from prik.contracts import Arg, Float64, Hidden, Int32, String, bind, native_call, raises

@bind("wide")
@raises(status="status", message="message", success=0)
@native_call([Arg(0), Hidden("status", Int32), Hidden("message", String[8])])
def wide(value: Float64) -> None: ...
""",
        encoding="utf-8",
    )
    source = tmp_path / "wide.c"
    source.write_text(
        """#include <string.h>

void wide(double value, int *status, char *message) {
    if (value < 0.0) {
        *status = -1;
        /* Fill the declared width with no terminator inside it. */
        memset(message, 'x', 8);
        return;
    }
    *status = 0;
    message[0] = '\\0';
}
""",
        encoding="utf-8",
    )
    result = build_pyi_extension(
        contract,
        native_language="c",
        native_c_sources=[source],
        output_dir=tmp_path / "build_wide",
        output_name="wide",
    )
    module = sole_native_module(result.import_module())
    binding = next(path.read_text(encoding="utf-8") for path in result.generated_sources if path.suffix == ".c")

    assert "prik_status_message_text" in binding
    with pytest.raises(RuntimeError, match=r"^x{8}$"):
        module.wide(np.float64(-1.0))

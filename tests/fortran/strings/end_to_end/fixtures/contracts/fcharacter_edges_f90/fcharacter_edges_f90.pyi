from x2py.contracts import Return, Returns, String, native_call

def fixed_inout(
    name: String[8]
) -> Returns["name", String[8]]: ...

def assumed_inout(
    name: String
) -> Returns["name", String]: ...

def optional_inout(
    label: String = ...
) -> Returns["label", String] | None: ...

@native_call([Return('label', 0)])
def make_out() -> String[6]: ...

def unicode_echo(
    label: String
) -> String[5]: ...

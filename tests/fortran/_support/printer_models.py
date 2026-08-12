from pathlib import Path


from prik.contracts import CONTRACT_SYMBOLS

from prik.parsers.fortran import parse_fortran_file as parse_fortran_source


from prik.semantics.fortran2ir import (
    fortran_module_to_semantic_module,
)

from prik.pipeline.pyi import pyi_text_to_semantic_module as _parse_pyi_text

from prik.printers import (
    emit_module,
)
from prik.pipeline.wrapper import WrapperGenerator
from prik.planning import WrapperPlanner

from prik.semantics.models import (
    SemanticModule,
)

from prik.policy.completion import complete_semantic_policies

OPERATOR_F90_SOURCE = (
    Path(__file__).parents[1] / "generic_interfaces" / "end_to_end" / "fixtures" / "foperators_f90.f90"
)

CONTRACT_IMPORT = f"from prik.contracts import {', '.join(sorted(CONTRACT_SYMBOLS))}\n"


def parse_pyi_text(source: str, *args, **kwargs):
    if "prik.contracts" in source:
        return _parse_pyi_text(source, *args, **kwargs)
    return _parse_pyi_text(f"{CONTRACT_IMPORT}{source}", *args, **kwargs)


def generate_pyi(source: str) -> str:
    fmod = parse_fortran_source(source)

    smod = fortran_module_to_semantic_module(fmod)

    return emit_module(smod)


def generate_wrapper(module: SemanticModule):
    """Generate one rendered wrapper through the canonical pipeline."""
    complete_semantic_policies(module)
    return WrapperGenerator().generate(WrapperPlanner().build(module))


def rendered_source(artifacts, suffix: str) -> str:
    """Return the sole rendered source with ``suffix``."""
    matches = [source.text for source in artifacts.sources if source.path.suffix == suffix]
    assert len(matches) == 1
    return matches[0]


def normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.strip().splitlines())

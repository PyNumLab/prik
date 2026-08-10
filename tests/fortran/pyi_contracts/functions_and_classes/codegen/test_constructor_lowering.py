"""Lowering selected for an edited direct native constructor."""

from prik.pipeline.pyi import pyi_text_to_semantic_module
from prik.semantics.policy_completion import complete_semantic_policies
from prik.codegen import WrapperCodeGenerator, WrapperPlanner


def test_bound_constructor_generates_one_initializer_without_keyword_default():
    module = pyi_text_to_semantic_module(
        """
from prik.contracts import Addr, Arg, Int32, Pass, bind, native_call

class state:
    @bind("init_state")
    @native_call([Pass(), Arg(0)])
    def __init__(self, seed: Addr(Int32)) -> None: ...

    id: Int32
""",
        module_name="edited",
    )
    complete_semantic_policies(module)

    artifacts = WrapperCodeGenerator().generate(WrapperPlanner().build(module))
    sources = {source.path.suffix: source.text for source in artifacts.sources}

    assert {path.name for path in artifacts.source_paths} == {
        "bind_c_edited_wrapper.f90",
        "edited_wrapper.c",
        "edited_wrapper.h",
    }
    assert "init_state" in sources[".f90"]
    assert "state__default_init_wrapper" not in sources[".c"]
    assert 'static char * kwlist[] = {"self", "seed", NULL};' in sources[".c"]
    assert 'PyArg_ParseTupleAndKeywords(args, kwargs, "OO", kwlist, &bound_self_obj, &bound_seed_obj)' in sources[".c"]
    assert "Py_BEGIN_ALLOW_THREADS" not in sources[".c"]
    assert "Py_END_ALLOW_THREADS" not in sources[".c"]

from prik.semantics.models import (
    SemanticModule,
    SemanticClass,
    SemanticFunction,
    SemanticType,
)


def get_function(module: SemanticModule, name: str) -> SemanticFunction:
    for f in module.functions:
        if f.name == name:
            return f

    raise AssertionError(f"Function '{name}' not found")


def get_class(module: SemanticModule, name: str) -> SemanticClass:
    for c in module.classes:
        if c.name == name:
            return c

    raise AssertionError(f"Class '{name}' not found")


def has_constraint(obj, name: str) -> bool:
    return any(c.name == name for c in obj.constraints)


def array_contract(semantic_type: SemanticType):
    assert semantic_type.storage is not None
    assert semantic_type.storage.array is not None
    return semantic_type.storage.array

"""Naming policy for public APIs and generated target-language symbols."""

from .generated_files import (
    adapter_module_name,
    adapter_source_name,
    binding_module_name,
    binding_source_name,
    bridge_module_name,
    bridge_source_name,
    stub_identifier,
    wrapper_header_name,
)
from .policy import (
    GeneratedSymbolRules,
    NamingPolicy,
    NormalizedPublicName,
    PublicNameRecord,
    generated_symbol_rules,
    normalize_public_name,
)

__all__ = (
    "GeneratedSymbolRules",
    "NamingPolicy",
    "NormalizedPublicName",
    "PublicNameRecord",
    "adapter_module_name",
    "adapter_source_name",
    "binding_module_name",
    "binding_source_name",
    "bridge_module_name",
    "bridge_source_name",
    "generated_symbol_rules",
    "normalize_public_name",
    "stub_identifier",
    "wrapper_header_name",
)

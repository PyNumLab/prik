"""Pointer descriptor build requirements in the generated manifest."""

from prik.pipeline.build import _manifest_native_array_requirements
from prik.semantics.native_array_handles import NativeArrayBuildRequirement, NativeArrayBuildRequirements


def test_pyi_manifest_records_pointer_descriptor_interop_requirements():
    manifest_section = _manifest_native_array_requirements(
        NativeArrayBuildRequirements(
            pointer_c_descriptor_interop=True,
            headers=("ISO_Fortran_binding.h",),
            items=(
                NativeArrayBuildRequirement(
                    owner="api.inspect.target",
                    item="target",
                    descriptor_kind="pointer",
                    handle_kind="argument_descriptor",
                    descriptor_interop="pointer_c_descriptor",
                    headers=("ISO_Fortran_binding.h",),
                ),
            ),
        )
    )

    assert manifest_section == {
        "pointer_c_descriptor_interop": True,
        "headers": ["ISO_Fortran_binding.h"],
        "items": [
            {
                "owner": "api.inspect.target",
                "item": "target",
                "descriptor_kind": "pointer",
                "handle_kind": "argument_descriptor",
                "descriptor_interop": "pointer_c_descriptor",
                "headers": ["ISO_Fortran_binding.h"],
            }
        ],
    }

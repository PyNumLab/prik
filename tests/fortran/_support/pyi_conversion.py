from prik.contracts import CONTRACT_SYMBOLS


from prik.pipeline.pyi import pyi_text_to_semantic_module


CONTRACT_IMPORT = f"from prik.contracts import {', '.join(sorted(CONTRACT_SYMBOLS))}\n"


def parse_pyi_text(source: str, *args, **kwargs):
    if "prik.contracts" in source:
        return pyi_text_to_semantic_module(source, *args, **kwargs)
    return pyi_text_to_semantic_module(f"{CONTRACT_IMPORT}{source}", *args, **kwargs)

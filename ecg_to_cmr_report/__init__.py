"""
ECG to CMR Report — CMR-style reports from PTB-XL data using a local LLM (Transformers or llama-cpp).
"""

from .e_to_c_llama1 import (
    build_prompt,
    call_llm,
    call_llama_local,
    generate_cmr_report,
    generate_cmr_with_llama,
    load_ptbxl_record,
    save_report,
    save_cmr_report,
)

__all__ = [
    "load_ptbxl_record",
    "build_prompt",
    "call_llm",
    "call_llama_local",
    "generate_cmr_report",
    "generate_cmr_with_llama",
    "save_report",
    "save_cmr_report",
]

"""
ECG to CMR Report Generator

Uses PTB-XL data (metadata + 12-lead ECG signal) and a local LLM to produce a CMR-style report.
All processing is local (no API), suitable for IRB/healthcare data.

Paths: PROJECT_ROOT is the folder containing ecg_to_cmr_report/ (repo root). Data paths in CSVs
can be relative to that (e.g. data/ptbxl_pclr_format/...) so the same repo works on Mac, Colab, Linux.

Initial approach: llama-cpp-python + GGUF model. This caused a segmentation fault on macOS
(Metal backend). We therefore use the Transformers backend by default (USE_TRANSFORMERS=1).

Usage:
    USE_TRANSFORMERS=1 python -m ecg_to_cmr_report.ecg_to_cmr_report
    USE_TRANSFORMERS=1 python -m ecg_to_cmr_report.ecg_to_cmr_report --ecg-id 2
"""

import argparse
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
PTBXL_CSV = PROJECT_ROOT / "data" / "ptbxl_database.csv"
ECG_LABELS_CSV = PROJECT_ROOT / "data" / "ptbxl_with_labels" / "ecg_with_labels.csv"
CMR_OUTPUT_DIR = PROJECT_ROOT / "ecg_to_cmr_report" / "outputs_llama1"

# 12-lead names in PCLR order
LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# GGUF path (only for llama-cpp backend; optional)
DEFAULT_GGUF = PROJECT_ROOT / "models" / "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

# Change this to run a different ECG, or pass: python -m ecg_to_cmr_report.ecg_to_cmr_report --ecg-id 2
DEFAULT_ECG_ID = 2

_llm = None
_transformers_model = None
_transformers_tokenizer = None


def _get_ecg_file_path(ecg_id: int) -> Path:
    if not ECG_LABELS_CSV.exists():
        raise FileNotFoundError(f"Required file not found: {ECG_LABELS_CSV}")
    labels = pd.read_csv(ECG_LABELS_CSV)
    match = labels[labels["ecg_id"] == ecg_id]
    if match.empty:
        raise FileNotFoundError(f"ecg_id={ecg_id} not in {ECG_LABELS_CSV}")
    path = Path(match.iloc[0]["ecg_file"])
    if not path.is_absolute():
        path = PROJECT_ROOT / path
    if not path.exists():
        raise FileNotFoundError(f"ECG file missing: {path}")
    return path


def summarize_ecg_signal(ecg: np.ndarray) -> str:
    """
    Turn the ECG waveform into a short text summary for the prompt.
    For each lead: min, max, mean in mV.
    """
    if ecg.ndim != 2 or ecg.shape != (4096, 12):
        return "(ECG shape unexpected)"
    return "\n".join(
        f"  {lead}: min={ecg[:, i].min():.2f} mV, max={ecg[:, i].max():.2f} mV, mean={ecg[:, i].mean():.2f} mV"
        for i, lead in enumerate(LEAD_NAMES)
    )


def load_ptbxl_record(ecg_id: int = 2) -> dict:
    """
    Load one record from PTB-XL: metadata + ECG signal.

    Args:
        ecg_id: The ECG ID (row number). Default 1.

    Returns:
        Dictionary with report, scp_codes, age, sex, ecg_signal_summary, etc.
    """
    df = pd.read_csv(PTBXL_CSV)
    row = df[df["ecg_id"] == ecg_id].iloc[0]
    record = {
        "ecg_id": int(row["ecg_id"]),
        "report": str(row["report"]),
        "scp_codes": str(row["scp_codes"]),
        "age": row["age"],
        "sex": row["sex"],
        "heart_axis": str(row["heart_axis"]) if pd.notna(row["heart_axis"]) else "",
        "ecg_signal_summary": "",
    }

    ecg_path = _get_ecg_file_path(ecg_id)
    ecg = np.load(ecg_path)
    record["ecg_signal_summary"] = summarize_ecg_signal(ecg)
    return record


def build_prompt(record: dict) -> str:
    """
    Build the prompt we send to Llama.
    We give it metadata + ECG signal summary and ask it to write a CMR report.
    """
    ecg_report = record["report"]
    scp_codes = record["scp_codes"]
    age = record["age"]
    sex = "male" if record["sex"] == 1 else "female"
    signal_summary = record.get("ecg_signal_summary", "(not available)")

    prompt = f"""You are a cardiac imaging expert. Based on the following ECG data (metadata and signal), write a short CMR (Cardiac Magnetic Resonance) style report.

ECG metadata:
- ECG report: {ecg_report}
- SCP diagnostic codes: {scp_codes}
- Patient age: {age} years
- Sex: {sex}

ECG signal (12 leads, voltage in mV - min, max, mean per lead):
{signal_summary}

Write a CMR report with these sections: Clinical Indication, Findings (brief), and Conclusion. Use both the metadata and the signal amplitudes to inform your report (e.g. low voltage in leads may suggest pericardial effusion). Keep it concise (3-5 sentences total). Do not repeat the same phrase. Do not invent specific numbers (e.g. ejection fraction).

CMR Report:
"""
    return prompt


def _use_transformers_backend() -> bool:
    """Use Hugging Face Transformers instead of llama-cpp (avoids Metal segfault on Mac)."""
    return os.environ.get("USE_TRANSFORMERS", "").strip().lower() in ("1", "true", "yes")


def _get_model_path() -> Path:
    """Get path to the GGUF model file."""
    path = os.environ.get("ECG_LLM_MODEL_PATH")
    if path:
        return Path(path)
    return DEFAULT_GGUF


def _get_device_llama():
    """Prefer CUDA (Colab), then MPS (Apple Silicon), then CPU."""
    import torch
    if os.environ.get("USE_CUDA") and torch.cuda.is_available():
        return "cuda"
    if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
        return "mps"
    return "cpu"


def call_llama_transformers(prompt: str, max_tokens: int = 256) -> str:
    """
    Call local model via Hugging Face Transformers.
    Uses CUDA on Colab, MPS (Metal) on Apple Silicon, or CPU.

    Requires: pip install transformers torch
    """
    global _transformers_model, _transformers_tokenizer
    if _transformers_model is None:
        from transformers import AutoModelForCausalLM, AutoTokenizer
        import torch
        model_id = "TinyLlama/TinyLlama-1.1B-Chat-v1.0"
        print(f"Loading {model_id} (first time may download ~2GB)...")
        _transformers_tokenizer = AutoTokenizer.from_pretrained(model_id)
        _transformers_model = AutoModelForCausalLM.from_pretrained(model_id)
        _device = _get_device_llama()
        _transformers_model = _transformers_model.to(_device)
        print(f"Model loaded on {_device}.")

    import torch
    _device = next(_transformers_model.parameters()).device
    inputs = _transformers_tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(_device) for k, v in inputs.items()}
    input_len = inputs["input_ids"].shape[1]
    print(f"Generating CMR report on {_device}...")
    outputs = _transformers_model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        do_sample=False,
        pad_token_id=_transformers_tokenizer.eos_token_id,
        repetition_penalty=1.2,  # Reduces repetitive phrases
    )
    # Decode only the generated part (skip the prompt tokens)
    generated = _transformers_tokenizer.decode(outputs[0][input_len:], skip_special_tokens=True)
    return generated.strip()


def _call_llama_cpp(prompt: str, max_tokens: int = 256) -> str:
    global _llm
    path = Path(os.environ.get("ECG_LLM_MODEL_PATH", DEFAULT_GGUF))
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}. Run: python -m ecg_to_cmr_report.download_model")
    if _llm is None:
        from llama_cpp import Llama
        _llm = Llama(model_path=str(path), n_ctx=2048, n_gpu_layers=0, verbose=False)
    return _llm(prompt, max_tokens=max_tokens, stop=["</s>"], echo=False)["choices"][0]["text"].strip()


def call_llm(prompt: str, max_tokens: int = 256) -> str:
    return call_llama_transformers(prompt, max_tokens) if _use_transformers_backend() else _call_llama_cpp(prompt, max_tokens)


def generate_cmr_report(ecg_id: int = 2) -> str:
    record = load_ptbxl_record(ecg_id)
    prompt = build_prompt(record)
    return call_llm(prompt)


def save_report(text: str, ecg_id: int) -> Path:
    CMR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = CMR_OUTPUT_DIR / f"cmr_report_ecg{ecg_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path.write_text(text, encoding="utf-8")
    return path


# Backward-compatible names
call_llama_local = call_llm
generate_cmr_with_llama = generate_cmr_report
save_cmr_report = save_report


def main():
    parser = argparse.ArgumentParser(description="Generate CMR report from PTB-XL ECG")
    parser.add_argument("--ecg-id", type=int, default=DEFAULT_ECG_ID, help=f"PTB-XL ECG ID (default: {DEFAULT_ECG_ID})")
    args = parser.parse_args()
    ecg_id = args.ecg_id

    start_time = time.perf_counter()
    print("Loading PTB-XL record (metadata + ECG signal)...")
    record = load_ptbxl_record(ecg_id)
    print(f"ECG ID: {ecg_id}  |  Report: {record['report'][:60]}...")
    print("ECG signal: 12 leads loaded.\n")

    backend = "Transformers (CPU)" if _use_transformers_backend() else f"llama-cpp ({DEFAULT_GGUF})"
    print(f"Calling local LLM ({backend})...\n")

    try:
        cmr_report = generate_cmr_report(ecg_id)
        saved = save_report(cmr_report, ecg_id)
        print("=" * 60)
        print("CMR REPORT (generated by LLM)")
        print("=" * 60)
        print(cmr_report)
        print("=" * 60)
        print(f"Saved to: {saved}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
        if not _use_transformers_backend():
            print("\nIf you see a segfault, use: USE_TRANSFORMERS=1 python -m ecg_to_cmr_report.ecg_to_cmr_report")
    finally:
        t = time.perf_counter() - start_time
        print(f"Time elapsed: {int(t) // 60} min {int(t) % 60} s")


if __name__ == "__main__":
    main()

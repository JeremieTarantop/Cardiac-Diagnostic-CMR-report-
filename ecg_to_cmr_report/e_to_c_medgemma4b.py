"""
ECG to CMR Report Generator — MedGemma 4B

Same pipeline as e_to_c_llama1.py but uses Google's MedGemma 4B (medical-focused model).
Runs locally via Hugging Face Transformers. No API calls.

Speed: On CPU only, a 4B model is very slow (~minutes per token). This script uses
Metal (MPS) on Apple Silicon when available for much faster inference, and defaults
to 128 max tokens (use --max-tokens to change).

Setup (see below):
  1. pip install transformers torch
  2. Hugging Face account + accept MedGemma terms
  3. huggingface-cli login (or set HF_TOKEN)

Usage:
    python -m ecg_to_cmr_report.e_to_c_medgemma4b
    python -m ecg_to_cmr_report.e_to_c_medgemma4b --ecg-id 2
"""

import argparse
import os
import time
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
PTBXL_CSV = PROJECT_ROOT / "data" / "ptbxl_database.csv"
ECG_LABELS_CSV = PROJECT_ROOT / "data" / "ptbxl_with_labels" / "ecg_with_labels.csv"
CMR_OUTPUT_DIR = PROJECT_ROOT / "ecg_to_cmr_report" / "outputs_medgemma4b"

LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# MedGemma 4B instruction-tuned (better for following the CMR report prompt)
MEDGEMMA_MODEL_ID = "google/medgemma-4b-it"
DEFAULT_ECG_ID = 2

_model = None
_tokenizer = None


def _get_ecg_file_path(ecg_id: int) -> Path:
    if not ECG_LABELS_CSV.exists():
        raise FileNotFoundError(f"Required file not found: {ECG_LABELS_CSV}")
    labels = pd.read_csv(ECG_LABELS_CSV)
    match = labels[labels["ecg_id"] == ecg_id]
    if match.empty:
        raise FileNotFoundError(f"ecg_id={ecg_id} not in {ECG_LABELS_CSV}")
    path = Path(match.iloc[0]["ecg_file"])
    if not path.exists():
        raise FileNotFoundError(f"ECG file missing: {path}")
    return path


def summarize_ecg_signal(ecg: np.ndarray) -> str:
    if ecg.ndim != 2 or ecg.shape != (4096, 12):
        return "(ECG shape unexpected)"
    return "\n".join(
        f"  {lead}: min={ecg[:, i].min():.2f} mV, max={ecg[:, i].max():.2f} mV, mean={ecg[:, i].mean():.2f} mV"
        for i, lead in enumerate(LEAD_NAMES)
    )


def load_ptbxl_record(ecg_id: int) -> dict:
    df = pd.read_csv(PTBXL_CSV)
    row = df[df["ecg_id"] == ecg_id].iloc[0]
    ecg_path = _get_ecg_file_path(ecg_id)
    ecg = np.load(ecg_path)
    record = {
        "ecg_id": int(row["ecg_id"]),
        "report": str(row["report"]),
        "scp_codes": str(row["scp_codes"]),
        "age": row["age"],
        "sex": row["sex"],
        "heart_axis": str(row["heart_axis"]) if pd.notna(row["heart_axis"]) else "",
        "ecg_signal_summary": summarize_ecg_signal(ecg),
    }
    return record


def build_prompt(record: dict) -> str:
    sex = "male" if record["sex"] == 1 else "female"
    return f"""You are a cardiac imaging expert. Based on the following ECG data (metadata and signal), write a short CMR (Cardiac Magnetic Resonance) style report.

ECG metadata:
- ECG report: {record["report"]}
- SCP diagnostic codes: {record["scp_codes"]}
- Patient age: {record["age"]} years
- Sex: {sex}

ECG signal (12 leads, voltage in mV - min, max, mean per lead):
{record.get("ecg_signal_summary", "(not available)")}

Write a CMR report with these sections: Clinical Indication, Findings (brief), and Conclusion. Use both the metadata and the signal amplitudes. Keep it concise (3-5 sentences). Do not repeat the same phrase. Do not invent specific numbers (e.g. ejection fraction).

CMR Report:
"""


def _get_device():
    """Use CUDA (e.g. Colab), then Metal (MPS) on Apple Silicon, then CPU."""
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
        if getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            return "mps"
    except Exception:
        pass
    return "cpu"


def _load_medgemma():
    """Load MedGemma 4B. Uses HF token from env or huggingface-cli login."""
    global _model, _tokenizer
    if _model is not None:
        return
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    token = os.environ.get("HF_TOKEN") or True  # True = use cached login
    device = _get_device()
    print(f"Loading {MEDGEMMA_MODEL_ID} (first time may download ~8GB)...")
    print("If you get a 401, run: huggingface-cli login and accept the model terms at https://huggingface.co/google/medgemma-4b-it")
    _tokenizer = AutoTokenizer.from_pretrained(MEDGEMMA_MODEL_ID, token=token)
    _model = AutoModelForCausalLM.from_pretrained(
        MEDGEMMA_MODEL_ID,
        token=token,
        torch_dtype=torch.bfloat16 if device in ("mps", "cuda") else torch.float32,
    )
    _model = _model.to(device)
    print(f"Model loaded on: {device}.")


def call_medgemma(prompt: str, max_tokens: int = 16) -> str:
    _load_medgemma()
    import torch
    device = next(_model.parameters()).device
    inputs = _tokenizer(prompt, return_tensors="pt", truncation=True, max_length=2048)
    inputs = {k: v.to(device) for k, v in inputs.items()}
    input_len = inputs["input_ids"].shape[1]
    print(f"Generating CMR report (max {max_tokens} tokens on {device})...")
    out = _model.generate(
        **inputs,
        max_new_tokens=max_tokens,
        do_sample=False,
        pad_token_id=_tokenizer.eos_token_id,
        repetition_penalty=1.2,
    )
    return _tokenizer.decode(out[0][input_len:], skip_special_tokens=True).strip()


def generate_cmr_report(ecg_id: int, max_tokens: int = 16) -> str:
    record = load_ptbxl_record(ecg_id)
    prompt = build_prompt(record)
    return call_medgemma(prompt, max_tokens=max_tokens)


def save_report(text: str, ecg_id: int) -> Path:
    CMR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    path = CMR_OUTPUT_DIR / f"cmr_report_medgemma4b_ecg{ecg_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(description="Generate CMR report from PTB-XL ECG using MedGemma 4B")
    parser.add_argument("--ecg-id", type=int, default=DEFAULT_ECG_ID, help=f"PTB-XL ECG ID (default: {DEFAULT_ECG_ID})")
    parser.add_argument("--max-tokens", type=int, default=128, help="Max new tokens (default 128; lower = faster)")
    args = parser.parse_args()
    ecg_id = args.ecg_id

    start_time = time.perf_counter()
    print("Loading PTB-XL record (metadata + ECG signal)...")
    record = load_ptbxl_record(ecg_id)
    print(f"ECG ID: {ecg_id}  |  Report: {record['report'][:60]}...")
    print("ECG signal: 12 leads loaded.\n")
    print("Calling MedGemma 4B...\n")

    try:
        cmr_report = generate_cmr_report(ecg_id, max_tokens=args.max_tokens)
        saved = save_report(cmr_report, ecg_id)
        print("=" * 60)
        print("CMR REPORT (generated by MedGemma 4B)")
        print("=" * 60)
        print(cmr_report)
        print("=" * 60)
        print(f"Saved to: {saved}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        t = time.perf_counter() - start_time
        print(f"Time elapsed: {int(t) // 60} min {int(t) % 60} s")


if __name__ == "__main__":
    main()

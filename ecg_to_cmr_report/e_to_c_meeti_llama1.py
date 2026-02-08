"""
ECG to CMR Report — MEETI dataset + TinyLlama 1.1B

Same CMR prompt and pipeline as e_to_c_llama1.py, but for MEETI records (Zenodo 15893351).
Inputs to the prompt: (i) raw ECG summary from signal [same extraction as e_to_c_llama1],
(ii) MEETI report + any FeatureDB parameters from .mat, (iii) MEETI LLM_Interpretation.

Paths: PROJECT_ROOT = repo root. --mat-path and --ecg-npy can be relative to repo root (portable).

Usage:
    USE_TRANSFORMERS=1 python -m ecg_to_cmr_report.e_to_c_meeti_llama1 --mat-path "MEETI/p1099/p10990038/s40161580/40161580.mat"
    USE_TRANSFORMERS=1 python -m ecg_to_cmr_report.e_to_c_meeti_llama1 --mat-path "MEETI/.../40000369.mat" --ecg-npy /path/to/raw_ecg.npy
"""

import argparse
import os
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent
MEETI_ROOT = PROJECT_ROOT / "MEETI"
CMR_OUTPUT_DIR = PROJECT_ROOT / "ecg_to_cmr_report" / "outputs_meeti_llama1"

# Same 12-lead order as e_to_c_llama1
LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# Reuse TinyLlama from e_to_c_llama1
from ecg_to_cmr_report.e_to_c_llama1 import call_llama_transformers


def summarize_ecg_signal(ecg: np.ndarray) -> str:
    """Same as e_to_c_llama1: per-lead min, max, mean in mV (expects shape (4096, 12) or (N, 12))."""
    if ecg.ndim != 2 or ecg.shape[1] != 12:
        return "(ECG shape unexpected; expected (N, 12))"
    return "\n".join(
        f"  {lead}: min={ecg[:, i].min():.2f} mV, max={ecg[:, i].max():.2f} mV, mean={ecg[:, i].mean():.2f} mV"
        for i, lead in enumerate(LEAD_NAMES)
    )


def _format_featuredb_summary(data: dict) -> str:
    """Turn featuredb_lead_* entries in .mat into a short text summary if present."""
    parts = []
    for key in sorted(data.keys()):
        if not key.startswith("featuredb_lead_"):
            continue
        v = data[key]
        if hasattr(v, "shape") and hasattr(v, "dtype"):
            try:
                n = np.asarray(v).size
                parts.append(f"  {key}: {n} values")
            except Exception:
                parts.append(f"  {key}: (present)")
    return "\n".join(parts) if parts else "(no FeatureDB parameters in this .mat)"


def load_meeti_record(mat_path: Path, ecg_npy_path: Optional[Path] = None) -> dict:
    """
    Load one MEETI record from .mat. Optionally add raw ECG summary from a .npy file
    (same format as PTB-XL: (4096, 12) or (N, 12) in mV).
    """
    import scipy.io

    mat_path = Path(mat_path)
    if not mat_path.exists():
        raise FileNotFoundError(f"MEETI .mat not found: {mat_path}")

    data = scipy.io.loadmat(str(mat_path), struct_as_record=False, squeeze_me=True)

    def _str(v) -> str:
        if isinstance(v, str):
            return v.strip()
        if hasattr(v, "size"):
            return str(v.flatten()[0]).strip() if v.size == 1 else str(v).strip()
        return str(v).strip()

    record = {
        "id": _str(data.get("id", "")),
        "report": _str(data.get("report", "")),
        "LLM_Interpretation": _str(data.get("LLM_Interpretation", "")),
        "ecg_signal_summary": "",
        "meeti_params_summary": "",
    }

    record["meeti_params_summary"] = _format_featuredb_summary(data)

    if ecg_npy_path and Path(ecg_npy_path).exists():
        ecg = np.load(ecg_npy_path)
        record["ecg_signal_summary"] = summarize_ecg_signal(ecg)
    else:
        record["ecg_signal_summary"] = "(raw ECG signal not provided; use --ecg-npy if available)"

    return record


# Max length for LLM_Interpretation in prompt to keep context short (faster generation)
MAX_LLM_INTERP_CHARS = 1200


def build_prompt(record: dict) -> str:
    """
    Same CMR prompt structure as e_to_c_llama1: expert instruction, ECG data, then ask for
    Clinical Indication, Findings, Conclusion.
    """
    report = record["report"]
    llm_interp = record["LLM_Interpretation"]
    if len(llm_interp) > MAX_LLM_INTERP_CHARS:
        llm_interp = llm_interp[:MAX_LLM_INTERP_CHARS] + " [...]"
    signal_summary = record.get("ecg_signal_summary", "(not available)")
    meeti_params = record.get("meeti_params_summary", "(not available)")

    prompt = f"""You are a cardiac imaging expert. Based on the following ECG data (metadata and signal), write a short CMR (Cardiac Magnetic Resonance) style report.

ECG metadata (MEETI):
- ECG report: {report}
- LLM interpretation (MEETI): {llm_interp}

MEETI extracted parameters (FeatureDB, if available):
{meeti_params}

ECG signal (12 leads, voltage in mV - min, max, mean per lead):
{signal_summary}

Write a CMR report with these sections: Clinical Indication, Findings (brief), and Conclusion. Use both the metadata and the signal amplitudes to inform your report (e.g. low voltage in leads may suggest pericardial effusion). Keep it concise (3-5 sentences total). Do not repeat the same phrase. Do not invent specific numbers (e.g. ejection fraction). Don't do Introduction.

CMR Report:
"""
    return prompt


def generate_cmr_report(mat_path: Path, ecg_npy_path: Optional[Path] = None, max_tokens: int = 128) -> str:
    record = load_meeti_record(mat_path, ecg_npy_path)
    prompt = build_prompt(record)
    return call_llama_transformers(prompt, max_tokens=max_tokens)


def save_report(text: str, record_id: str) -> Path:
    CMR_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = "".join(c if c.isalnum() else "_" for c in record_id)[:32]
    path = CMR_OUTPUT_DIR / f"cmr_report_meeti_{safe_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    path.write_text(text, encoding="utf-8")
    return path


def main():
    parser = argparse.ArgumentParser(
        description="Generate CMR report from MEETI record using TinyLlama 1.1B (same prompt as e_to_c_llama1)"
    )
    parser.add_argument(
        "--mat-path",
        type=str,
        required=True,
        help="Path to MEETI .mat file (e.g. MEETI/p1099/p10990038/s40161580/40161580.mat)",
    )
    parser.add_argument(
        "--ecg-npy",
        type=str,
        default=None,
        help="Optional path to raw ECG .npy (shape (N, 12)) for same extraction as e_to_c_llama1",
    )
    parser.add_argument("--max-tokens", type=int, default=128, help="Max new tokens (default 128; lower = faster)")
    args = parser.parse_args()

    mat_path = Path(args.mat_path)
    if not mat_path.is_absolute():
        mat_path = PROJECT_ROOT / mat_path
    ecg_npy = Path(args.ecg_npy) if args.ecg_npy else None
    if ecg_npy and not ecg_npy.is_absolute():
        ecg_npy = PROJECT_ROOT / ecg_npy

    start_time = time.perf_counter()
    print("Loading MEETI record...")
    record = load_meeti_record(mat_path, ecg_npy)
    print(f"Record id: {record['id']}  |  Report: {record['report'][:60]}...")
    print("LLM_Interpretation length:", len(record["LLM_Interpretation"]))
    print("Calling TinyLlama 1.1B...\n")

    try:
        cmr_report = generate_cmr_report(mat_path, ecg_npy, max_tokens=args.max_tokens)
        saved = save_report(cmr_report, record["id"])
        print("=" * 60)
        print("CMR REPORT (generated by Llama 1B)")
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

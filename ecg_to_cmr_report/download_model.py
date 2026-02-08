"""
Download a small GGUF model for llama-cpp-python (no API, IRB-friendly).

Run once: python -m ecg_to_cmr_report.download_model

This downloads TinyLlama (~700MB) to models/ for use with llama-cpp-python only.
If you use USE_TRANSFORMERS=1, you do NOT need this: Transformers downloads
its own copy to ~/.cache/huggingface/ and uses that. So run this script only
if you plan to use the GGUF/llama-cpp backend (e.g. on a machine where it doesn't crash).
"""

from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
MODELS_DIR = PROJECT_ROOT / "models"
MODELS_DIR.mkdir(parents=True, exist_ok=True)

# TinyLlama 1.1B Chat, Q4 quantized - good for CPU, ~700MB
REPO = "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF"
FILE = "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"


def main():
    print(f"Downloading {FILE} to {MODELS_DIR}/")
    print("This may take a few minutes (~700MB)...")
    try:
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(
            repo_id=REPO,
            filename=FILE,
            local_dir=str(MODELS_DIR),
            local_dir_use_symlinks=False,
        )
        print(f"Saved to: {path}")
        print("Done! You can now run: python -m ecg_to_cmr_report.ecg_to_cmr_report")
    except ImportError:
        print("Need huggingface_hub: pip install huggingface_hub")
        print("Or download manually:")
        print(f"  https://huggingface.co/{REPO}/blob/main/{FILE}")
        print(f"  Save to: {MODELS_DIR / FILE}")


if __name__ == "__main__":
    main()

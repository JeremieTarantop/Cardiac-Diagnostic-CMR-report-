# Cardiac Diagnostic CMR Report

Generate **CMR-style (Cardiac Magnetic Resonance) reports** from ECG data using local LLMs. All processing can run locally (IRB-friendly) or on **Google Colab with GPU** for faster generation.

## Repo structure

- **`ecg_to_cmr_report/`** — Main package:
  - **PTB-XL + TinyLlama**: `e_to_c_llama1.py` — CMR from PTB-XL ECG (metadata + signal summary).
  - **PTB-XL + MedGemma 4B**: `e_to_c_medgemma4b.py` — Same pipeline with a medical LLM (HF token required).
  - **MEETI + TinyLlama**: `e_to_c_meeti_llama1.py` — CMR from MEETI records (report + LLM interpretation).
  - **Explore MEETI**: `explore_meeti.py` — Load MEETI .mat into a DataFrame or inspect one record by id.
  - **Visualize ECG**: `visualize_ecg.py` — Plot PTB-XL traces.
- **`data/`** — PTB-XL metadata and paths (large signals/MEETI not in repo; see below).
- **`scripts/`** — Download and preparation scripts.

## Quick start (local)

```bash
pip install transformers torch pandas numpy
# PTB-XL: put data in data/ (see data/README.md). Then:
USE_TRANSFORMERS=1 python -m ecg_to_cmr_report.e_to_c_llama1 --ecg-id 2
```

## Run on Google Colab (GPU)

For **much faster** generation (TinyLlama or MedGemma on GPU):

1. Open [Colab](https://colab.research.google.com/).
2. **Runtime → Change runtime type → T4 GPU** (or better).
3. Open the notebook **`notebooks/CMR_report_Colab_GPU.ipynb`** from this repo (e.g. clone the repo in a cell, then open it), or run the same steps as in that notebook.

The notebook clones this repo, installs dependencies, sets `USE_CUDA=1`, and runs the CMR pipeline on GPU. For MedGemma you’ll need a Hugging Face token (e.g. in a Colab secret).

## Data (not in repo)

- **PTB-XL**: Place `ptbxl_database.csv`, `data/ptbxl_with_labels/ecg_with_labels.csv`, and ECG files (e.g. `data/ptbxl_pclr_format/` or PTB-XL .npy) as in `data/README.md`.
- **MEETI**: Download from [Zenodo 15893351](https://zenodo.org/records/15893351) and put the `MEETI` folder in the project root (or set path in code). Raw ECG for MEETI is in [MIMIC-IV-ECG](https://physionet.org/content/mimic-iv-ecg/1.0/) (see `ecg_to_cmr_report/MEETI_RAW_ECG.md`).

## License and citation

Use according to the licenses of PTB-XL, MEETI, and MIMIC-IV-ECG. Cite the respective datasets and, if you use this code, the repo.

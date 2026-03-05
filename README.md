# OLD version, to be updated (March 2026)

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

## Run on Google Colab (GPU) — no data upload

**Recommended:** Use the **test-data** notebook. It uses the small PTB test set already in the repo — you don’t download or upload anything.

1. **Open in Colab:** [**Open CMR_report_Colab_TestData.ipynb**](https://colab.research.google.com/github/JeremieTarantop/Cardiac-Diagnostic-CMR-report-/blob/main/notebooks/CMR_report_Colab_TestData.ipynb)
2. **Runtime → Change runtime type → T4 GPU** (or better).
3. **Run all cells** in order. The notebook clones the repo, converts `data/ptbxl_test/` into the format the pipeline needs, and runs CMR generation.

**If you have your own data:** Use [CMR_report_Colab_GPU.ipynb](https://colab.research.google.com/github/JeremieTarantop/Cardiac-Diagnostic-CMR-report-/blob/main/notebooks/CMR_report_Colab_GPU.ipynb) and upload or mount your `data/` (see that notebook).

## Data (not in repo)

- **PTB-XL**: Place `ptbxl_database.csv`, `data/ptbxl_with_labels/ecg_with_labels.csv`, and ECG files (e.g. `data/ptbxl_pclr_format/` or PTB-XL .npy) as in `data/README.md`.
- **MEETI**: Download from [Zenodo 15893351](https://zenodo.org/records/15893351) and put the `MEETI` folder in the project root (or set path in code). Raw ECG for MEETI is in [MIMIC-IV-ECG](https://physionet.org/content/mimic-iv-ecg/1.0/) (see `ecg_to_cmr_report/MEETI_RAW_ECG.md`).

## License and citation

Use according to the licenses of PTB-XL, MEETI, and MIMIC-IV-ECG. Cite the respective datasets and, if you use this code, the repo.

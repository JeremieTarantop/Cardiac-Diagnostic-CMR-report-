# ECG to CMR Report

Takes **PTB-XL data** (metadata + ECG signal) and uses a **local Llama model** to generate a CMR-style report.

**Everything runs locally** — no API calls, suitable for IRB/healthcare data. Works on CPU (no GPU needed). When you get a GPU at Mass General, llama-cpp-python will use it automatically.

## How it works

1. **Load PTB-XL record** — Metadata + ECG waveform (12 leads)
2. **Summarize signal** — Min, max, mean per lead (mV)
3. **Build prompt** — Metadata + signal summary
4. **Call local Llama** — llama-cpp-python, runs on CPU

## Setup

1. **Install dependencies**:
   ```bash
   pip install pandas numpy llama-cpp-python
   ```

2. **Download a small model** (one-time, ~700MB):
   ```bash
   pip install huggingface_hub  # if not already
   python -m ecg_to_cmr_report.download_model
   ```
   This puts TinyLlama in `models/`. It runs on CPU, no GPU needed.

3. **Or download manually** — Get a GGUF file from [Hugging Face](https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF), save to `models/`, and set:
   ```bash
   export ECG_LLM_MODEL_PATH=/path/to/your/model.gguf
   ```

## Usage

### Run with 1 example

```bash
cd "/Users/tarantojeremie/Desktop/Research MIT"
python -m ecg_to_cmr_report.ecg_to_cmr_report
```

### Use in Python

```python
from ecg_to_cmr_report.ecg_to_cmr_report import generate_cmr_with_llama

cmr_report = generate_cmr_with_llama(ecg_id=1)
print(cmr_report)
```

## Functions

| Function | Purpose |
|----------|---------|
| `load_ptbxl_record(ecg_id)` | Load metadata + ECG signal, summarize waveform |
| `build_prompt(record)` | Build prompt for Llama |
| `call_llama_local(prompt)` | Run local model, return CMR text |
| `generate_cmr_with_llama(ecg_id)` | Full pipeline |

## Notes

- **IRB-friendly**: No data leaves your machine.
- **CPU-only**: TinyLlama runs fine on CPU. First run loads the model (~10–30 s).
- **Future GPU**: At Mass General, use a larger model and set `ECG_LLM_MODEL_PATH`; llama-cpp-python will use GPU if available.

# Where is the raw ECG data for MEETI?

You have the **correct** MEETI dataset. The [Zenodo MEETI package](https://zenodo.org/records/15893351) does **not** bundle raw ECG waveforms in the zip.

## What Zenodo MEETI contains

- **.mat files**: `id`, `report`, `LLM_Interpretation`, and (in some releases) per-beat FeatureDB parameters.
- **.png files**: plotted ECG images (for a subset of records).
- **No** `.dat` / `.hea` waveform files and **no** raw signal arrays inside the .mat.

## Where the raw signals are

From the [Zenodo data description](https://zenodo.org/records/15893351):

> "Raw ECG data and report: The **raw ECG signals and accompanying text reports are included directly from MIMIC-IV-ECG**."

So the raw signals are **in MIMIC-IV-ECG**, not inside the MEETI zip. MEETI reuses the same identifiers and folder layout as [MIMIC-IV-ECG on PhysioNet](https://physionet.org/content/mimic-iv-ecg/1.0/).

## How to get raw + report + LLM interpretation together

1. **Keep your MEETI folder** for:
   - `report`, `LLM_Interpretation`, and any FeatureDB fields in the .mat.
   - .png images when present.

2. **Get raw waveforms from MIMIC-IV-ECG** (PhysioNet):
   - Dataset: https://physionet.org/content/mimic-iv-ecg/1.0/
   - Same path layout: `files/pNNNN/pXXXXXXXX/sZZZZZZZZ/` with `ZZZZZZZZ.dat` and `ZZZZZZZZ.hea` (WFDB).
   - The **MEETI record id** (e.g. `47620441`) is the same as the **MIMIC-IV-ECG study_id**, so the path under MIMIC-IV-ECG is the same as under MEETI, but with `.dat`/`.hea` instead of `.mat`/`.png`.

3. **Match by id**: For MEETI id `47620441`, your MEETI .mat is at:
   `MEETI/p1000/p10005439/s47620441/47620441.mat`  
   The corresponding raw record in MIMIC-IV-ECG is:
   `files/p1000/p10005439/s47620441/47620441` (use with WFDB: `wfdb.rdrecord(path)`).

4. **Optional**: Use `get_mimic_ecg_path_for_meeti_id(id)` from `ecg_to_cmr_report.explore_meeti` to get the MIMIC-IV-ECG relative path (e.g. `files/p1000/p10005439/s47620441/47620441`). Then, if you have MIMIC-IV-ECG downloaded, load with [wfdb](https://physionet.org/content/wfdb-python/): `wfdb.rdrecord(mimic_iv_ecg_root / path)`.

## Summary

| What you want        | Source        | Location / format                          |
|----------------------|---------------|--------------------------------------------|
| Report, LLM text     | MEETI (Zenodo)| In the .mat (`report`, `LLM_Interpretation`) |
| Plotted image        | MEETI (Zenodo)| `{id}.png` next to the .mat (when present) |
| Raw ECG waveform     | MIMIC-IV-ECG | PhysioNet, same path, WFDB `.dat`/`.hea`   |

So you did **not** download the wrong dataset; raw ECG is in a separate dataset (MIMIC-IV-ECG) by design.

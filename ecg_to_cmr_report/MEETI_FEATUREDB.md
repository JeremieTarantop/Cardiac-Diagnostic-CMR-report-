# Where are the FeatureDB / per-beat ECG parameters in MEETI?

The [MEETI paper](https://arxiv.org/html/2507.15255v1) states that MEETI includes **quantitative ECG features for every beat in each lead**, extracted with the [FeatureDB](https://github.com/PKUDigitalHealth/FeatureDB) toolkit, and that they are stored **in the .mat file** (Table 1: *"featuredb_lead_X … Beat parameters were extracted from each lead"*).

## What we see in your MEETI .mat files

We scanned many `.mat` files in your MEETI folder. **Every file checked contains only three variables:**

- `id`
- `report`
- `LLM_Interpretation`

There are **no** `featuredb_lead_I`, `featuredb_lead_II`, … or any other FeatureDB/per-beat variables in these .mat files.

So in the **current Zenodo MEETI zip (v1, 3.3 GB)** that you downloaded, the per-beat parameters are **not** present in the .mat files.

## Where they are supposed to be (per paper)

- **Location:** Inside the same .mat as `id`, `report`, and `LLM_Interpretation`.
- **Variable names:** `featuredb_lead_X` with X = I, II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6.
- **Content (Table 2):** For each lead, beat-level parameters such as  
  HR, RR1, RR2, P_amplitude, P_duration, PR_interval, QRS_amplitude, QRS_duration, T_amplitude, T_duration, ST_duration, ST_form, QT_interval, QTc.

So either the Zenodo release you have is a version that was published **without** these fields in the .mat, or they are provided in a **different** file/version.

## What you can do

1. **Check Zenodo for updates**  
   [Zenodo record 15893351](https://zenodo.org/records/15893351) — look for a **newer version** (e.g. v2) or an **additional file** (e.g. “MEETI_parameters” or “FeatureDB”) that might contain the per-beat parameters.

2. **Check the MEETI GitHub repo**  
   [PKUDigitalHealth/MIMIC-IV-ECG-Ext-Text-Image](https://github.com/PKUDigitalHealth/MIMIC-IV-ECG-Ext-Text-Image) — README, releases, or issues may mention where to download FeatureDB data or a “full” .mat with `featuredb_lead_*`.

3. **Ask the authors**  
   The paper lists contacts (e.g. Hong Shenda, Feng Mengling). You can ask specifically: *“In which Zenodo file or version are the FeatureDB per-beat parameters (featuredb_lead_*) provided?”*

4. **Extract them yourself (if you have raw ECG)**  
   If you have the raw waveforms (e.g. from [MIMIC-IV-ECG](https://physionet.org/content/mimic-iv-ecg/1.0/)), you can run [FeatureDB](https://github.com/PKUDigitalHealth/FeatureDB) yourself to get the same per-beat parameters and align them to MEETI by study id.

## Summary

| Item                         | In your MEETI .mat? | Intended place (paper) |
|-----------------------------|---------------------|-------------------------|
| id, report, LLM_Interpretation | Yes                 | Same .mat               |
| featuredb_lead_I … V6       | No                  | Same .mat (Table 1)     |

So: **they are not in the MEETI files you have.** They should be in the .mat according to the paper; to get them you’ll need a different Zenodo version/file, the authors’ instructions, or to run FeatureDB on MIMIC-IV-ECG yourself.

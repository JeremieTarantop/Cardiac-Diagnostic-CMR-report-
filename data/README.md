# PTB-XL ECG Data

This directory contains ECG data downloaded from the PTB-XL dataset.

## Download Instructions

Download scripts are located in the `scripts/` folder. Run from project root:

### Option 1: Simple Download (Recommended)
```bash
cd "/Users/tarantojeremie/Desktop/Research MIT"
./scripts/download_ptbxl.sh
```

### Option 2: Limited to Exactly 100 Files
```bash
./scripts/download_ptbxl_limited.sh
```

### Option 3: Using curl (macOS)
```bash
./scripts/download_ptbxl_curl.sh
```

### Option 4: Python download script
```bash
python scripts/download_ptbxl.py
python scripts/download_ptbxl_metadata.py  # For metadata CSV
```

All downloads go to `data/ptbxl_test/`.

## File Format

PTB-XL files are in WFDB (Waveform Database) format:
- `.dat` files: Binary waveform data
- `.hea` files: Header files with metadata

## Converting to PCLR Format

The PCLR model expects:
- Shape: `(N, 4096, 12)` for 12-lead ECGs
- Values in millivolts
- 10 seconds of data interpolated to 4096 samples
- Lead order: I, II, III, aVR, aVL, aVF, V1, V2, V3, V4, V5, V6

See `convert_ptbxl_to_pclr.py` for a conversion script.

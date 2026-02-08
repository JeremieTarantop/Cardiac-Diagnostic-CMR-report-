# Scripts

This folder contains utility scripts for the Research MIT project.

## Data Download (PTB-XL)

| Script | Description |
|--------|-------------|
| `download_ptbxl.py` | Python script to download PTB-XL ECG files |
| `download_ptbxl_metadata.py` | Download PTB-XL metadata CSV |
| `download_ptbxl.sh` | Bash/wget download (all records100) |
| `download_ptbxl_limited.sh` | Bash download limited to 100 files |
| `download_ptbxl_curl.sh` | Bash/curl download (macOS-compatible) |

## Exploration

| Script | Description |
|--------|-------------|
| `explore_ptbxl_metadata.py` | Explore PTB-XL metadata and available labels |

Run from project root, e.g.:
```bash
python scripts/download_ptbxl.py
python scripts/explore_ptbxl_metadata.py
```

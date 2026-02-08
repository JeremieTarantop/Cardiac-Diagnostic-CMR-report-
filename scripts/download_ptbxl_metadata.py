#!/usr/bin/env python3
"""
Download PTB-XL metadata CSV file.
This file contains patient information, diagnoses, and clinical labels.
"""

import urllib.request
from pathlib import Path

# Project root is parent of scripts/
PROJECT_ROOT = Path(__file__).parent.parent
METADATA_URL = "https://physionet.org/files/ptb-xl/1.0.3/ptbxl_database.csv"
OUTPUT_FILE = PROJECT_ROOT / "data" / "ptbxl_database.csv"


def download_metadata():
    """Download the PTB-XL metadata CSV file."""
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    
    print("Downloading PTB-XL metadata CSV...")
    print(f"URL: {METADATA_URL}")
    print(f"Output: {OUTPUT_FILE}")
    print()
    
    try:
        urllib.request.urlretrieve(METADATA_URL, str(OUTPUT_FILE))
        print(f"✓ Successfully downloaded metadata to: {OUTPUT_FILE}")
        
        # Get file size
        file_size = OUTPUT_FILE.stat().st_size / (1024 * 1024)  # MB
        print(f"  File size: {file_size:.2f} MB")
        
        return True
    
    except Exception as e:
        print(f"✗ Error downloading metadata: {e}")
        return False


if __name__ == "__main__":
    download_metadata()

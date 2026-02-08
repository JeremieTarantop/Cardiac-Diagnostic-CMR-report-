#!/usr/bin/env python3
"""
Download PTB-XL ECG data files from PhysioNet.
This script downloads .dat and .hea files from the records100/ directory.
"""

import os
import re
import urllib.request
import urllib.parse
from pathlib import Path
from typing import List, Tuple

# Project root is parent of scripts/
PROJECT_ROOT = Path(__file__).parent.parent
BASE_URL = "https://physionet.org/files/ptb-xl/1.0.3/records100"


def get_subdirectories() -> List[str]:
    """Get list of subdirectories in records100/."""
    print("Fetching directory structure...")
    
    try:
        with urllib.request.urlopen(f"{BASE_URL}/") as response:
            html = response.read().decode('utf-8')
        
        # Find all subdirectory links (5-digit numbers)
        pattern = r'href="(\d{5}/)"'
        subdirs = re.findall(pattern, html)
        
        # Sort to get them in order
        subdirs = sorted(set(subdirs))
        print(f"Found {len(subdirs)} subdirectories")
        return subdirs
    
    except Exception as e:
        print(f"Error fetching subdirectories: {e}")
        return []


def get_files_in_subdirectory(subdir: str) -> List[str]:
    """Get list of .dat and .hea files in a subdirectory."""
    try:
        url = f"{BASE_URL}/{subdir}"
        with urllib.request.urlopen(url) as response:
            html = response.read().decode('utf-8')
        
        # Find all .dat and .hea files
        pattern = r'href="([^"]*\.(?:dat|hea))"'
        files = re.findall(pattern, html)
        
        # Prepend subdirectory path
        files = [f"{subdir}{f}" for f in files]
        return files
    
    except Exception as e:
        print(f"Error fetching files from {subdir}: {e}")
        return []


def download_file(file_path: str, output_dir: Path) -> bool:
    """Download a single file."""
    try:
        url = f"{BASE_URL}/{file_path}"
        output_path = output_dir / file_path
        
        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Download the file
        urllib.request.urlretrieve(url, str(output_path))
        return True
    
    except Exception as e:
        print(f"Error downloading {file_path}: {e}")
        return False


def main():
    """Main download function."""
    output_dir = PROJECT_ROOT / "data" / "ptbxl_test"
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 60)
    print("PTB-XL ECG Data Downloader")
    print("=" * 60)
    print(f"Output directory: {output_dir}")
    print()
    
    # Get list of subdirectories
    subdirs = get_subdirectories()
    
    if not subdirs:
        print("No subdirectories found. Exiting.")
        return
    
    # Get files from each subdirectory (limit to first 100 files total)
    print("\nCollecting file list from subdirectories...")
    all_files = []
    max_files = 100  # Limit to first 100 files
    
    for subdir in subdirs:
        files = get_files_in_subdirectory(subdir)
        all_files.extend(files)
        
        if len(all_files) >= max_files:
            all_files = all_files[:max_files]
            break
        
        print(f"Found {len(files)} files in {subdir} (total: {len(all_files)})")
    
    if not all_files:
        print("No files found. Exiting.")
        return
    
    print(f"\nDownloading {len(all_files)} files...")
    print("This may take a few minutes...\n")
    
    # Download each file
    successful = 0
    failed = 0
    
    for i, file_path in enumerate(all_files, 1):
        if download_file(file_path, output_dir):
            successful += 1
        else:
            failed += 1
        
        if i % 10 == 0 or i == len(all_files):
            print(f"Progress: {i}/{len(all_files)} files ({successful} successful, {failed} failed)")
    
    print()
    print("=" * 60)
    print("Download complete!")
    print("=" * 60)
    print(f"Files saved to: {output_dir}")
    print()
    
    # Count downloaded files
    dat_files = list(output_dir.rglob("*.dat"))
    hea_files = list(output_dir.rglob("*.hea"))
    
    print(f"Summary:")
    print(f"  .dat files: {len(dat_files)}")
    print(f"  .hea files: {len(hea_files)}")
    print()
    print("Note: PTB-XL files are in WFDB format.")
    print("Use data/convert_ptbxl_to_pclr.py to convert them for use with PCLR.")


if __name__ == "__main__":
    main()

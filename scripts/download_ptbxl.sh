#!/bin/bash

# Script to download first 100 ECG files from PTB-XL dataset
# PTB-XL is a large publicly available 12-lead ECG dataset
# Run from project root: ./scripts/download_ptbxl.sh

# Navigate to data directory (scripts/../data/ptbxl_test)
cd "$(dirname "$0")/../data/ptbxl_test"

echo "Downloading PTB-XL ECG data files..."
echo "This will download .dat and .hea files from records100/"

# Download files recursively from the records100 directory
# The --cut-dirs=3 removes the first 3 directory levels from the URL path
# -r: recursive
# -np: no parent (don't go up directories)
# -nH: no host directories
# -A: accept only .dat and .hea files
wget -r -np -nH --cut-dirs=3 -A "*.dat,*.hea" \
    https://physionet.org/files/ptb-xl/1.0.3/records100/

echo ""
echo "Download complete!"
echo "Files are located in: $(pwd)"
echo ""
echo "To see what was downloaded, run:"
echo "  find . -name '*.dat' | wc -l  # Count .dat files"
echo "  find . -name '*.hea' | wc -l  # Count .hea files"

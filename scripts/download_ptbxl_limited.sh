#!/bin/bash

# Script to download exactly the first 100 ECG files from PTB-XL dataset
# This version limits the download to exactly 100 record pairs (.dat + .hea)
# Run from project root: ./scripts/download_ptbxl_limited.sh

# Navigate to data directory
cd "$(dirname "$0")/../data/ptbxl_test"

echo "Downloading first 100 ECG files from PTB-XL dataset..."
echo "This may take a few minutes..."

# First, get the list of files available
echo "Fetching file list..."
wget -q -O - https://physionet.org/files/ptb-xl/1.0.3/records100/ | \
    grep -oP 'href="[^"]*\.(dat|hea)"' | \
    sed 's/href="//;s/"//' | \
    sort -u | \
    head -100 > /tmp/ptbxl_files.txt

# Download each file
count=0
while IFS= read -r file; do
    if [ -z "$file" ]; then continue; fi
    
    # Extract directory structure
    dir=$(dirname "$file" 2>/dev/null || echo ".")
    filename=$(basename "$file")
    
    # Create directory if needed
    mkdir -p "$dir"
    
    # Download the file
    wget -q --show-progress -O "$file" "https://physionet.org/files/ptb-xl/1.0.3/records100/$file"
    
    count=$((count + 1))
    if [ $((count % 10)) -eq 0 ]; then
        echo "Downloaded $count files..."
    fi
done < /tmp/ptbxl_files.txt

# Also download the .hea files for the same records
echo "Downloading corresponding .hea files..."
count=0
while IFS= read -r file; do
    if [ -z "$file" ]; then continue; fi
    hea_file="${file%.dat}.hea"
    dir=$(dirname "$hea_file" 2>/dev/null || echo ".")
    mkdir -p "$dir"
    wget -q --show-progress -O "$hea_file" "https://physionet.org/files/ptb-xl/1.0.3/records100/$hea_file" 2>/dev/null
    count=$((count + 1))
done < /tmp/ptbxl_files.txt

rm /tmp/ptbxl_files.txt

echo ""
echo "Download complete!"
echo "Files are located in: $(pwd)"
echo ""
echo "Summary:"
echo "  .dat files: $(find . -name '*.dat' | wc -l | tr -d ' ')"
echo "  .hea files: $(find . -name '*.hea' | wc -l | tr -d ' ')"
echo ""
echo "Note: PTB-XL files are in WFDB format. You may need to use:"
echo "  - wfdb Python package to read them"
echo "  - Or convert them to numpy arrays for use with PCLR"

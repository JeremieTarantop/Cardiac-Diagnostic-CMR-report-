#!/bin/bash

# Script to download first 100 ECG files from PTB-XL dataset using curl
# (macOS-compatible version)
# Run from project root: ./scripts/download_ptbxl_curl.sh

# Navigate to data directory
cd "$(dirname "$0")/../data/ptbxl_test"

echo "Downloading PTB-XL ECG data files..."
echo "This will download .dat and .hea files from records100/"
echo "This may take a few minutes..."

# Base URL
BASE_URL="https://physionet.org/files/ptb-xl/1.0.3/records100"

# Get the directory listing
echo "Fetching file list..."
curl -s "$BASE_URL/" | grep -oP 'href="[^"]*\.(dat|hea)"' | sed 's/href="//;s/"//' | sort -u > /tmp/ptbxl_files.txt

total_files=$(wc -l < /tmp/ptbxl_files.txt | tr -d ' ')
echo "Found $total_files files to download"
echo ""

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
    url="$BASE_URL/$file"
    output_path="$file"
    
    curl -s -L -o "$output_path" "$url"
    
    count=$((count + 1))
    if [ $((count % 10)) -eq 0 ]; then
        echo "Downloaded $count/$total_files files..."
    fi
done < /tmp/ptbxl_files.txt

rm /tmp/ptbxl_files.txt

echo ""
echo "Download complete!"
echo "Files are located in: $(pwd)"
echo ""
echo "Summary:"
echo "  .dat files: $(find . -name '*.dat' 2>/dev/null | wc -l | tr -d ' ')"
echo "  .hea files: $(find . -name '*.hea' 2>/dev/null | wc -l | tr -d ' ')"
echo ""
echo "Note: PTB-XL files are in WFDB format. You may need to use:"
echo "  - wfdb Python package to read them"
echo "  - Or convert them to numpy arrays for use with PCLR"

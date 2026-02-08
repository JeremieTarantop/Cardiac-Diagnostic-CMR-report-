#!/usr/bin/env python3
"""
Prepare PTB-XL data with labels for fine-tuning PCLR.
This script links your downloaded ECG files with the metadata CSV.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json

METADATA_FILE = Path(__file__).parent / "data" / "ptbxl_database.csv"
ECG_DIR = Path(__file__).parent / "data" / "ptbxl_pclr_format"
OUTPUT_DIR = Path(__file__).parent / "data" / "ptbxl_with_labels"


def load_metadata():
    """Load the PTB-XL metadata CSV."""
    print("Loading metadata...")
    df = pd.read_csv(METADATA_FILE)
    print(f"Loaded {len(df)} records")
    return df


def find_matching_ecgs(df):
    """Find which ECG files we have and match them with metadata."""
    print("\nFinding matching ECG files...")
    
    # Get list of downloaded ECG files
    ecg_files = list(ECG_DIR.rglob("*.npy"))
    print(f"Found {len(ecg_files)} ECG files")
    
    # Extract record IDs from filenames
    # Format: ./00000/00001_lr.npy -> 00000/00001_lr
    ecg_records = {}
    for ecg_file in ecg_files:
        # Get relative path from ECG_DIR
        rel_path = ecg_file.relative_to(ECG_DIR)
        # Remove .npy extension and normalize path separators
        record_key = str(rel_path.with_suffix('')).replace('\\', '/')
        # Remove leading ./ if present
        if record_key.startswith('./'):
            record_key = record_key[2:]
        ecg_records[record_key] = str(ecg_file)
    
    # Match with metadata using filename_lr column
    # CSV has format: "records100/00000/00001_lr"
    # We need to extract just "00000/00001_lr"
    matched_data = []
    for idx, row in df.iterrows():
        filename_lr = str(row['filename_lr'])
        # Remove "records100/" prefix if present
        if filename_lr.startswith('records100/'):
            filename_lr = filename_lr[11:]  # Remove "records100/"
        
        if filename_lr in ecg_records:
            matched_data.append({
            'ecg_id': row['ecg_id'],
            'ecg_file': ecg_records[filename_lr],
            'age': row['age'],
            'sex': row['sex'],
            'height': row['height'],
            'weight': row['weight'],
            'scp_codes': row['scp_codes'],
            'heart_axis': row['heart_axis'],
            'infarction_stadium1': row['infarction_stadium1'],
            'infarction_stadium2': row['infarction_stadium2'],
            'baseline_drift': row['baseline_drift'],
            'static_noise': row['static_noise'],
            'burst_noise': row['burst_noise'],
            'electrodes_problems': row['electrodes_problems'],
            'extra_beats': row['extra_beats'],
            'pacemaker': row['pacemaker'],
        })
    
    matched_df = pd.DataFrame(matched_data)
    print(f"Matched {len(matched_df)} ECG files with metadata")
    
    return matched_df


def show_available_labels(df):
    """Show what labels are available for prediction."""
    print("\n" + "=" * 60)
    print("Available Labels for Prediction:")
    print("=" * 60)
    
    # Age (regression)
    age_valid = df['age'].notna().sum()
    if age_valid > 0:
        print(f"\n1. AGE (Regression)")
        print(f"   - Valid values: {age_valid}/{len(df)}")
        print(f"   - Range: {df['age'].min():.1f} - {df['age'].max():.1f} years")
        print(f"   - Mean: {df['age'].mean():.1f} years")
    
    # Sex (classification)
    sex_valid = df['sex'].notna().sum()
    if sex_valid > 0:
        print(f"\n2. SEX (Binary Classification)")
        print(f"   - Valid values: {sex_valid}/{len(df)}")
        print(f"   - Distribution:")
        print(df['sex'].value_counts().to_string())
    
    # Height/Weight/BMI (regression)
    height_valid = df['height'].notna().sum()
    weight_valid = df['weight'].notna().sum()
    if height_valid > 0 or weight_valid > 0:
        print(f"\n3. HEIGHT/WEIGHT (Regression)")
        print(f"   - Height: {height_valid} valid values")
        print(f"   - Weight: {weight_valid} valid values")
        if height_valid > 0 and weight_valid > 0:
            # Calculate BMI where both are available
            bmi = df['weight'] / ((df['height'] / 100) ** 2)
            bmi_valid = bmi.notna().sum()
            print(f"   - BMI: {bmi_valid} valid values (calculated)")
    
    # SCP codes (multi-label classification)
    scp_valid = df['scp_codes'].notna().sum()
    if scp_valid > 0:
        print(f"\n4. SCP CODES (Multi-label Classification)")
        print(f"   - Valid values: {scp_valid}/{len(df)}")
        print(f"   - These are diagnostic codes (e.g., 'NORM', 'MI', 'STTC', etc.)")
        print(f"   - Example: {df['scp_codes'].iloc[0] if scp_valid > 0 else 'N/A'}")
    
    # Heart axis (classification)
    axis_valid = df['heart_axis'].notna().sum()
    if axis_valid > 0:
        print(f"\n5. HEART AXIS (Classification)")
        print(f"   - Valid values: {axis_valid}/{len(df)}")
        print(f"   - Unique values: {df['heart_axis'].nunique()}")
    
    # Infarction stadium (classification)
    inf1_valid = df['infarction_stadium1'].notna().sum()
    inf2_valid = df['infarction_stadium2'].notna().sum()
    if inf1_valid > 0 or inf2_valid > 0:
        print(f"\n6. INFARCTION STADIUM (Classification)")
        print(f"   - Stadium 1: {inf1_valid} valid values")
        print(f"   - Stadium 2: {inf2_valid} valid values")
    
    # Quality flags (binary classification)
    print(f"\n7. SIGNAL QUALITY FLAGS (Binary Classification)")
    for col in ['baseline_drift', 'static_noise', 'burst_noise', 
                'electrodes_problems', 'extra_beats', 'pacemaker']:
        valid = df[col].notna().sum()
        if valid > 0:
            if df[col].dtype == bool:
                true_count = (df[col] == True).sum()
            elif df[col].dtype in ['int64', 'float64']:
                true_count = (df[col] > 0).sum()
            else:
                true_count = "N/A (non-numeric)"
            print(f"   - {col}: {true_count}/{valid} positive cases")


def save_labeled_dataset(df):
    """Save the matched dataset with labels."""
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Save as CSV
    csv_file = OUTPUT_DIR / "ecg_with_labels.csv"
    df.to_csv(csv_file, index=False)
    print(f"\n✓ Saved labeled dataset to: {csv_file}")
    
    # Save summary
    summary = {
        'total_records': len(df),
        'available_labels': {
            'age': int(df['age'].notna().sum()),
            'sex': int(df['sex'].notna().sum()),
            'height': int(df['height'].notna().sum()),
            'weight': int(df['weight'].notna().sum()),
            'scp_codes': int(df['scp_codes'].notna().sum()),
            'heart_axis': int(df['heart_axis'].notna().sum()),
        }
    }
    
    summary_file = OUTPUT_DIR / "label_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    print(f"✓ Saved summary to: {summary_file}")


def main():
    print("=" * 60)
    print("PTB-XL Label Preparation")
    print("=" * 60)
    
    # Load metadata
    metadata_df = load_metadata()
    
    # Find matching ECGs
    matched_df = find_matching_ecgs(metadata_df)
    
    if len(matched_df) == 0:
        print("\n✗ No matching ECG files found!")
        print("Make sure you've run convert_ptbxl_to_pclr.py first")
        return
    
    # Show available labels
    show_available_labels(matched_df)
    
    # Save labeled dataset
    save_labeled_dataset(matched_df)
    
    print("\n" + "=" * 60)
    print("Note about LVEF:")
    print("=" * 60)
    print("PTB-XL does NOT include Left Ventricle Ejection Fraction (LVEF).")
    print("\nAlternative options:")
    print("1. Use other available labels (age, sex, diagnoses, etc.)")
    print("2. Look for other datasets that include LVEF:")
    print("   - MIMIC-IV (requires credentials)")
    print("   - UK Biobank (requires application)")
    print("   - Other research datasets")
    print("3. Use PTB-XL for other prediction tasks")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Explore PTB-XL metadata to see what clinical labels are available.
"""

import pandas as pd
import numpy as np
from pathlib import Path

# Project root is parent of scripts/
PROJECT_ROOT = Path(__file__).parent.parent
METADATA_FILE = PROJECT_ROOT / "data" / "ptbxl_database.csv"


def explore_metadata():
    """Load and explore the PTB-XL metadata."""
    print("Loading PTB-XL metadata...")
    print("=" * 60)
    
    # Load the CSV
    df = pd.read_csv(METADATA_FILE)
    
    print(f"\nDataset shape: {df.shape[0]} records, {df.shape[1]} columns")
    print("\n" + "=" * 60)
    print("Available columns:")
    print("=" * 60)
    
    # Show all columns
    for i, col in enumerate(df.columns, 1):
        print(f"{i:3d}. {col}")
    
    print("\n" + "=" * 60)
    print("Sample of first few rows:")
    print("=" * 60)
    print(df.head())
    
    print("\n" + "=" * 60)
    print("Looking for LVEF or ejection fraction related columns:")
    print("=" * 60)
    
    # Search for LVEF-related columns
    lvef_keywords = ['lvef', 'ejection', 'fraction', 'ef', 'ventricular']
    found = False
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in lvef_keywords):
            print(f"  ✓ Found: {col}")
            print(f"    Non-null values: {df[col].notna().sum()} / {len(df)}")
            if df[col].dtype in ['int64', 'float64']:
                print(f"    Range: {df[col].min():.2f} - {df[col].max():.2f}")
                print(f"    Mean: {df[col].mean():.2f}")
            found = True
    
    if not found:
        print("  ✗ No LVEF/ejection fraction columns found in PTB-XL")
    
    print("\n" + "=" * 60)
    print("Clinical/diagnostic columns (potential labels):")
    print("=" * 60)
    
    # Look for diagnostic/clinical columns
    clinical_keywords = ['diagnosis', 'scp', 'mi', 'infarction', 'arrhythmia', 
                       'age', 'sex', 'gender', 'height', 'weight', 'bmi']
    clinical_cols = []
    for col in df.columns:
        col_lower = col.lower()
        if any(keyword in col_lower for keyword in clinical_keywords):
            clinical_cols.append(col)
    
    if clinical_cols:
        for col in clinical_cols[:20]:  # Show first 20
            print(f"  • {col}")
            if df[col].dtype in ['int64', 'float64']:
                non_null = df[col].notna().sum()
                print(f"    ({non_null} non-null values)")
    else:
        print("  No obvious clinical columns found")
    
    print("\n" + "=" * 60)
    print("Data types summary:")
    print("=" * 60)
    print(df.dtypes.value_counts())
    
    print("\n" + "=" * 60)
    print("Records matching your downloaded ECGs:")
    print("=" * 60)
    
    # Check if we can match the downloaded records
    if 'ecg_id' in df.columns or 'filename' in df.columns:
        id_col = 'ecg_id' if 'ecg_id' in df.columns else 'filename'
        print(f"Using '{id_col}' column to match records")
        print(f"Sample IDs: {df[id_col].head(10).tolist()}")
    
    return df


if __name__ == "__main__":
    df = explore_metadata()
    
    print("\n" + "=" * 60)
    print("Next steps:")
    print("=" * 60)
    print("1. Review the columns above to find labels you want to predict")
    print("2. If LVEF is not available, consider:")
    print("   - Using other clinical labels (diagnoses, age, etc.)")
    print("   - Looking for other datasets that include LVEF")
    print("   - Using PTB-XL for other prediction tasks")

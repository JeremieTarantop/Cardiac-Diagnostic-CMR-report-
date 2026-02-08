"""
Simple ECG visualization script using DataFrames.

Loads PTB-XL ECG files with all metadata and displays everything clearly.

Usage:
    python -m ecg_to_cmr_report.visualize_ecg
    # Change the ecg_id in the script to see different patients
"""

from pathlib import Path
from typing import Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 12-lead names in PCLR order
LEAD_NAMES = ["I", "II", "III", "aVR", "aVL", "aVF", "V1", "V2", "V3", "V4", "V5", "V6"]

# Project root (parent of ecg_to_cmr_report folder)
PROJECT_ROOT = Path(__file__).parent.parent
PTBXL_CSV = PROJECT_ROOT / "data" / "ptbxl_database.csv"
ECG_LABELS_CSV = PROJECT_ROOT / "data" / "ptbxl_with_labels" / "ecg_with_labels.csv"


def load_patient_data(ecg_id: int) -> dict:
    """
    Load ALL information for one patient: metadata + ECG signal.

    Args:
        ecg_id: ECG ID from PTB-XL

    Returns:
        Dictionary with:
        - metadata: DataFrame row with all metadata
        - ecg_df: DataFrame with ECG signal (time + 12 leads)
        - ecg_file: Path to the ECG file
    """
    # Load metadata from ptbxl_database.csv
    metadata_df = pd.read_csv(PTBXL_CSV)
    patient_row = metadata_df[metadata_df["ecg_id"] == ecg_id]
    
    if patient_row.empty:
        raise ValueError(f"ECG ID {ecg_id} not found in ptbxl_database.csv")

    # Get ECG file path
    filename_lr = patient_row.iloc[0]["filename_lr"]
    # Convert "records100/00000/00001_lr" to our local path
    if filename_lr.startswith("records100/"):
        filename_lr = filename_lr[11:]  # Remove "records100/"
    ecg_file = PROJECT_ROOT / "data" / "ptbxl_pclr_format" / f"{filename_lr}.npy"

    # Also try ecg_with_labels.csv (has direct paths)
    if ECG_LABELS_CSV.exists():
        labels_df = pd.read_csv(ECG_LABELS_CSV)
        match = labels_df[labels_df["ecg_id"] == ecg_id]
        if not match.empty:
            ecg_file = Path(match.iloc[0]["ecg_file"])

    if not ecg_file.exists():
        raise FileNotFoundError(f"ECG file not found: {ecg_file}")

    # Load ECG signal as DataFrame
    ecg_array = np.load(ecg_file)
    duration = 10.0  # seconds
    time = np.linspace(0, duration, 4096)
    
    data = {"time": time}
    for idx, lead_name in enumerate(LEAD_NAMES):
        data[lead_name] = ecg_array[:, idx]
    ecg_df = pd.DataFrame(data)

    return {
        "metadata": patient_row.iloc[0],
        "ecg_df": ecg_df,
        "ecg_file": ecg_file,
    }


def display_patient_info(ecg_id: int):
    """
    Display all patient information clearly: metadata + ECG signal preview.

    Args:
        ecg_id: ECG ID to display
    """
    data = load_patient_data(ecg_id)
    metadata = data["metadata"]
    ecg_df = data["ecg_df"]

    print("=" * 80)
    print(f"PATIENT INFORMATION - ECG ID: {ecg_id}")
    print("=" * 80)

    # Basic demographics
    print("\n📋 DEMOGRAPHICS:")
    print(f"  Patient ID: {metadata.get('patient_id', 'N/A')}")
    print(f"  Age: {metadata.get('age', 'N/A')} years")
    sex_val = metadata.get('sex', None)
    if pd.notna(sex_val):
        sex_str = "Male" if sex_val == 1 else "Female"
        print(f"  Sex: {sex_str}")
    else:
        print(f"  Sex: N/A")
    print(f"  Height: {metadata.get('height', 'N/A')} cm")
    print(f"  Weight: {metadata.get('weight', 'N/A')} kg")

    # Recording info
    print("\n📅 RECORDING INFORMATION:")
    print(f"  Date: {metadata.get('recording_date', 'N/A')}")
    print(f"  Device: {metadata.get('device', 'N/A')}")
    print(f"  Site: {metadata.get('site', 'N/A')}")

    # ECG report (most important!)
    print("\n📝 ECG REPORT:")
    report = metadata.get('report', '')
    if pd.notna(report) and report:
        print(f"  {report}")
    else:
        print("  (No report available)")

    # SCP diagnostic codes
    print("\n🏥 DIAGNOSTIC CODES (SCP):")
    scp_codes = metadata.get('scp_codes', '')
    if pd.notna(scp_codes) and scp_codes:
        print(f"  {scp_codes}")
    else:
        print("  (No diagnostic codes)")

    # Heart axis
    heart_axis = metadata.get('heart_axis', '')
    if pd.notna(heart_axis) and heart_axis:
        print(f"\n🧭 HEART AXIS: {heart_axis}")

    # Signal quality
    print("\n📊 SIGNAL QUALITY:")
    quality_fields = {
        'baseline_drift': 'Baseline drift',
        'static_noise': 'Static noise',
        'burst_noise': 'Burst noise',
        'electrodes_problems': 'Electrode problems',
        'extra_beats': 'Extra beats',
        'pacemaker': 'Pacemaker',
    }
    for field, label in quality_fields.items():
        val = metadata.get(field, None)
        if pd.notna(val):
            status = "Yes" if val else "No"
            print(f"  {label}: {status}")

    # ECG signal summary
    print("\n📈 ECG SIGNAL (12-Lead):")
    print(f"  Shape: {ecg_df.shape} (4096 time samples × 13 columns)")
    print(f"  Duration: 10 seconds")
    print(f"  Sampling rate: ~409.6 Hz")
    print("\n  First few rows:")
    print(ecg_df.head(5).to_string(index=False))
    print("\n  Voltage ranges per lead:")
    for lead in LEAD_NAMES:
        min_val = ecg_df[lead].min()
        max_val = ecg_df[lead].max()
        mean_val = ecg_df[lead].mean()
        print(f"    {lead:4s}: {min_val:7.2f} to {max_val:7.2f} mV (mean: {mean_val:7.2f} mV)")

    print("\n" + "=" * 80)


def plot_ecg_from_file(filename: str, save_path: Optional[str] = None):
    """
    Load an ECG file and plot all 12 leads.

    Args:
        filename: Path to the .npy file
        save_path: Optional path to save the figure (e.g., "my_plot.png")
    """
    # Load numpy array
    if Path(filename).is_absolute():
        ecg_path = Path(filename)
    else:
        ecg_path = PROJECT_ROOT / filename

    ecg_array = np.load(ecg_path)
    duration = 10.0
    time = np.linspace(0, duration, 4096)

    # Create DataFrame
    data = {"time": time}
    for idx, lead_name in enumerate(LEAD_NAMES):
        data[lead_name] = ecg_array[:, idx]
    df = pd.DataFrame(data)

    # Create figure with 12 subplots (4 rows × 3 columns)
    fig, axes = plt.subplots(4, 3, figsize=(15, 10))
    fig.suptitle(f"12-Lead ECG: {Path(filename).name}", fontsize=16)

    # Plot each lead
    for idx, (lead_name, ax) in enumerate(zip(LEAD_NAMES, axes.flat)):
        ax.plot(df["time"], df[lead_name], linewidth=0.5, color="blue")
        ax.set_title(f"Lead {lead_name}", fontsize=10)
        ax.set_xlabel("Time (s)")
        ax.set_ylabel("Voltage (mV)")
        ax.grid(True, alpha=0.3)

        # Set reasonable y-axis limits
        y_min, y_max = df[lead_name].min(), df[lead_name].max()
        margin = (y_max - y_min) * 0.1
        ax.set_ylim(y_min - margin, y_max + margin)

    plt.tight_layout()

    if save_path:
        plt.savefig(save_path, dpi=150)
        print(f"Saved plot to: {save_path}")
    else:
        plt.show()


def plot_patient_ecg(ecg_id: int, save_path: Optional[str] = None):
    """
    Plot ECG for a specific patient (by ECG ID).

    Args:
        ecg_id: ECG ID
        save_path: Optional path to save the figure
    """
    data = load_patient_data(ecg_id)
    metadata = data["metadata"]
    ecg_file = data["ecg_file"]

    # Create title with patient info
    age = metadata.get('age', 'N/A')
    sex_val = metadata.get('sex', None)
    sex_str = "M" if sex_val == 1 else "F" if sex_val == 0 else "?"
    title = f"ECG ID {ecg_id} - Age {age}, {sex_str}"

    plot_ecg_from_file(str(ecg_file), save_path)


def main():
    """Main function: display all patient info and plot ECG."""
    # CHANGE THIS ECG_ID to see different patients
    ecg_id = 1

    # Display all information
    display_patient_info(ecg_id)

    # Plot ECG
    print("\n" + "=" * 80)
    print("Plotting ECG...")
    print("=" * 80)
    plot_patient_ecg(ecg_id)


if __name__ == "__main__":
    main()

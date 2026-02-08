"""
Convert PTB-XL WFDB format ECG files to PCLR-compatible format.

This script reads WFDB format files and converts them to numpy arrays
that can be used with the PCLR model.

Requirements:
    pip install wfdb numpy scipy
"""

import os
import numpy as np
from scipy import signal
from scipy.interpolate import interp1d
import wfdb
from pathlib import Path
from typing import List, Dict, Tuple


# PCLR expected lead order
PCLR_LEADS = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
PCLR_SAMPLES = 4096  # 10 seconds at ~409.6 Hz
PCLR_DURATION = 10.0  # seconds


def read_wfdb_record(record_path: str) -> Tuple[np.ndarray, Dict]:
    """
    Read a WFDB record and return the signal and metadata.
    
    Args:
        record_path: Path to the record (without .dat or .hea extension)
    
    Returns:
        signal: numpy array of shape (n_samples, n_leads)
        metadata: dictionary with record metadata
    """
    record = wfdb.rdrecord(record_path)
    return record.p_signal, {
        'fs': record.fs,  # Sampling frequency
        'sig_name': record.sig_name,  # Lead names
        'units': record.units,  # Units (usually mV)
        'comments': record.comments
    }


def convert_to_pclr_format(signal_data: np.ndarray, metadata: Dict, 
                           target_samples: int = PCLR_SAMPLES) -> np.ndarray:
    """
    Convert ECG signal to PCLR format.
    
    Args:
        signal_data: ECG signal array of shape (n_samples, n_leads)
        metadata: Dictionary with 'fs' (sampling frequency) and 'sig_name' (lead names)
        target_samples: Target number of samples (default 4096)
    
    Returns:
        PCLR-formatted ECG array of shape (target_samples, 12)
    """
    fs = metadata['fs']
    sig_names = metadata['sig_name']
    
    # Get current number of samples
    n_samples, n_leads = signal_data.shape
    
    # Calculate duration
    duration = n_samples / fs
    
    # Create output array
    output = np.zeros((target_samples, 12))
    
    # Map leads to PCLR order
    lead_map = {name.upper(): idx for idx, name in enumerate(PCLR_LEADS)}
    
    for lead_idx, lead_name in enumerate(sig_names):
        lead_name_upper = lead_name.upper()
        
        # Find corresponding PCLR lead index
        if lead_name_upper in lead_map:
            pclr_idx = lead_map[lead_name_upper]
            
            # Get the lead signal
            lead_signal = signal_data[:, lead_idx]
            
            # Convert to millivolts if needed (assuming units are in metadata)
            # Most PTB-XL files are already in mV, but check units if available
            
            # Interpolate to target_samples
            original_time = np.linspace(0, duration, n_samples)
            target_time = np.linspace(0, duration, target_samples)
            
            # Use linear interpolation
            interp_func = interp1d(original_time, lead_signal, 
                                 kind='linear', 
                                 bounds_error=False, 
                                 fill_value='extrapolate')
            interpolated = interp_func(target_time)
            
            output[:, pclr_idx] = interpolated
    
    return output


def process_ptbxl_directory(data_dir: str, output_dir: str = None) -> List[np.ndarray]:
    """
    Process all WFDB records in a directory and convert to PCLR format.
    
    Args:
        data_dir: Directory containing .dat and .hea files
        output_dir: Optional directory to save converted .npy files
    
    Returns:
        List of PCLR-formatted ECG arrays
    """
    data_path = Path(data_dir)
    ecgs = []
    
    # Find all .hea files (each .hea file corresponds to one record)
    hea_files = list(data_path.rglob('*.hea'))
    
    print(f"Found {len(hea_files)} ECG records")
    
    for i, hea_file in enumerate(hea_files):
        try:
            # Get record path (without extension)
            record_path = str(hea_file.with_suffix(''))
            
            # Read the record
            signal_data, metadata = read_wfdb_record(record_path)
            
            # Convert to PCLR format
            pclr_ecg = convert_to_pclr_format(signal_data, metadata)
            ecgs.append(pclr_ecg)
            
            # Save if output directory specified
            if output_dir:
                output_path = Path(output_dir)
                output_path.mkdir(parents=True, exist_ok=True)
                
                # Create filename from original record
                rel_path = hea_file.relative_to(data_path)
                output_file = output_path / rel_path.with_suffix('.npy')
                output_file.parent.mkdir(parents=True, exist_ok=True)
                np.save(output_file, pclr_ecg)
            
            if (i + 1) % 10 == 0:
                print(f"Processed {i + 1}/{len(hea_files)} records...")
                
        except Exception as e:
            print(f"Error processing {hea_file}: {e}")
            continue
    
    print(f"\nSuccessfully converted {len(ecgs)} ECG records")
    return ecgs


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Convert PTB-XL WFDB files to PCLR format')
    parser.add_argument('--input', '-i', type=str, 
                       default='ptbxl_test',
                       help='Input directory with WFDB files')
    parser.add_argument('--output', '-o', type=str,
                       default='ptbxl_pclr_format',
                       help='Output directory for .npy files')
    
    args = parser.parse_args()
    
    # Get absolute paths
    script_dir = Path(__file__).parent
    input_dir = script_dir / args.input
    output_dir = script_dir / args.output
    
    if not input_dir.exists():
        print(f"Error: Input directory {input_dir} does not exist")
        print("Please download the PTB-XL data first using download_ptbxl.sh")
        exit(1)
    
    print(f"Converting ECGs from {input_dir} to PCLR format...")
    print(f"Output will be saved to {output_dir}")
    print()
    
    ecgs = process_ptbxl_directory(str(input_dir), str(output_dir))
    
    if ecgs:
        # Stack all ECGs into a single array
        ecg_array = np.stack(ecgs)
        print(f"\nFinal array shape: {ecg_array.shape}")
        print(f"Ready for use with PCLR model!")

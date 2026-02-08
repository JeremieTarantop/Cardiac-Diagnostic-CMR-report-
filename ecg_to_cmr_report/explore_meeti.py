"""
Explore the MEETI dataset (Zenodo 15893351): load .mat records into a DataFrame
or show all information for one record by id.

Usage:
    python -m ecg_to_cmr_report.explore_meeti
    python -m ecg_to_cmr_report.explore_meeti --max-records 100
    python -m ecg_to_cmr_report.explore_meeti --id 47620441
"""

import argparse
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent
MEETI_ROOT = PROJECT_ROOT / "MEETI"


def find_mat_by_id(record_id: str) -> Optional[Path]:
    """Find the .mat file for a MEETI record id (filename is {id}.mat under MEETI)."""
    record_id = str(record_id).strip()
    # MEETI layout: .../s{id}/{id}.mat
    for mat_path in MEETI_ROOT.rglob(f"{record_id}.mat"):
        return mat_path
    return None


def get_mimic_ecg_path_for_meeti_id(record_id: str) -> Optional[str]:
    """
    Return the relative path (no extension) to the raw WFDB record in MIMIC-IV-ECG for this MEETI id.
    Raw ECG is not in the MEETI zip; it lives in MIMIC-IV-ECG on PhysioNet (same path layout).
    Use with: wfdb.rdrecord(mimic_root / path) if you have MIMIC-IV-ECG downloaded.
    """
    mat_path = find_mat_by_id(record_id)
    if mat_path is None:
        return None
    # MEETI path: .../MEETI/p1000/p10005439/s47620441/47620441.mat
    # MIMIC-IV-ECG path: files/p1000/p10005439/s47620441/47620441 (no extension for WFDB)
    try:
        parts = mat_path.relative_to(MEETI_ROOT).parts
        # parts = ('p1000', 'p10005439', 's47620441', '47620441.mat')
        base = str(parts[-1]).replace(".mat", "")
        # MIMIC-IV-ECG on PhysioNet uses files/pNNNN/pXXXXXXXX/sZZZZZZZZ/ZZZZZZZZ
        rel = "files/" + "/".join(parts[:-1] + (base,))
        return rel
    except ValueError:
        return None


def _to_scalar_or_array(v) -> str | np.ndarray:
    """Convert scipy loadmat value to a plain string or keep array."""
    if isinstance(v, str):
        return v.strip()
    if isinstance(v, np.ndarray):
        if v.size == 1:
            return str(np.asarray(v).flat[0]).strip()
        return v
    return str(v).strip()


def load_full_meeti_record(mat_path: Path) -> dict:
    """Load a MEETI .mat and return all keys/values (for single-record view)."""
    import scipy.io

    data = scipy.io.loadmat(str(mat_path), struct_as_record=False, squeeze_me=True)
    out = {"path": str(mat_path)}

    for key in sorted(data.keys()):
        if key.startswith("__"):
            continue
        v = data[key]
        out[key] = _to_scalar_or_array(v)
    return out


def print_record_info(record: dict, record_id: Optional[str] = None) -> None:
    """Print all MEETI information for one record in a readable way."""
    print("=" * 60)
    print("MEETI record — full information")
    print("=" * 60)
    print("path:", record.get("path", "N/A"))
    rid = record_id or record.get("id")
    if rid:
        mimic_path = get_mimic_ecg_path_for_meeti_id(str(rid))
        if mimic_path:
            print("raw_ecg (MIMIC-IV-ECG):", mimic_path)
            print("  (Raw waveform is in MIMIC-IV-ECG on PhysioNet, not in MEETI zip. See MEETI_RAW_ECG.md)")
    # Report if FeatureDB per-beat parameters are present (paper says they should be in .mat)
    featuredb_keys = [k for k in record if k.startswith("featuredb_lead_")]
    if featuredb_keys:
        print("FeatureDB (per-beat parameters): present —", sorted(featuredb_keys))
    else:
        print("FeatureDB (per-beat parameters): not found in this .mat (see MEETI_FEATUREDB.md)")
    print()

    for key in ("id", "report", "LLM_Interpretation"):
        if key not in record:
            continue
        val = record[key]
        if isinstance(val, (np.ndarray, np.generic)):
            val = np.asarray(val).tolist() if hasattr(val, "size") and val.size > 1 else str(np.asarray(val).flat[0])
        else:
            val = str(val)
        print("-" * 60)
        print(key)
        print("-" * 60)
        print(val)
        print()

    for key in sorted(record.keys()):
        if key in ("path", "id", "report", "LLM_Interpretation"):
            continue
        val = record[key]
        print("-" * 60)
        print(key)
        print("-" * 60)
        if isinstance(val, np.ndarray):
            print("shape:", val.shape, "dtype:", val.dtype)
            if val.size <= 20:
                print(val)
            else:
                print(val[:20], "...")
        else:
            print(val)
        print()


def _discover_mat_files(max_records: int = 200):
    """Find .mat files under MEETI, up to max_records (scans patient folders to avoid full tree)."""
    found = []
    for patient_dir in sorted(MEETI_ROOT.iterdir()):
        if not patient_dir.is_dir():
            continue
        for subject_dir in patient_dir.iterdir():
            if len(found) >= max_records:
                return found
            if not subject_dir.is_dir():
                continue
            for study_dir in subject_dir.iterdir():
                if len(found) >= max_records:
                    return found
                if not study_dir.is_dir():
                    continue
                for f in study_dir.glob("*.mat"):
                    found.append(f)
                    if len(found) >= max_records:
                        return found
    return found


def _load_mat_record(path: Path) -> dict:
    """Load one MEETI .mat and return a flat dict (id, report, LLM_Interpretation, path, any featuredb)."""
    import scipy.io

    data = scipy.io.loadmat(str(path), struct_as_record=False, squeeze_me=True)
    row = {"path": str(path)}

    for key in ("id", "report", "LLM_Interpretation"):
        if key in data:
            v = data[key]
            if hasattr(v, "strip"):
                row[key] = v.strip() if isinstance(v, str) else str(v).strip()
            else:
                row[key] = str(v).strip() if v.size == 1 else str(v)

    # Any key like featuredb_lead_I, featuredb_lead_II, etc. (store as repr or summary for explorer)
    for key in data:
        if key.startswith("__"):
            continue
        if key in row:
            continue
        v = data[key]
        if hasattr(v, "shape") and v.size > 1:
            row[f"{key}_shape"] = str(getattr(v, "shape", ""))
        elif hasattr(v, "dtype") and getattr(v.dtype, "names", None):
            row[f"{key}_fields"] = str(v.dtype.names)
    return row


def build_meeti_dataframe(max_records: int = 200) -> pd.DataFrame:
    """Build a DataFrame of MEETI records from .mat files."""
    paths = _discover_mat_files(max_records=max_records)
    if not paths:
        return pd.DataFrame()

    rows = []
    for p in paths:
        try:
            rows.append(_load_mat_record(p))
        except Exception as e:
            rows.append({"path": str(p), "load_error": str(e)})

    df = pd.DataFrame(rows)
    return df


def main():
    parser = argparse.ArgumentParser(description="Explore MEETI dataset (DataFrame + sample text, or one record by id)")
    parser.add_argument("--id", type=str, default=None, help="Show all MEETI information for this record id (e.g. 47620441)")
    parser.add_argument("--max-records", type=int, default=200, help="Max .mat files to load when not using --id (default 200)")
    args = parser.parse_args()

    if not MEETI_ROOT.exists():
        print(f"MEETI folder not found: {MEETI_ROOT}")
        return

    if args.id is not None:
        record_id = args.id.strip()
        print(f"Looking up MEETI record id: {record_id}")
        mat_path = find_mat_by_id(record_id)
        if mat_path is None:
            print(f"No .mat file found for id {record_id} under {MEETI_ROOT}")
            return
        print(f"Found: {mat_path}\n")
        record = load_full_meeti_record(mat_path)
        print_record_info(record, record_id=record_id)
        return

    print("Discovering MEETI .mat files...")
    df = build_meeti_dataframe(max_records=args.max_records)

    if df.empty:
        print("No .mat files found.")
        return

    print("\n" + "=" * 60)
    print("MEETI dataset overview (DataFrame)")
    print("=" * 60)
    print(f"Number of records: {len(df)}")
    print(f"Number of columns/features: {len(df.columns)}")
    print(f"Columns: {list(df.columns)}")
    print("\nDtypes:")
    print(df.dtypes.to_string())
    print("\nBasic stats (non-numeric):")
    for col in df.select_dtypes(include=["object"]).columns:
        if col in ("path", "load_error"):
            continue
        lens = df[col].dropna().astype(str).str.len()
        print(f"  {col}: len min={lens.min()}, max={lens.max()}, mean={lens.mean():.0f}")

    print("\n" + "=" * 60)
    print("Sample text: report (first 3 rows)")
    print("=" * 60)
    if "report" in df.columns:
        for i, r in enumerate(df["report"].dropna().head(3)):
            print(f"[{i}] {repr(r[:200])}{'...' if len(str(r)) > 200 else ''}")
    else:
        print("(no 'report' column)")

    print("\n" + "=" * 60)
    print("Sample text: LLM_Interpretation (first 2 rows, truncated)")
    print("=" * 60)
    if "LLM_Interpretation" in df.columns:
        for i, r in enumerate(df["LLM_Interpretation"].dropna().head(2)):
            s = str(r)[:500]
            print(f"[{i}] {s}...")
            print()
    else:
        print("(no 'LLM_Interpretation' column)")

    print("\n" + "=" * 60)
    print("Sample IDs and paths (first 5)")
    print("=" * 60)
    for _, row in df.head(5).iterrows():
        print("  id:", row.get("id", "N/A"), "| path:", row.get("path", "")[-80:])


if __name__ == "__main__":
    main()

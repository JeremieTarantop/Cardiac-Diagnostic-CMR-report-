# PTB-XL Labels Information

## Summary

**PTB-XL does NOT include Left Ventricle Ejection Fraction (LVEF).**

However, you have **50 ECG records** matched with metadata, and several other labels you can use for fine-tuning your PCLR model.

## Available Labels for Your 50 ECGs

### 1. **AGE** (Regression Task)
- ✅ All 50 records have age
- Range: 17-60 years
- Mean: 37.8 years
- **Use case**: Predict patient age from ECG

### 2. **SEX** (Binary Classification)
- ✅ All 50 records have sex
- Distribution: 28 female (0), 22 male (1)
- **Use case**: Predict patient sex from ECG

### 3. **SCP CODES** (Multi-label Classification)
- ✅ All 50 records have diagnostic codes
- These are ECG interpretation codes like:
  - `NORM`: Normal
  - `MI`: Myocardial Infarction
  - `STTC`: ST/T changes
  - `LVOLT`: Low voltage
  - `SR`: Sinus rhythm
  - And many more...
- **Use case**: Predict multiple diagnoses from ECG

### 4. **WEIGHT** (Regression)
- ✅ 41/50 records have weight
- **Use case**: Predict patient weight from ECG

### 5. **HEART AXIS** (Classification)
- ✅ 15/50 records have heart axis
- **Use case**: Classify electrical heart axis

### 6. **INFARCTION STADIUM** (Classification)
- ✅ 5/50 records have infarction staging
- **Use case**: Classify myocardial infarction stage

## Your Data Files

1. **ECG data** (PCLR format): `data/ptbxl_pclr_format/`
   - 50 numpy arrays, shape: (4096, 12)
   - Ready to use with PCLR model

2. **Labels CSV**: `data/ptbxl_with_labels/ecg_with_labels.csv`
   - Links each ECG file to its metadata/labels
   - Use this to create training datasets

## If You Need LVEF Specifically

Since PTB-XL doesn't have LVEF, here are your options:

### Option 1: Use Other Available Labels
Fine-tune PCLR to predict:
- Age (regression)
- Sex (classification)
- Diagnostic codes (multi-label)
- Weight (regression)

These are still clinically relevant tasks!

### Option 2: Find Datasets with LVEF
Datasets that may include LVEF:
- **MIMIC-IV**: Requires credentials, includes echocardiography data
- **UK Biobank**: Requires application, includes both ECG and echo data
- **Other research datasets**: May require collaboration/approval

### Option 3: Use PTB-XL for Other Tasks
PTB-XL is excellent for:
- ECG diagnosis prediction
- Age/sex prediction
- Signal quality assessment
- Multi-label classification tasks

## Next Steps

1. **Choose a label** you want to predict (e.g., age, sex, or diagnostic codes)
2. **Load your data**:
   ```python
   import pandas as pd
   import numpy as np
   
   # Load labels
   labels_df = pd.read_csv('data/ptbxl_with_labels/ecg_with_labels.csv')
   
   # Load ECGs
   ecg_files = labels_df['ecg_file'].tolist()
   ecgs = np.array([np.load(f) for f in ecg_files])
   
   # Get labels (e.g., age)
   ages = labels_df['age'].values
   ```

3. **Use the fine-tuning code** in your PCLR.ipynb notebook to train a model

## Example: Fine-tuning for Age Prediction

```python
# Load data
labels_df = pd.read_csv('data/ptbxl_with_labels/ecg_with_labels.csv')
ecg_files = labels_df['ecg_file'].tolist()
X = np.array([np.load(f) for f in ecg_files])  # Shape: (50, 4096, 12)
y = labels_df['age'].values  # Shape: (50,)

# Create fine-tuned model (from your notebook)
finetune_model = create_finetune_model_with_head(
    model, 
    num_classes=1, 
    task_type='regression'
)

# Train
finetune_model.fit(X, y, epochs=50, validation_split=0.2)
```

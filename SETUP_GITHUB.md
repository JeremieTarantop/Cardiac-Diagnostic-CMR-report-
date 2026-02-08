# Push this project to GitHub

Your repo: **https://github.com/tarantop/Cardiac-Diagnostic-CMR-report-.git**

Run these commands from the **project root** (the folder that contains `ecg_to_cmr_report`, `data`, `README.md`, etc.):

```bash
cd "/Users/tarantojeremie/Desktop/Research MIT"

# 1. Initialize git (if not already)
git init

# 2. Add the GitHub remote
git remote add origin https://github.com/tarantop/Cardiac-Diagnostic-CMR-report-.git

# 3. Stage files (.gitignore already excludes MEETI, large data, models, outputs)
git add .
git status   # check what will be committed

# 4. First commit
git commit -m "Initial commit: ECG to CMR report pipeline, Colab GPU notebook"

# 5. Push (main branch; create it if needed)
git branch -M main
git push -u origin main
```

If the repo already had a commit (e.g. README created on GitHub), use:

```bash
git pull origin main --rebase
git push -u origin main
```

**What is NOT pushed** (see `.gitignore`): `MEETI/`, `data/ptbxl_pclr_format/`, `data/ptbxl_test/`, `data/ptbxl_database.csv`, `models/*.gguf`, generated outputs, `__pycache__`. So the repo stays small; data and models are added locally or on Colab (upload/Drive).

**Colab**: Open [Colab](https://colab.research.google.com/), set GPU runtime, then open `notebooks/CMR_report_Colab_GPU.ipynb` from your repo (e.g. clone the repo in a cell and run the notebook).

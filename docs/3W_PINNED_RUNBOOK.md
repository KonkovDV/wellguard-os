# Pinned 3W loader runbook

## Pin

- Repository: `https://github.com/petrobras/3W`
- Dataset version: `2.0.0`
- Required local file: `<checkout>/dataset/dataset.ini`, with `DATASET = 2.0.0`
- Data format: Parquet instances under `<checkout>/dataset`
- Current public repository latest release observed: `v.1.80.0` (repository/toolkit release, not the dataset semantic version). Do not confuse the two.

## Commands

```bash
# after obtaining a local checkout through your approved data process
python -c "from wellguard.dataio.threew import write_manifest; write_manifest('/data/3W', 'artifacts/3w_manifest.json')"
python -c "from wellguard.dataio.threew import load_instance; print(load_instance('/data/3W/dataset/<instance>.parquet')[1])"
```

The loader never downloads data, silently maps ambiguous columns, or treats a public dataset run as GPN evidence. The manifest stores SHA-256 for `dataset.ini` and every Parquet file.

Pressure channels (`P-TPT`, `P-PDG`, `P-MON-CKP`, …) are documented in **Pa** for dataset 2.0.0; the loader converts them to canonical **bar** (`× 1e-5`) before any WellGuard QC/physics step.

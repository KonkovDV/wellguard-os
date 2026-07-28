# Shadow mode execution plan

## What is implemented now

`python -m wellguard.cli shadow <canonical.csv> --output shadow_decisions.jsonl`
(or `python shadow/run_shadow.py …`) replays fixed windows through the same pipeline and
writes an append-only JSONL journal under `artifacts/` only.

Each record includes: operator card, `model_version`, QC, optional `window_context`
(e.g. `existing_alarm_*` passthrough), and empty `expert_disposition` /
`expert_useful` / `expert_notes_code` slots for pilot review.

It is read-only: no SCADA write path, no actuator, no external network, no hidden upload.

## Gating sequence

1. **Data contract:** owner supplies anonymized CSV/Parquet plus tag dictionary, units, timezone, sample interval and event-label policy.
2. **Archive replay:** 3-6 weeks of history, split by time and well, with current alarms as baseline.
3. **Calibration freeze:** thresholds are frozen before the holdout period; no tuning on test windows.
4. **Read-only live shadow:** 4-8 weeks, decisions logged with timestamp, model version, input QC and operator disposition.
5. **Go/no-go:** compare detection delay, useful-alert rate, false alarms per shift, coverage, missingness and operator workload against baseline.

## Cannot be executed yet

The GPN archive, approved tag dictionary, asset owner, event labels and safe endpoint are not available in this workspace. The code and contract are ready; claiming an archive result now would be fabrication.

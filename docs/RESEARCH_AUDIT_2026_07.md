# Research and industry audit (updated Jul 2026 / third refresh)

## Decision

WellGuard remains a **read-only surveillance demonstrator for complicated ESP wells**:
event class + onset + evidence channels + next check. Not generic PdM, not safety, not control.

## Evidence reviewed (2024–2026)

| Source | Takeaway for WellGuard | Claim impact |
| --- | --- | --- |
| SPE 230862 — Explainable ESP Diagnostics (KOGS 2026 / AIQ–ADNOC) | Rules separate failures vs operating changes; sparse-sensor robustness | Governing rules + `sensor_coverage` transparency |
| SPE 229219 — Translating Physics into Intelligence | ML denoises physics rules | ML auxiliary in `benchmark/` |
| Sci. Reports 16:7005 (2026) — gas-lock / annulus valve | Amp osc, PIP osc/drop, rate decline, mild motor-t | Gas Mode A + supports |
| Appl. Sci. nodal multiphase ESP (field gas-lock examples) | Gas lock often PIP↑ + Pd/WHP↓ | Gas Mode B (`pip_rise_whp_drop_osc`) — same letter class |
| SPE 201476 — free gas case studies | Distinguish oscillations / lock / instability; need intake+WHP | WHP used as surface head proxy (no PDP required) |
| JPEPT 14:1071–1083 (2024) — intake plugging | Rate↓ + PIP↑ + annulus↑; low amp osc | `intake_restriction` + plugging supports |
| Rule-based ESP expert system (2025 preprint) | Underload / cooling IF–THEN rules | `underload_support`, `cooling_support` only |
| Sensors 25(8):2444 (2025) — MK-ESPFDM | Mechanism knowledge + DL | Mechanism-first design |
| 3W Dataset 2.0.0 — Sci. Data (2026) / arXiv:2507.01048 | Public early-detection benchmark | Loader pinned; **no field metric claim** |
| SPE 225271 / 225249 | Twin / HF electrical APC | Out of scope |
| Sci. Reports (2026) physics-informed RUL transformer; SPE 225275 | RUL / PdM life | **Forbidden** by claim freeze |

## Real-case pattern map → letter classes

| Field pattern | WellGuard class | Detector / notes |
| --- | --- | --- |
| Amp osc + PIP drop (± casing, cooling, WHP soft drop) | `gas_interference` | `pip_drop_osc` — not confirmed gas-lock |
| Amp osc + PIP rise + WHP drop | `gas_interference` | `pip_rise_whp_drop_osc` — ≠ plugging |
| Rate+load+current down + PIP/annulus up, low amp osc | `intake_restriction` | Plugging triage |
| Slow current+temp creep, flat rate | `water_breakthrough_candidate` | water_cut reinforce |
| Single-channel intake drift, quiet coupling | `sensor_fault_suspected` | KIP verify |
| Frequency step, affinity-consistent | `operation_change` | Suppress false complication |
| Bad QC / gaps / OOR | `sensor_quality_issue` | Fail closed |

## Explicitly not implemented

- APC / frequency writeback
- Digital twin / PDP product path
- RUL / RoF / remaining-life transformers
- Field accuracy or economics claims
- New event classes beyond the letter

## INDUSTRIX fit (unchanged)

Narrow edge component for production technologist workflow — not a platform/digital-twin competitor.

## Red-team / evidence floor

Synthetic mechanics only: 84 cases (7×12), red-team floors, expanding pytest suite.
See `docs/REDTEAM.md`, `docs/CLAIM_FREEZE.md`.

## Remaining blockers before any industrial accuracy claim

1. Owner archive + tag dictionary + units  
2. Expert labels / daily reports  
3. Time-based holdout (no shuffle)  
4. Shadow with disposition fill  
5. Go/no-go checklist (`docs/GO_NO_GO_CHECKLIST.md`)

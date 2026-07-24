# Research and industry audit, July 2026

## Decision
WellGuard is positioned as a **read-only surveillance demonstrator for complicated ESP wells**, not as generic predictive maintenance and not as a safety system. The narrow claim is deliberate: the operator receives an event class, time of onset, evidence channels and a next verification step.

## Evidence reviewed

- **3W Dataset 2.0.0, Scientific Data, 24 Apr 2026:** Petrobras' public multivariate time-series dataset adds instances, variables and a label and explicitly targets early detection with enough anticipation for corrective action. It is a valuable external validation source, but current WellGuard benchmark does not claim to have run on it until a release-pinned loader and label mapping are executed.
- **HF-ESPNet, Scientific Reports, 22 Jun 2026:** physics-informed multimodal transformer for ESP failure/RUL. Supports multimodal telemetry and physics consistency as a research direction, but also reinforces the need for field labels and degradation definitions.
- **Explainable ESP Diagnostics Enabled by Physics-Guided AI, SPE 230862, Feb 2026:** physics-guided rules help distinguish failure modes from operating changes and create actionable feedback under sparse labels. This is the closest methodological precedent for WellGuard's governing rule layer.
- **Hybrid Physics-ML Framework for Virtual Flow Metering in ESP-Lifted Oil Fields, SPE 233457, Jun 2026:** uses pressure, pump and completion features with well-based leakage-safe splitting. It validates the use of head/pressure/speed features, while showing that WellGuard should keep virtual metering as a future extension, not its core claim.
- **Time-aware ESP predictive maintenance, JPET, Aug 2025:** supports time-aware labels and trend features; it is not evidence of WellGuard performance.

## Industry fit

Public 2026 reporting describes Gazprom Neft as having more than 90% Russian IT substitution and about 80% digital-twin coverage across the value chain. That makes a generic digital twin, chatbot or broad AI platform a poor position. WellGuard should be framed as a small, auditable edge component that can feed an existing engineering workflow and does not compete with the company's platform.

INDUSTRIX public materials accept projects from idea to product and emphasize engineering specificity, practical significance, novelty and the ability to test at a real facility. WellGuard maps to:

- Level 1: **Разработка и эксплуатация месторождений**;
- Level 2: **Эксплуатация скважин и подземное оборудование**;
- Level 3: **Комплексные системы предиктивной аналитики динамического оборудования и увеличения скорости принятия решений**.

## What was rejected in the previous submissions

The prior projects were technically credible but either overlapped a saturated category, required laboratory proof, or used synthetic-only evidence without a narrow operating owner. WellGuard improves the causal chain: ESP well surveillance -> delayed recognition of gas interference/intake restriction/water breakthrough -> production technologist -> existing telemetry -> physics-guided cross-channel checks -> verify/triage recommendation -> shadow-mode KPI.

## Red-team conclusion

Current synthetic benchmark: 84 cases, 12 seeds, 7 scenarios; class accuracy 1.0, complication precision/recall 1.0, false complication alarms 0/hour, maximum detection delay 100 minutes. These numbers are **mechanics checks only**. The benchmark is intentionally separable and must not be presented as field accuracy.

Hardening added after audit: empty/missing/non-numeric/NaN/out-of-range input fails closed; robust scale handles flat sensors; explicit pressure-unit adapter; API upload and row limits; no unit inference; no persistence; no actuator or external network channel; **≥28 automated tests** (40+ in v0.1.4 including letter-alignment); CI and red-team gates included.

## Remaining blockers before industrial claim

1. Pin a public dataset release and publish an exact loader plus label mapping.
2. Add customer-data schema mapping and unit dictionary approved by the asset owner.
3. Establish a time-based and well-grouped holdout protocol before tuning thresholds.
4. Run retrospective baseline comparison against existing alarms.
5. Only then define field KPI and any economic scenario.

## Red-team edge-case closure, second pass

The second pass found two fail-open behaviors in the draft: an infinite value was not counted as missing, and a one-row/short history could be labelled normal. Both are now closed: non-finite values are QC defects and histories under 30 rows return `sensor_quality_issue`.

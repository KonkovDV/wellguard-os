# Security policy (advisory demonstrator)

## Scope

WellGuard OS is an **on-prem, read-only, advisory** research demonstrator.
It must never write to SCADA/АСУ ТП, never actuate equipment, and never be treated
as a safety instrument (СУЗ) or failure/accident confirmer.

## Reporting

Open a GitHub issue for suspected security problems in input handling, sandboxing,
or documentation that overclaims field safety. Do not include production telemetry
or personal data in public issues.

## Hardening already in tree

- Fail-closed QC (schema, ranges, timeline, NaN/Inf, quality flags)
- API upload size / row / **column** limits; CSV parse errors → 400; pipeline reject → **422**.
- Long `operator_annotation` (>64) fail-closed (anti-PII coded-notes rule).
- Optional `water_cut_pct` reinforces water-breakthrough only; cannot invent complication alone.
- Docker published only on host loopback (`127.0.0.1:8000`)
- Shadow outputs constrained under `artifacts/`
- Operator card disclaimers: heuristic score ≠ probability; `actuation: never`

## Out of scope

No RBAC, no signed audit log, no multi-tenant isolation — expected for a TRL-4
demonstrator. Production deployment requires the owner's security review.

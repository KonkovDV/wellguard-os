# THREAT_MODEL.md

- **Режим:** advisory-only, read-only. Система не пишет команды в АСУ ТП/SCADA, не управляет арматурой/ЭЦН.
- **Сеть:** локальный контур. Compose публикует API только на `127.0.0.1`; внутри контейнера процесс слушает `0.0.0.0` (иначе port-publish не работает).
- **Данные:** вход read-only; сервис не персистит телеметрию.
- **Границы:** нет RBAC, подписанных артефактов и неизменяемого аудита — это демонстратор, не средство безопасности.

## Input hardening (v0.1.1 → v0.1.3)

- Empty, missing-column, non-numeric, NaN/Inf, **out-of-range**, and invalid `quality_ok` fail closed as `sensor_quality_issue`.
- Channels are coerced to float once before physics; dtype mismatch cannot crash the rule layer.
- API upload limit: 25 MiB; row count checked from newline estimate **before** `read_csv`, then again after parse (max 2,000,000).
- No automatic unit inference; adapters require explicit pressure units.
- 3W loader converts documented Pa → canonical bar.
- Shadow decision logs are forced under `artifacts/` (no path traversal).
- Frequency step cannot suppress a gas/restriction signature; operation_change requires affinity-consistent response.
- Baseline uses the most stable early window to resist early-onset poisoning.
- No persistence, external network, actuator, or command channel.

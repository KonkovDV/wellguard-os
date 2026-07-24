# THREAT_MODEL.md

- **Режим:** advisory-only, read-only. Система не пишет команды в АСУ ТП/SCADA, не управляет арматурой/ЭЦН.
- **Сеть:** локальный контур. Compose публикует API только на `127.0.0.1`; внутри контейнера процесс слушает `0.0.0.0` (иначе port-publish не работает).
- **Данные:** вход read-only; сервис не персистит телеметрию.
- **Границы:** нет RBAC, подписанных артефактов и неизменяемого аудита — это демонстратор, не средство безопасности.

## Input hardening (v0.1.1 → v0.1.4)

- Empty, missing-required, non-numeric, NaN/Inf, **out-of-range**, invalid `quality_ok`, and **timeline** defects fail closed as `sensor_quality_issue`.
- Required: time, frequency, current, load, WHP, motor T, casing P, liquid rate, **`operating_mode`**.
- Conditional: **`intake_p_bar` optional** (letter: «если доступно»); without it gas/sensor-fault paths degrade.
- Optional extras accepted per GPN contract (water cut, gas, vibration, start/stop, alarms, report flags, annotations).
- Channels coerced to float once before physics; dtype mismatch cannot crash the rule layer.
- API upload limit: 25 MiB; row count checked before and after parse (max 2,000,000).
- No automatic unit inference; adapters require explicit pressure units; expected units exposed in QC.
- 3W loader converts documented Pa → canonical bar.
- Shadow decision logs forced under `artifacts/`.
- Operator card: `heuristic_score` is rule strength, not probability; `output_limits` on every card.
- Local UI: synthetic demo **or** read-only CSV upload.
- No persistence, external network, actuator, or command channel.

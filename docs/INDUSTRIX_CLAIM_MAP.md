# INDUSTRIX_CLAIM_MAP.md

| Критерий | Claim | Артефакт | Ограничение |
| --- | --- | --- | --- |
| Инженерная сущность | Физически мотивированные ESP-признаки + causal baseline + persistence | `wellguard/physics.py`, `wellguard/detect.py` | Не полная модель ЭЦН/PVT |
| Практическая значимость | Карточка для технолога: класс, onset, drivers, проверка | `wellguard/recommend.py`, `README.md` | Advisory-only |
| Новизна | Разделение осложнения, смены режима, sensor fault и quality issue | `wellguard/classify.py`, red-team | Синтетические классы пока разделимы |
| Испытуемость | Архив -> калибровка -> read-only shadow mode -> go/no-go | `docs/PILOT_PLAN.md` | Объект/теги подтверждает владелец |
| Российское ПО | Локальный Python/API/UI, loopback Docker, Apache-2.0 | `pyproject.toml`, `Dockerfile` | Интеграционные адаптеры требуют пилота |
| Evidence | 84 synthetic cases (7×12), ≥28 automated tests (suite grows with hardening), CI + RT probes | `benchmark/`, `tests/`, `artifacts/_redteam_probes.py` | Не полевая точность; 3W — loader, не field claim |
| Входы | Режим `operating_mode` обязателен; `intake_p_bar` опционален | `wellguard/schema.py` | Без приёма деградируют gas/sensor-fault |
| Опциональные поля | water_cut / gas / vibration / alarms / reports — контракт + passthrough | `data/contracts/gpn_archive_schema.json` | water_cut усиливает WB; остальное журнал/пилот |
| УТГ | Самооценка УТГ 4: воспроизводимый программный прототип | `docs/MODEL_CARD.md` | Не промышленная валидация |
| Claim freeze | Публичные утверждения = письмо INDUSTRIX | `docs/CLAIM_FREEZE.md` | Без расширения обещаний |
| Пилот | Go/no-go + разметка + shadow-report | `docs/GO_NO_GO_CHECKLIST.md`, `docs/EXPERT_LABELING.md`, `shadow/report_shadow.py` | Dry-run ≠ field claim |

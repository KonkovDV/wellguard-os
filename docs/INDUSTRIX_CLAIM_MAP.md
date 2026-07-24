# INDUSTRIX_CLAIM_MAP.md

| Критерий | Claim | Артефакт | Ограничение |
| --- | --- | --- | --- |
| Инженерная сущность | Физически мотивированные ESP-признаки + causal baseline + persistence | `wellguard/physics.py`, `wellguard/detect.py` | Не полная модель ЭЦН/PVT |
| Практическая значимость | Карточка для технолога: класс, onset, drivers, проверка | `wellguard/recommend.py`, `README.md` | Advisory-only |
| Новизна | Разделение осложнения, смены режима, sensor fault и quality issue | `wellguard/classify.py`, red-team | Синтетические классы пока разделимы |
| Испытуемость | Архив -> калибровка -> read-only shadow mode -> go/no-go | `docs/PILOT_PLAN.md` | Объект/теги подтверждает владелец |
| Российское ПО | Локальный Python/API/UI, loopback Docker, Apache-2.0 | `pyproject.toml`, `Dockerfile` | Интеграционные адаптеры требуют пилота |
| Evidence | 84 synthetic cases, 12 seeds, 24 tests, CI | `benchmark/`, `tests/` | Не полевая точность; 3W/ESPset пока validation sources |

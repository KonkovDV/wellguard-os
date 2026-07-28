# MODEL_CARD.md

- **Назначение:** предварительное выявление, классификация и временная локализация осложнённых режимов ЭЦН.
- **Архитектура:** physics-guided rule layer (governs) + вспомогательный ML-score (GroupKFold, не переопределяет решение).
- **Классы:** normal, gas_interference, intake_restriction, water_breakthrough_candidate, sensor_fault_suspected, operation_change, sensor_quality_issue.
- **Признаки (v0.1.10):** affinity features; gas Modes A/B (PIP drop vs PIP↑+WHP↓ + amp osc); plugging supports + underload; `sensor_coverage`; optional `gas_factor`/`gas_rate` reinforce gas only; `consistency` bundle.
- **Данные:** синтетика (генератор). Адаптеры: Petrobras 3W Dataset 2.0.0 (локальный pin + SHA-256), контракт обезличенного архива заказчика.
- **Карточка:** `heuristic_score` / `confidence` — сила срабатывания правил, **не вероятность события**; `output_limits` явно ограничивает вывод.
- **УТГ (самооценка):** 4 — воспроизводимый программный прототип и расчётный контур на синтетике; не полевая валидация и не готовность к промышленной эксплуатации.
- **Ограничения:** показатели синтетические, не полевые; advisory-only; не СУЗ; не подтверждает отказ/аварию; не выдаёт RUL; не пишет в АСУ ТП.
- **Научная опора:** `docs/RESEARCH_AUDIT_2026_07.md`, `docs/PHYSICS.md` — без field claim.

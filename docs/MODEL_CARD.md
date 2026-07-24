# MODEL_CARD.md

- **Назначение:** предварительное выявление, классификация и временная локализация осложнённых режимов ЭЦН.
- **Архитектура:** physics-guided rule layer (governs) + вспомогательный ML-score (GroupKFold, не переопределяет решение).
- **Классы:** normal, gas_interference, intake_restriction, water_breakthrough_candidate, sensor_fault_suspected, operation_change, sensor_quality_issue.
- **Данные:** синтетика (генератор). Реальные адаптеры: Petrobras 3W, ESPset (на пилоте).
- **Ограничения:** показатели синтетические, не полевые; advisory-only.

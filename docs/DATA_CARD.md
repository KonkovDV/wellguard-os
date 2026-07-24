# DATA_CARD.md

- **Demo/benchmark:** детерминированный синтетический генератор (`wellguard/generator.py`), 7 сценариев × seeds.
- **Рекомендуемые открытые данные для валидации:**
  - Petrobras **3W** (реальные нештатные события в скважинах): https://github.com/petrobras/3W
  - **ESPset** (вибро-данные отказов ЭЦН, 2025).
  - Equinor **Volve** (добыча/телеметрия).
- **На пилоте:** обезличенный архив куста ЭЦН заказчика.

## Public-data reproducibility boundary

WellGuard does not claim that the current demo has been trained on 3W or ESPset. The adapter layer is deliberately explicit: a public-data loader must map the exact release schema, declare units, and preserve the original event labels before any benchmark is reported. Until that loader is executed against a pinned dataset release, public datasets are **planned validation sources**, not evidence for the current metrics.

## Public-data reproducibility boundary

WellGuard does not claim that the current demo has been trained on 3W or ESPset. The adapter layer is deliberately explicit: a public-data loader must map the exact release schema, declare units, and preserve the original event labels before any benchmark is reported. Until that loader is executed against a pinned dataset release, public datasets are planned validation sources, not evidence for the current metrics.

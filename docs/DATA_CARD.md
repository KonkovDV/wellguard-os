# DATA_CARD.md

- **Demo/benchmark:** детерминированный синтетический генератор (`wellguard/generator.py`), 7 сценариев × 12 seeds = 84 кейса.
- **Рекомендуемые открытые данные для валидации (ещё не field evidence):**
  - Petrobras **3W** Dataset 2.0.0 — локальный pin + SHA-256 (`wellguard/dataio/threew.py`); loader не скачивает данные.
  - **ESPset** (вибро-данные отказов ЭЦН).
  - Equinor **Volve**.
- **На пилоте:** обезличенный архив заказчика по контракту `data/contracts/gpn_archive_schema.json`.

## Public-data reproducibility boundary

WellGuard does not claim that the current demo has been validated on 3W or ESPset.
The adapter layer is explicit: a public-data loader must map the exact release schema,
declare units, and preserve original event labels before any field benchmark is reported.
Until that run is executed and published against a pinned release, public datasets are
**planned validation sources**, not evidence for the current synthetic metrics.

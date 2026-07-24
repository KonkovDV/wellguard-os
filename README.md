# WellGuard OS v0.1.3

Открытый on-prem **адвайзорный демонстратор** раннего выявления, классификации и временной
локализации осложнённых режимов механизированной скважины (ЭЦН) по штатной телеметрии.
Physics-guided признаки + ML. **Advisory only.** Не управляет оборудованием, не пишет в АСУ ТП.

> Это исследовательский демонстратор, не средство противоаварийной защиты и не замена штатным системам.
> Показатели получены на **синтетике** и не являются полевой точностью.

## Почему это попадает в INDUSTRIX (причинно-следственная цепочка)

**Процесс:** эксплуатация осложнённого фонда ТРИЗ (ЭЦН). →
**Потеря:** газовые пробки, срыв подачи, засорение, обводнение и дрейф датчиков маскируются
переходными режимами → простои, недобор, лишние выезды, преждевременный отказ ЭЦН. →
**Пользователь:** технолог по добыче, инженер по мехфонду, диспетчер. →
**Входы:** ток/частота/загрузка ЭЦН, устьевые P/T, давление на приёме, дебит, затрубное давление. →
**Алгоритм:** physics-residual (законы подобия) + mode-aware базовая линия + CUSUM + hold-time + quality gate → класс события. →
**Действие:** приоритизация вмешательств, отделение осложнения от дрейфа датчика. →
**Эффект:** задержка обнаружения, precision/recall, ложные тревоги/смену, часы предотвращённого простоя.

## Одна команда

```bash
pip install -e ".[dev]"
python -m wellguard.cli demo --scenario gas_interference   # объяснимая карточка события
python -m benchmark.run_benchmark    # метрики + ML GroupKFold
python -m benchmark.redteam          # пороги приёмки, exit code 1 при нарушении
python run_tests.py                  # pytest
```

API (read-only, только 127.0.0.1): `uvicorn wellguard.api:app --host 127.0.0.1 --port 8000` 
UI: `streamlit run app.py` 
Docker: `docker compose up` (bind только loopback).

## Конвейер

QC (схема/единицы/полнота) → physics-признаки (head_coef, q_per_freq, current_per_q, current_var) →
mode-aware robust baseline → CUSUM + persistence hold-time → physics-guided классификация →
временная локализация onset → governed operator card.

**Классы:** normal, gas_interference, intake_restriction, water_breakthrough_candidate,
sensor_fault_suspected, operation_change, sensor_quality_issue.

## Пороги приёмки red-team (только синтетика)

| Метрика | Порог | Текущее (12 seeds × 7 сцен.) |
| --- | --- | --- |
| class accuracy | ≥ 0.95 | **1.00** |
| precision | ≥ 0.90 | **1.00** |
| recall | ≥ 0.75 | **1.00** |
| ложные тревоги / час | ≤ 0.5 | **0.0** |
| макс. задержка обнаружения | ≤ 120 мин | **100 мин** |
| sensor_fault как осложнение | 0 | **0** |

См. `docs/REDTEAM.md` и `artifacts/benchmark.json`.

## Новизна

Не «ещё один anomaly score» и не «предиктивка отказа насоса»: система **отделяет реальное
осложнение от неисправности датчика** через кросс-канальную физическую согласованность,
локализует onset во времени и даёт объяснимую карточку. Physics-guided rule layer управляет
решением; ML (GroupKFold, без утечки) — вспомогательный score.

## Данные для валидации

Demo — синтетика. Реальные открытые данные для адаптации: Petrobras **3W** (реальные
нештатные события в скважинах), **ESPset** (вибро-отказы ЭЦН), Equinor **Volve**. См. `docs/DATA_CARD.md`.

## Пилот

Ретроспектива → калибровка порогов на архиве → read-only shadow mode → go/no-go. `docs/PILOT_PLAN.md`.

## Лицензия

Apache-2.0.

## Audit status

В v0.1.1 закрыты fail-open случаи на пустых/неполных/NaN-данных, добавлены лимиты API-входа и явный адаптер единиц. Метрики benchmark остаются синтетическими; public-data validation не заявляется до воспроизводимого запуска на pinned release.

## Pinned 3W, GPN archive, shadow mode

- 3W loader: `wellguard/dataio/threew.py`, pinned to dataset 2.0.0, local-only, SHA-256 manifest.
- GPN archive contract: `data/contracts/gpn_archive_schema.json` and `wellguard/dataio/gpn_archive.py`.
- Shadow replay: `shadow/run_shadow.py`, fixed windows, JSONL decision log, read-only by construction.
- Runbooks: `docs/3W_PINNED_RUNBOOK.md`, `docs/SHADOW_MODE.md`.

No GPN archive or approved tag dictionary is bundled. The project reports no field result until the owner supplies those inputs.

## Release 0.1.3

Red-team hardening: out-of-range/quality_ok fail-closed, stable warmup baseline, affinity-gated operation_change, Pa→bar in 3W loader, packaged `wellguard.dataio`, API row pre-check, Docker publish-safe bind, sandboxed shadow outputs.

## Release 0.1.2

Pinned local-only 3W Dataset 2.0.0 loader, SHA-256 manifest, strict GPN archive contract, and fixed-window read-only shadow replay are included.

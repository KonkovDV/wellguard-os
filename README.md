# WellGuard OS v0.1.4

Открытый on-prem **адвайзорный демонстратор** раннего выявления, классификации и временной
локализации осложнённых режимов механизированной скважины (ЭЦН) по штатной телеметрии.
Physics-guided признаки + ML. **Advisory only.** Не управляет оборудованием, не пишет в АСУ ТП.

> Это исследовательский демонстратор, не средство противоаварийной защиты и не замена штатным системам.
> Показатели получены на **синтетике** и не являются полевой точностью.
> Самооценка **УТГ 4** — воспроизводимый программный прототип, не промышленная валидация.

## Почему это попадает в INDUSTRIX (причинно-следственная цепочка)

**Процесс:** эксплуатация осложнённого фонда ТРИЗ (ЭЦН). →
**Потеря:** газовые пробки, срыв подачи, засорение, обводнение и дрейф датчиков маскируются
переходными режимами → простои, недобор, лишние выезды, преждевременный отказ ЭЦН. →
**Пользователь:** технолог по добыче, инженер по мехфонду, специалист по добыче, диспетчер,
руководитель направления по эксплуатации скважин. →
**Входы:** время, частота/ток/загрузка ЭЦН, устьевое P, приёмное P (если доступно), T ПЭД,
затрубное P, дебит, **режим работы** (`operating_mode`), качество данных; опционально —
обводнённость, газ, вибрация, пуски/остановы, тревоги, рапорты, аннотации. →
**Алгоритм:** QC (схема/таймлайн/единицы/пропуски) → physics-residual → causal baseline →
CUSUM + hold-time → разделение осложнения / смены режима / качества → карточка. →
**Действие:** приоритизация проверки, отделение осложнения от дрейфа датчика. →
**Эффект:** задержка обнаружения, precision/recall, ложные тревоги/смену (на синтетике).

## Одна команда

```bash
pip install -e ".[dev]"
python -m wellguard.cli demo --scenario gas_interference   # объяснимая карточка события
python -m benchmark.run_benchmark    # метрики + ML GroupKFold
python -m benchmark.redteam          # пороги приёмки, exit code 1 при нарушении
python run_tests.py                  # pytest (≥28; currently 40+)
```

API (read-only, только 127.0.0.1): `uvicorn wellguard.api:app --host 127.0.0.1 --port 8000`  
UI: `streamlit run app.py` (синтетика **или** загрузка canonical CSV, только чтение)  
Docker: `docker compose up` (publish только loopback).

## Конвейер

QC (схема / временная шкала / ожидаемые единицы / полнота) → physics-признаки
(head_coef, q_per_freq, current_per_q, current_var) → causal robust baseline →
CUSUM + persistence hold-time → physics-guided классификация → onset → governed operator card
(`heuristic_score` ≠ вероятность; `output_limits` в каждой карточке).

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

См. `docs/REDTEAM.md` и `artifacts/benchmark.json`. Evidence заявки: **84** кейса, **7×12**,
автотесты **≥28** (в v0.1.4 suite расширен hardening/letter-alignment тестами).

## Новизна

Не «ещё один anomaly score» и не «предиктивка отказа насоса»: система **отделяет реальное
осложнение от неисправности датчика** через кросс-канальную физическую согласованность,
локализует onset во времени и даёт объяснимую карточку. Physics-guided rule layer управляет
решением; ML (GroupKFold, без утечки) — вспомогательный score.

## Данные для валидации

Demo — синтетика. Реальные открытые данные для адаптации: Petrobras **3W** (локальный loader
2.0.0 + SHA-256; не field claim), **ESPset**, Equinor **Volve**. См. `docs/DATA_CARD.md`.

## Пилот

Ретроспектива → калибровка порогов на архиве → read-only shadow mode → go/no-go.
`docs/PILOT_PLAN.md`, `docs/INDUSTRIX_CLAIM_MAP.md`.

## Лицензия

Apache-2.0.

## Release 0.1.4

Letter-alignment: `operating_mode` required; `intake_p_bar` optional; timeline QC; archive
optional extras contract; Streamlit CSV upload; heuristic score disclaimers; УТГ 4 in model card.

## Release 0.1.3

Red-team hardening: out-of-range/quality_ok fail-closed, absolute early-onset gas path,
affinity-gated operation_change, Pa→bar in 3W loader, packaged `wellguard.dataio`, API row
pre-check, Docker publish-safe bind, sandboxed shadow outputs.

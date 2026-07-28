# WellGuard OS

**On-prem адвайзорный демонстратор** раннего выявления и классификации осложнённых режимов
скважин с ЭЦН по штатной телеметрии. Physics-guided правила + QC. **Только рекомендация.**

[![CI](https://github.com/KonkovDV/wellguard-os/actions/workflows/ci.yml/badge.svg)](https://github.com/KonkovDV/wellguard-os/actions/workflows/ci.yml)
![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue)
![License](https://img.shields.io/badge/license-Apache%202.0-green)
![Mode](https://img.shields.io/badge/mode-advisory%20read--only-orange)

> **Не СУЗ и не АСУ ТП.** Не управляет оборудованием, не подтверждает отказ/аварию, не заменяет инженера.  
> Метрики — на **синтетике** (не полевая точность). Самооценка **УТГ 4** — воспроизводимый прототип.  
> Публичный периметр утверждений зафиксирован письмом INDUSTRIX 2026 → [`docs/CLAIM_FREEZE.md`](docs/CLAIM_FREEZE.md).

---

## Зачем

На осложнённом фонде технолог одновременно смотрит частоту, ток, загрузку, давления, температуру,
дебит и качество измерений. Газовая интерференция, ограничение приёма, рост обводнённости,
смена режима и дрейф датчика выглядят похоже в отдельных каналах.

**WellGuard OS** собирает согласованную **карточку события**: какой класс отклонения,
когда началось (onset), какие каналы подтверждают вывод и что проверить в первую очередь.

## Что умеет (и чего не умеет)

| Умеет | Не умеет / не заявляет |
| --- | --- |
| QC схемы, таймлайна, диапазонов, NaN/Inf | Полевую точность и экономический эффект |
| Physics-признаки + causal baseline + hold-time | RUL / остаточный ресурс |
| Отделить осложнение / смену режима / sensor fault / quality | Запись в АСУ ТП, команды, СУЗ |
| Объяснимая карточка + heuristic score ≠ вероятность | Подтверждение отказа или аварии |
| CLI, read-only API/UI, Docker loopback | Автономную эксплуатацию |
| Синтетика, red-team gate, shadow JSONL, контракт архива | Завершённую валидацию на 3W/архиве заказчика |

## Быстрый старт

```bash
pip install -e ".[dev]"

python -m wellguard.cli demo --scenario gas_interference
python -m benchmark.redteam          # exit 1 при нарушении порогов
python run_tests.py                  # pytest
python artifacts/_redteam_probes.py  # adversarial probes
```

```bash
# Read-only API (только loopback)
uvicorn wellguard.api:app --host 127.0.0.1 --port 8000

# UI: синтетика или CSV
streamlit run app.py

# Пилотный dry-run контур
python -m wellguard.cli export-demo --scenario gas_interference
python -m wellguard.cli shadow artifacts/demo_canonical.csv --window 400 --step 80
python -m wellguard.cli shadow-report artifacts/shadow_decisions.jsonl

docker compose up   # publish 127.0.0.1:8000 → контейнер
```

## Конвейер

```text
CSV/архив
  → coerce + QC (схема, единицы, таймлайн, ranges, quality)
  → physics features (head_coef, q_per_freq, current_per_q, current_var)
  → causal robust baseline + CUSUM + persistence hold-time
  → rule layer: осложнение | смена режима | sensor fault | quality | normal
  → operator card (explanation, drivers, output_limits, actuation=never)
```

### Классы карточки

| Класс | Смысл для технолога |
| --- | --- |
| `gas_interference` | Проверить газовый режим / сепарацию / частоту |
| `intake_restriction` | Проверить приём / подачу / возможное засорение |
| `water_breakthrough_candidate` | Возможный рост обводнённости — подтвердить замером |
| `sensor_fault_suspected` | Канал давления изменился без отклика подачи/тока |
| `operation_change` | Смена режима (частота / declared mode), не осложнение |
| `sensor_quality_issue` | Данные непригодны — решение не выносится |
| `normal` | В пределах ожидаемого режима |

`heuristic_score` / `confidence` — **сила правила**, не вероятность события.

## Входные данные

**Обязательные:** `t_min`, `freq_hz`, `whp_bar`, `current_a`, `load_pct`, `q_liq_m3d`,
`motor_t_c`, `casing_p_bar`, `operating_mode`.

**Условно:** `intake_p_bar` (если доступно; без него деградируют gas / sensor-fault).

**Опционально (контракт архива):** обводнённость, газ, вибрация, пуски/остановы,
тревоги АСУ, флаги рапортов, короткие coded-аннотации.  
`water_cut_pct` только **усиливает** кандидата обводнённости, не создаёт его в одиночку.

См. [`data/contracts/gpn_archive_schema.json`](data/contracts/gpn_archive_schema.json).

## Evidence (синтетика)

Red-team пороги (`python -m benchmark.redteam`) — **механика на синтетике**, не поле:

| Метрика | Порог | Текущее |
| --- | --- | --- |
| Class accuracy | ≥ 0.95 | **1.00** |
| Precision (осложнения) | ≥ 0.90 | **1.00** |
| Recall (осложнения) | ≥ 0.75 | **1.00** |
| Ложные тревоги осложнений / час | ≤ 0.5 | **0.0** |
| Макс. задержка обнаружения | ≤ 120 мин | **100 мин** |
| Sensor fault → complication | 0 | **0** |

Контур заявки: **84** кейса (7 сценариев × 12 seeds), автотесты **≥ 28** (сейчас расширенный suite),
CI + adversarial probes. Подробности: [`docs/REDTEAM.md`](docs/REDTEAM.md), [`docs/THREAT_MODEL.md`](docs/THREAT_MODEL.md).

## Пилот у владельца объекта

Архив → разметка → калибровка на истории → holdout → **read-only shadow** → go/no-go.

| Документ | Содержание |
| --- | --- |
| [`docs/PILOT_PLAN.md`](docs/PILOT_PLAN.md) | 10 шагов из письма |
| [`docs/GO_NO_GO_CHECKLIST.md`](docs/GO_NO_GO_CHECKLIST.md) | Продолжение / доработка / остановка |
| [`docs/EXPERT_LABELING.md`](docs/EXPERT_LABELING.md) | Шаблон экспертной разметки |
| [`docs/INDUSTRIX_CLAIM_MAP.md`](docs/INDUSTRIX_CLAIM_MAP.md) | Claim → артефакт |
| [`docs/MODEL_CARD.md`](docs/MODEL_CARD.md) | Модель / УТГ 4 / ограничения |
| [`SECURITY.md`](SECURITY.md) | Security policy демонстратора |

## Карта репозитория

```text
wellguard/          ядро: schema, physics, classify, API, CLI, dataio
benchmark/          синтетический бенчмарк + red-team gate
shadow/             read-only replay + dry-run report
tests/              pytest (letter / hardening / pilot)
data/contracts/     контракт обезличенного архива
data/templates/     шаблон экспертной разметки
docs/               physics, threat model, pilot, claim freeze
artifacts/          локальные demo/shadow выходы (не field evidence)
```

## Лицензия

Apache-2.0. Версия пакета: см. `pyproject.toml` / `wellguard.__version__`.

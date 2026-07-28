# EXPERT_LABELING.md — шаблон разметки эпизодов

Шаблон для архивной проверки и shadow-оценки из письма INDUSTRIX.
Не заменяет суточные рапорты; служит согласованной таблицей эпизодов.

## Файл

`data/templates/expert_labeling_template.csv`

## Поля

| Поле | Смысл |
| --- | --- |
| `well_id_hash` | Обезличенный идентификатор скважины |
| `episode_id` | Локальный ID эпизода |
| `t_start_min` / `t_end_min` | Интервал на той же шкале, что и `t_min` в архиве |
| `expert_class` | Один из классов WellGuard **или** `unknown` / `other` |
| `plant_alarm_active` | 1 = в интервале была действующая тревога АСУ |
| `confirmed` | 1 = эпизод подтверждён экспертом как реальное событие разбора |
| `useful_for_technologist` | 1 = карточка/разбор был бы полезен (заполняется и на shadow) |
| `notes_code` | Короткий код (не PII): `RAPORT_OK`, `FREQ_STEP`, `CHECK_KIP`, … |
| `source` | `daily_report` / `technologist` / `alarm_review` / `baseline` |

## Допустимые `expert_class`

`normal`, `gas_interference`, `intake_restriction`, `water_breakthrough_candidate`,
`sensor_fault_suspected`, `operation_change`, `sensor_quality_issue`, `unknown`, `other`

## Правила

1. Разметка **до** калибровки порогов на holdout (письмо: без подгонки под тест).
2. Не вносить ФИО, названия кустов, координаты, свободный текст с ПДн.
3. Несколько экспертов → отдельные файлы или суффикс в `episode_id`.
4. На shadow те же коды используются в JSONL-полях `expert_disposition` /
   `expert_useful` / `expert_notes_code` (заполняются вручную при разборе журнала).

## Связь с go/no-go

Заполненный шаблон + shadow-отчёт → разделы B3/B6 и C2–C6 в
`docs/GO_NO_GO_CHECKLIST.md`.

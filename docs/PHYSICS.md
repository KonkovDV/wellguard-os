# PHYSICS.md — допущения, границы и научная опора

WellGuard OS использует **упрощённые, физически мотивированные признаки**, не полную
электро-гидравлическую модель ЭЦН и не digital twin сепаратора.

## Признаки

| Признак | Формула / смысл | Опора |
| --- | --- | --- |
| `head_coef` | (intake − whp) / (f/50)² — H ~ f² | affinity laws; head loss → газ/срыв |
| `q_per_freq` | q / (f/50) — Q ~ f | засорение приёма / потеря подачи |
| `current_per_freq` | I / (f/50) | жидкостный отклик на шаг частоты |
| `current_per_q` | I / \|q\| | прокси плотности / обводнённости |
| `current_var` | rolling std тока | газовые пробки / vapour-lock на штатной телеметрии |
| `intake_var` | rolling std PIP | колебания приёма (Sci. Reports gas-lock) |
| casing / rate / PIP osc / cooling / WHP drop | optional gas supports | усиливают `gas_interference` |
| Gas Mode B | PIP↑ + WHP↓ + amp osc | тот же класс; ≠ plugging |
| pip_rise / annulus / head / underload | restriction supports | JPEPT plugging + expert underload |

## Что поддержано литературой 2025–2026 (без field claim)

- **SPE 230862 (2026):** physics-guided rules отделяют режимы/faults при редких метках — наш rule layer.
- **SPE 229219 (2025/26):** ML как denoiser над экспертными правилами — ML у нас вспомогательный (benchmark).
- **Sci. Reports (2026) gas-lock:** ток + PIP osc/drop + rate + mild motor-t — Gas Mode A.
- **Appl. Sci. / SPE 201476:** gas-lock field pattern PIP↑ + WHP/Pd↓ + amp osc — Gas Mode B (тот же класс письма).
- **JPEPT (2024) intake plugging:** подача↓ при PIP↑, низкая osc тока — `intake_restriction`.
- **SPE 230862:** sparse-sensor transparency → `sensor_coverage` в drivers.
- **Sci. Reports RUL transformer (2026) / SPE 225275:** **запрещены** claim freeze.
- **SPE 225271 / 225249:** twin / HF APC — **вне scope** письма.
- **3W Dataset 2.0.0 (Scientific Data 2026):** публичный источник для будущей внешней проверки; loader pin есть, field run не заявлен.

## Чего модель НЕ делает

- не решает полную гидравлику / PVT / многофазность;
- не оценивает efficiency газосепаратора и не пишет в APC;
- не выдаёт RUL / RoF;
- пороги на синтетике — требуют рекалибровки на архиве владельца;
- не является СУЗ.

from __future__ import annotations

# Governed operator recommendation. Advisory only: proposes a CHECK, never an action
# on equipment. Maps an event class to a human-facing card.

RECS = {
    "normal": ("no_action", "Режим в норме. Действий не требуется."),
    "gas_interference": ("check", "Проверить газовый режим: колебания тока и падение давления на приёме. Рассмотреть газосепаратор/частоту."),
    "intake_restriction": ("check", "Проверить приём насоса: устойчивое падение подачи и загрузки. Возможно засорение/срыв подачи."),
    "water_breakthrough_candidate": ("monitor", "Возможный рост обводнённости: медленный рост тока и температуры. Подтвердить замером обводнённости."),
    "sensor_fault_suspected": ("verify_sensor", "Подозрение на неисправность датчика: давление на приёме изменилось без отклика подачи/тока. Сверить КИП."),
    "operation_change": ("no_action", "Зафиксирована смена режима (частота). Физика согласована, осложнения нет."),
    "sensor_quality_issue": ("verify_data", "Низкое качество данных в окне. Решение не выносится до восстановления телеметрии."),
}


def operator_card(cls: dict) -> dict:
    action, text = RECS.get(cls["event_class"], ("monitor", "Наблюдение."))
    card = {
        "event_class": cls["event_class"],
        "recommended_action": action,
        "explanation": text,
        "onset_index": cls["onset_index"],
        "confidence": round(float(cls["confidence"]), 3),
        "is_complication": cls["is_complication"],
        "drivers": cls.get("drivers", {}),
        "tail_completeness": cls.get("tail_completeness"),
        "advisory_only": True,
        "actuation": "never",
    }
    qc = cls.get("qc")
    if isinstance(qc, dict):
        card["qc"] = {
            "schema_ok": qc.get("schema_ok"),
            "completeness": qc.get("completeness"),
            "out_of_range": qc.get("out_of_range"),
            "numeric_missing": qc.get("numeric_missing"),
            "issues": list(qc.get("issues") or []),
        }
    return card

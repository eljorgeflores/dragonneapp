"""Datos de ejemplo para validar el template sin IA."""

MOCK_REVENUE_REPORT = {
    "cover": {
        "hotel_name": "Hotel Boutique Ejemplo",
        "report_title": "Diagnóstico ejecutivo de revenue y distribución",
        "period_label": "2025-01-01 — 2025-01-31",
        "prepared_by": "Dragonné",
        "report_date": "2025-02-15",
    },
    "executive_summary": (
        "La operación muestra concentración de demanda en fin de semana con ADR estable, "
        "pero dependencia elevada de OTAs en esas noches. El canal directo participa poco "
        "cuando la demanda es fuerte. La prioridad inmediata es proteger tarifa en noches "
        "altas y empujar visibilidad directa sin disparar comisión. "
        "La lectura estratégica: el hotel compite bien en tarifa pública pero cede margen neto "
        "por mix de canal en las fechas donde ya tiene poder de pricing."
    ),
    "key_findings": [
        {
            "title": "ADR más bajo en OTA principal vs directo en sábados",
            "impact": "high",
            "diagnosis": "En sábados el ADR del canal OTA líder queda 8–12% bajo respecto al directo en el mismo periodo.",
            "business_implication": "Erosiona margen neto en las noches donde el hotel ya podría captar tarifa plena.",
            "recommended_action": "Revisar paridad y restricciones de estancia mínima en fines de semana; alinear BAR con estrategia directa.",
        },
        {
            "title": "Poca producción directa entre domingo y jueves",
            "impact": "medium",
            "diagnosis": "El mix entre semana depende de OTAs y tarifas promocionales.",
            "business_implication": "Mayor costo de distribución en días de demanda blanda.",
            "recommended_action": "Paquetes y bundles solo en directo para noches flojas; medir conversión del motor.",
        },
        {
            "title": "Brecha de paridad puntual en suites y habitación premium",
            "impact": "low",
            "diagnosis": "En 3 fechas el BAR directo quedó por debajo del OTA en categoría premium.",
            "business_implication": "Riesgo de canibalización y percepción de valor incoherente en upsell.",
            "recommended_action": "Regla de mínimo en channel manager para categorías altas; revisión semanal de BAR.",
        },
    ],
    "anomalies": [
        {
            "title": "Pico de cancelaciones en un canal puntual",
            "severity": "medium",
            "what_happened": "Una semana muestra cancelaciones desproporcionadas vs el promedio móvil.",
            "why_it_matters": "Puede indicar política de cancelación, overbooking de terceros o problema de paridad.",
            "recommended_action": "Auditar políticas publicadas por canal y pickup neto por fecha de estancia.",
        }
    ],
    "kpi_table": [
        {
            "metric": "Room nights (periodo)",
            "value": "1.240",
            "executive_read": "Volumen acorde a categoría; concentrado en Q de demanda alta.",
            "attention_level": "low",
        },
        {
            "metric": "Participación OTA estimada",
            "value": "62%",
            "executive_read": "Dependencia relevante; conviene plan de migración gradual a directo.",
            "attention_level": "high",
        },
    ],
    "strategic_recommendations": [
        {
            "title": "Reglas de estancia y cerramiento en alta",
            "priority": "high",
            "action": "Definir mínimo de noches y stop-sell coordinado en channel manager para noches críticas.",
            "expected_impact": "Mejor control de tarifa neta y mix de canal en fechas fuertes.",
        },
        {
            "title": "Campaña directa sólo para entre semana",
            "priority": "medium",
            "action": "Oferta exclusiva en motor de reservas para domingo–jueves con ventana de 14 días.",
            "expected_impact": "Sube producción directa sin canibalizar fines de semana.",
        },
    ],
    "plan_30_60_90": {
        "days_30": [
            "Auditoría de paridad y políticas por canal.",
            "Ajuste de BAR y restricciones en 4 fines de semana clave.",
        ],
        "days_60": [
            "Reporte semanal de mix y ADR por canal.",
            "Prueba A/B de landing en motor para estancias entre semana.",
        ],
        "days_90": [
            "Objetivo de participación directa medible.",
            "Integración de reporting de costo de distribución neto.",
        ],
    },
    "additional_reports_needed": [
        {
            "report_name": "Pickup por día de llegada",
            "why_it_is_needed": "Permite ver si el problema es precio, visibilidad o restricción operativa.",
        },
        {
            "report_name": "Cancelaciones por canal y lead time",
            "why_it_is_needed": "Aislar si el canal puntual arrastra ruido en inventario.",
        },
    ],
    "next_steps": [
        "Confirmar con revenue/comercial las 2 acciones de prioridad alta.",
        "Agendar segunda corrida con export de canales desagregados.",
    ],
}

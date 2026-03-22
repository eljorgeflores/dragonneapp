# DragonApp — Fase 4.5 (copy y percepción)

## A. Diagnóstico breve del copy previo

- **Loading:** mencionaba “IA” y sonaba a proceso técnico más que a lectura comercial.
- **Hero y meta:** útiles pero con jerga mezclada (“reporte”, “ventana”) sin marco de confianza (“según export”).
- **Cobertura:** “Campos detectados” bien; “modelo” en datos faltantes restaba credibilidad operativa.
- **Paneles:** títulos genéricos (“Riesgos detectados”, “Recomendaciones accionables”) y “Urgencia/Impacto” algo alarmista.
- **Historial:** “Análisis” y “Rep.” poco alineados con “fuentes leídas”.
- **Prompt OpenAI:** buen nivel técnico; faltaba explicitar sobriedad, anti-alarmismo y redacción tipo memorando (no marketing ni “voz IA”).

## B. Tono recomendado (y dos variantes)

| Variante | Enfoque | Cuándo usar |
|----------|---------|-------------|
| **Gerencia general** | Más narrativo, menos jerga de canal; “distribución” antes que “mix OTA”. | Comunicación a dueños o GMs sin equipo revenue dedicado. |
| **Revenue / comercial** | Mantiene ADR, canales, ventanas de fechas; decisiones sobre tarifa e inventario. | Hoteles con RM o director comercial fuerte. |

**Default implementado:** híbrido **revenue-first sobrio** (closer to RM): términos estándar de hotelería con frases cortas y disclaimers (“según el export”, “validar con tu equipo”). Los títulos del tablero siguen entendibles para GM sin perder precisión comercial.

## C. Textos cambiados (referencia)

- Panel, carga, hero, loading, tablero (JS + `app.html`), KPIs, gráficos, paneles izquierda/centro/derecha, errores y share (`app.js`).
- Títulos guardados: `Lectura comercial · N fuente(s) · fecha` (`analysis_service.py`, `routes/api.py`).
- Prompt del modelo: rol, estilo, datos faltantes (`analysis_core.py`).
- PDF y vista pública alineados (`pdf_service.py`, `share_public.html`).

## D. Implementación

Ver diff en los archivos listados abajo; sin cambios de arquitectura ni de esquema JSON.

## E. Mejoras visibles para el usuario

- Menos “producto IA”, más **lectura comercial** y **según el export**.
- **Datos faltantes** enmarcados como huecos del archivo, no como limitación del “modelo”.
- **Próximos pasos** con tono de comité de dirección (validar con equipo antes de mover tarifas).
- **Loading** sin mencionar IA; vocabulario de cruce de datos.
- **Historial** con columnas “Referencia / Fuentes” y copy de extracto explícito.

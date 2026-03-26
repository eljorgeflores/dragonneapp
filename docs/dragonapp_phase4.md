# DragonApp — Fase 4 (producto / UX flujo core)

Objetivo: mejorar la experiencia **upload → validación → análisis → resultado → historial** sin cambiar arquitectura ni stack.

## Archivos tocados

| Área | Archivo |
|------|---------|
| Plantilla panel | `templates/app.html` |
| Lógica cliente | `static/app.js` |
| Estilos | `static/styles.css` |

## Comportamiento

1. **Upload / validación:** si no hay archivos, mensaje bajo el botón (`#analyzeFormStatus`) + hint en la dropzone; se limpia al añadir archivos. El `<input type="file">` **no** usa `required` HTML5 para que el `submit` llegue al JS y el copy sea consistente en español (el servidor sigue rechazando cero archivos).
2. **Análisis en curso:** fases rotativas en `#resultsLoadingPhase` + texto de tiempo estimado; `stopLoadingPhaseCycle` al terminar.
3. **Resultado ejecutivo:** bloque `#resultHero` (título, meta de archivos/reportes/días, lectura corta del resumen, lista corta de `datos_faltantes`).
4. **Cobertura por archivo/hoja:** `#resultSourcePanel` a partir de `summary.report_summaries` (nombre/hoja, campos detectados, días, rango de fechas).
5. **Detalle:** `resultMeta` y KPIs; paneles con intros y acento en recomendaciones (`panel-block-actions`).
6. **Historial:** columna **Análisis** (título + preview del resumen), botones `type="button"`, estado `.is-active` al seleccionar; respuesta JSON tolerante a cuerpo no-JSON en POST `/analyze`.

## Validación rápida

```bash
python3 -m pytest test_analyze_report.py test_flows.py -q
```

Prueba manual en navegador: subir CSV/Excel, esperar resultado, revisar hero + panel de cobertura, abrir un ítem del historial.

## Deuda (opcional)

- Afinar copy por segmento (GM vs revenue).
- Comparación entre análisis en historial (fuera de alcance de esta fase).

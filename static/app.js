const appShell = document.getElementById('appShell');

/** Prefijo de montaje (URL_PREFIX) cuando la app no está en la raíz del dominio. */
function appUrlPath(path) {
  const attr = document.body && document.body.getAttribute('data-url-prefix');
  const raw = attr != null ? String(attr).trim() : '';
  const base = raw.replace(/\/$/, '');
  const p = (path || '').startsWith('/') ? path : `/${path}`;
  return base ? `${base}${p}` : p;
}

function followAppRedirect(href) {
  if (!href || typeof href !== 'string') return;
  const h = href.trim();
  if (/^https?:\/\//i.test(h)) {
    window.location.href = h;
    return;
  }
  window.location.href = appUrlPath(h.startsWith('/') ? h : `/${h}`);
}

const fileInput = document.getElementById('files');
const fileList = document.getElementById('fileList');
const fileSelectionSummary = document.getElementById('fileSelectionSummary');
const fileLimitHint = document.getElementById('fileLimitHint');
const dropzone = document.getElementById('dropzone');
const form = document.getElementById('analyzeForm');
const businessContextInput = document.getElementById('business_context');
const resultsCard = document.getElementById('resultsCard');
const resultsLayout = document.getElementById('resultsLayout');
const resultsLoading = document.getElementById('resultsLoading');
const tableroContent = document.getElementById('tableroContent');
const tableroKpis = document.getElementById('tableroKpis');
const tableroLeft = document.getElementById('tableroLeft');
const tableroCenter = document.getElementById('tableroCenter');
const tableroRight = document.getElementById('tableroRight');
const paywallEl = document.getElementById('paywall');
const planBadge = document.getElementById('planBadge');
const resultMeta = document.getElementById('resultMeta');
const uploadNoticesPanel = document.getElementById('uploadNoticesPanel');
const analyzeFormStatus = document.getElementById('analyzeFormStatus');
const resultHero = document.getElementById('resultHero');
const downloadPdfBtn = document.getElementById('downloadPdfBtn');
const copyShareBtn = document.getElementById('copyShareBtn');
const emailShareBtn = document.getElementById('emailShareBtn');
const serverEmailShareBtn = document.getElementById('serverEmailShareBtn');
const shareFeedback = document.getElementById('shareFeedback');
let currentAnalysisId = null;
let currentShareUrl = null;
let loadingPhaseTimer = null;

const LOADING_PHASES = [
  'Validando archivos y leyendo columnas…',
  'Cruzando fechas, canales e ingresos del export…',
  'Redactando la lectura comercial (puede tardar un minuto más)…',
];

const DELETE_ANALYSIS_CONFIRM =
  '¿Eliminar esta lectura de tu historial?\n\n' +
  'Se borrará de forma permanente: no podrás recuperarla ni volver a abrirla desde Pullso. Los enlaces compartidos dejarán de funcionar y no podrás usarla como referencia o comparativa en el producto para lecturas futuras.\n\n' +
  'El cupo de lecturas de tu mes (UTC) no se restablece al borrar.';

function getMaxFiles() {
  const raw = (form && form.dataset.maxFiles) || (appShell && appShell.dataset.maxFiles) || '5';
  const v = parseInt(raw, 10);
  return Number.isFinite(v) && v > 0 ? v : 5;
}

function showFileHint(msg) {
  if (!fileLimitHint) return;
  if (!msg) {
    fileLimitHint.classList.add('hidden');
    fileLimitHint.textContent = '';
    return;
  }
  fileLimitHint.textContent = msg;
  fileLimitHint.classList.remove('hidden');
}

function setInputFiles(fileArray) {
  if (!fileInput) return;
  const maxF = getMaxFiles();
  const slice = fileArray.slice(0, maxF);
  const dt = new DataTransfer();
  slice.forEach(f => dt.items.add(f));
  fileInput.files = dt.files;
  renderFiles();
}

function syncFileSelectionChrome() {
  if (!fileInput) return;
  const n = fileInput.files.length;
  if (dropzone) dropzone.classList.toggle('has-files', n > 0);
  if (fileSelectionSummary) {
    fileSelectionSummary.textContent =
      n === 0 ? '' : n === 1 ? '1 archivo seleccionado.' : `${n} archivos seleccionados.`;
  }
}

function renderFiles() {
  if (!fileInput || !fileList) return;
  if (analyzeFormStatus && fileInput.files.length) {
    analyzeFormStatus.textContent = '';
    analyzeFormStatus.classList.add('hidden');
  }
  fileList.innerHTML = '';
  [...fileInput.files].forEach((file, idx) => {
    const chip = document.createElement('div');
    chip.className = 'file-chip file-chip-row';
    const label = document.createElement('span');
    label.className = 'file-chip-label';
    label.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
    chip.appendChild(label);
    const rm = document.createElement('button');
    rm.type = 'button';
    rm.className = 'file-chip-remove';
    rm.setAttribute('aria-label', `Quitar ${file.name}`);
    rm.textContent = '×';
    rm.addEventListener('click', () => {
      const next = [...fileInput.files].filter((_, i) => i !== idx);
      setInputFiles(next);
      showFileHint('');
    });
    chip.appendChild(rm);
    fileList.appendChild(chip);
  });
  syncFileSelectionChrome();
  requestAnimationFrame(() => syncFileSelectionChrome());
}

if (dropzone) {
  const onDragOver = e => {
    e.preventDefault();
    if (e.dataTransfer) e.dataTransfer.dropEffect = 'copy';
    dropzone.classList.add('dragover');
  };
  dropzone.addEventListener('dragenter', onDragOver, true);
  dropzone.addEventListener('dragover', onDragOver, true);
  dropzone.addEventListener('dragleave', e => {
    const next = e.relatedTarget;
    if (next && dropzone.contains(next)) return;
    dropzone.classList.remove('dragover');
  });
  dropzone.addEventListener(
    'drop',
    e => {
      e.preventDefault();
      e.stopPropagation();
      dropzone.classList.remove('dragover');
      const dtFiles = e.dataTransfer && e.dataTransfer.files;
      if (fileInput && dtFiles && dtFiles.length > 0) {
        const maxF = getMaxFiles();
        const incoming = [...dtFiles];
        const existing = [...fileInput.files];
        const merged = [...existing, ...incoming];
        if (merged.length > maxF) {
          showFileHint(
            `Tu plan admite hasta ${maxF} archivo(s) por corrida. Quita los que no vayas a usar con ✕.`,
          );
        } else {
          showFileHint('');
        }
        setInputFiles(merged);
      }
    },
    true,
  );
}
if (fileInput) {
  fileInput.addEventListener('change', () => {
    const maxF = getMaxFiles();
    const arr = [...fileInput.files];
    if (arr.length > maxF) {
      showFileHint(`Tu plan admite hasta ${maxF} archivo(s) por corrida. Se tomaron solo los primeros ${maxF}.`);
      setInputFiles(arr);
    } else {
      if (arr.length <= maxF) showFileHint('');
      renderFiles();
    }
  });
}

function htmlEscape(value) {
  return String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

/**
 * Error 402 en el tablero: texto del servidor + consejos según el tipo de límite.
 * No usar "archivo(s)" genérico en la condición: el mensaje de fechas del backend
 * habla de "archivos" al tranquilizar y eso disparaba por error el tip de plan Gratis.
 */
function buildPlanLimitErrorHtml(rawError) {
  const err = rawError || 'No se completó la lectura por un límite de tu plan.';
  const errLower = err.toLowerCase();
  const tips = [];

  if (errLower.includes('en plan gratis va un solo archivo')) {
    tips.push(
      'En <strong>plan Gratis</strong> solo analizamos <strong>un archivo</strong> por envío. Quita el resto con ✕ y vuelve a generar la lectura.'
    );
  } else if (errLower.includes('plan pro admite hasta') && errLower.includes('archivos por corrida')) {
    tips.push(
      'Ajusta la selección hasta el tope de archivos de <strong>Pro</strong>, o sube el resto en otra corrida.'
    );
  } else if (errLower.includes('pro+ admite hasta') && errLower.includes('archivos por corrida')) {
    tips.push(
      'En <strong>Pro+</strong> hay un máximo de archivos por envío: divide la carga en dos envíos si necesitas todas las fuentes.'
    );
  } else if (errLower.includes('prueba extendida admite hasta') && errLower.includes('archivos por corrida')) {
    tips.push(
      'Tu <strong>prueba extendida</strong> usa el mismo tope de archivos por envío que Pro+: divide la carga si necesitas más fuentes en una sola lectura.'
    );
  }

  if (
    errLower.includes('rango de fechas muy amplio') ||
    errLower.includes('columna de fecha equivocada') ||
    errLower.includes('formatos mezclados')
  ) {
    tips.push(
      'Si el mensaje te sorprende, revisa en Excel o en el PMS que la columna de fechas sea la correcta y sin celdas con años o formatos raros.'
    );
  }

  let html = `<div class="upload-limit-panel" role="alert"><p class="upload-limit-panel__text">${htmlEscape(err)}</p>`;
  if (tips.length) {
    html += `<ul class="upload-limit-panel__tips">${tips.map((t) => `<li>${t}</li>`).join('')}</ul>`;
  }
  html += '</div>';
  return html;
}

function formatDisplayDate(raw) {
  if (!raw) return '';
  const s = String(raw).replace('T', ' ').trim();
  return s.length >= 16 ? s.slice(0, 16) : s;
}

function formatDateShort(iso) {
  if (!iso) return '—';
  try {
    const d = new Date(iso);
    if (Number.isNaN(d.getTime())) return String(iso).slice(0, 10);
    return d.toLocaleDateString('es-MX', { day: '2-digit', month: 'short', year: 'numeric' });
  } catch {
    return '—';
  }
}

function formatSheetLabel(sheetName) {
  if (!sheetName) return 'Reporte';
  const s = String(sheetName);
  const idx = s.indexOf('::');
  if (idx === -1) return s;
  return `${s.slice(0, idx)} · hoja «${s.slice(idx + 2)}»`;
}

function executiveLead(text) {
  const t = (text || '').trim().replace(/\s+/g, ' ');
  if (!t) {
    return 'Abajo está el detalle: métricas del export, hallazgos y pasos concretos. Si falta texto arriba, el resumen ejecutivo en el tablero lo desarrolla.';
  }
  if (t.length <= 300) return t;
  const slice = t.slice(0, 300);
  const dot = slice.lastIndexOf('.');
  return dot > 100 ? slice.slice(0, dot + 1) : `${slice}…`;
}

function datosFaltantesAsStrings(analysis) {
  const gaps = analysis?.datos_faltantes;
  if (!gaps || !gaps.length) return [];
  return gaps
    .map(g => (typeof g === 'string' ? g : (g && (g.text || g.detalle || g.titulo)) || ''))
    .map(s => String(s).trim())
    .filter(Boolean);
}

function renderResultSourcePanel(summary) {
  const el = document.getElementById('resultSourcePanel');
  if (!el || !summary) return;
  const rows = summary.report_summaries || [];
  if (!rows.length) {
    el.classList.add('hidden');
    el.innerHTML = '';
    return;
  }
  el.classList.remove('hidden');
  const parts = rows.map(r => {
    const label = formatSheetLabel(r.sheet_name);
    const dc = r.days_covered ?? 0;
    const dr = r.date_range || {};
    const start = formatDateShort(dr.start);
    const end = formatDateShort(dr.end);
    const fd = r.fields_detected || [];
    const fields = fd.slice(0, 12).join(', ');
    const more = fd.length > 12 ? '…' : '';
    const fieldsLine = fields
      ? `Columnas reconocidas en este archivo: ${fields}${more}`
      : 'En este archivo no identificamos con claridad fechas, canales o ingresos: la lectura será más acotada.';
    return `<div class="result-source-row">
      <div>
        <div class="result-source-name">${htmlEscape(label)}</div>
        <div class="result-source-fields">${htmlEscape(fieldsLine)}</div>
      </div>
      <div class="result-source-meta">
        <strong>${htmlEscape(dc)}</strong> días con datos en esta fuente<br/>
        Ventana detectada: ${htmlEscape(start)} → ${htmlEscape(end)}
      </div>
    </div>`;
  });
  el.innerHTML = `<h3>Fuentes cargadas y cobertura de fechas</h3><div class="result-source-rows">${parts.join('')}</div>`;
}

function renderResultHero(title, createdAt, analysis, summary) {
  if (!resultHero) return;
  resultHero.classList.remove('hidden');
  const titleEl = document.getElementById('resultHeroTitle');
  const metaEl = document.getElementById('resultHeroMeta');
  const leadEl = document.getElementById('resultHeroLead');
  const gapBox = document.getElementById('resultHeroGapCallout');
  const gapList = document.getElementById('resultHeroGapList');
  if (titleEl) titleEl.textContent = title || 'Lectura guardada';
  const files = summary?.total_files ?? '—';
  const reps = summary?.reports_detected ?? '—';
  const od = summary?.overall_days_covered ?? 0;
  const md = summary?.max_days_covered ?? 0;
  if (metaEl) {
    const when = formatDisplayDate(createdAt);
    metaEl.textContent = `${when ? `${when} · ` : ''}${files} archivo(s) en la carga · ${reps} fuente(s) leída(s) · ${od} días en la ventana total · hasta ${md} días en la fuente más larga`;
  }
  if (leadEl) leadEl.textContent = executiveLead(analysis?.resumen_ejecutivo);
  const strGaps = datosFaltantesAsStrings(analysis);
  if (gapBox && gapList) {
    if (strGaps.length) {
      gapBox.classList.remove('hidden');
      const cap = strGaps.slice(0, 6);
      gapList.innerHTML = cap.map(s => `<li>${htmlEscape(s)}</li>`).join('');
      if (strGaps.length > 6) {
        gapList.insertAdjacentHTML(
          'beforeend',
          `<li class="muted">${htmlEscape(`+ ${strGaps.length - 6} en el panel «Próximos pasos» (columna derecha).`)}</li>`,
        );
      }
    } else {
      gapBox.classList.add('hidden');
      gapList.innerHTML = '';
    }
  }
}

function hideResultHeroAndSource() {
  if (resultHero) resultHero.classList.add('hidden');
  const rsp = document.getElementById('resultSourcePanel');
  if (rsp) {
    rsp.classList.add('hidden');
    rsp.innerHTML = '';
  }
}

function startLoadingPhaseCycle() {
  if (loadingPhaseTimer) clearInterval(loadingPhaseTimer);
  const phaseEl = document.getElementById('resultsLoadingPhase');
  if (!phaseEl) return;
  let i = 0;
  phaseEl.textContent = LOADING_PHASES[0];
  loadingPhaseTimer = setInterval(() => {
    i = (i + 1) % LOADING_PHASES.length;
    phaseEl.textContent = LOADING_PHASES[i];
  }, 4500);
}

function stopLoadingPhaseCycle() {
  if (loadingPhaseTimer) {
    clearInterval(loadingPhaseTimer);
    loadingPhaseTimer = null;
  }
}

function markHistorySelection(analysisId) {
  document.querySelectorAll('.history-item').forEach(b => {
    b.classList.toggle('is-active', String(b.dataset.analysisId) === String(analysisId));
  });
}

function renderSummary(summary, plan) {
  if (resultMeta) {
    const od = summary.overall_days_covered || 0;
    const md = summary.max_days_covered || 0;
    resultMeta.textContent = `Cruce de ${summary.reports_detected} fuente(s) en ${summary.total_files} archivo(s). Ventana total aproximada: ${od} día(s); la fuente individual más larga cubre hasta ${md} día(s).`;
  }
  if (uploadNoticesPanel) {
    const notes = Array.isArray(summary.upload_notices) ? summary.upload_notices : [];
    if (notes.length) {
      uploadNoticesPanel.classList.remove('hidden');
      uploadNoticesPanel.innerHTML = notes
        .map(n => {
          if (!n) return '';
          if (Array.isArray(n.messages) && n.messages.length) {
            const head = n.sheet ? `<strong>${htmlEscape(String(n.sheet))}</strong><br>` : '';
            const body = n.messages.map(m => htmlEscape(String(m))).join('<br>');
            return `<div class="alert info small">${head}${body}</div>`;
          }
          const msg = n.message || '';
          return msg ? `<div class="alert info small">${htmlEscape(msg)}</div>` : '';
        })
        .join('');
    } else {
      uploadNoticesPanel.classList.add('hidden');
      uploadNoticesPanel.innerHTML = '';
    }
  }
  if (planBadge) {
    planBadge.textContent =
      plan === 'pro_plus'
        ? 'Pro+'
        : plan === 'pro'
          ? 'PRO'
          : plan === 'free_trial'
            ? 'PRUEBA'
            : 'GRATIS';
  }
  const cards = [
    { label: 'Archivos (carga)', value: summary.total_files },
    { label: 'Fuentes leídas', value: summary.reports_detected },
    { label: 'Días (ventana total)', value: summary.overall_days_covered || 0 },
    { label: 'Máx. días (una fuente)', value: summary.max_days_covered || 0 },
  ];
  if (tableroKpis) {
    tableroKpis.innerHTML = cards.map(item => `<div class="kpi"><div class="label">${item.label}</div><div class="value">${htmlEscape(item.value)}</div></div>`).join('');
  }
  renderResultSourcePanel(summary);
}

function pickChartColor(idx) {
  const palette = ['#f6a905', '#f07e07', '#808081', '#343434', '#e6e6e6'];
  return palette[idx % palette.length];
}

function renderCharts(summary) {
  if (!tableroLeft) return;
  const reportSummaries = summary.report_summaries || [];
  const main = reportSummaries[0] || {};
  const metrics = main.metrics || {};
  const channels = main.metrics?.top_canales_por_ingreso || main.metrics?.top_canales_por_reservas || [];

  let totalIngreso = 0;
  channels.forEach(c => {
    if (c.ingreso != null) totalIngreso += Number(c.ingreso);
    else if (c.reservas != null) totalIngreso += Number(c.reservas);
  });
  const slices = channels.slice(0, 5);
  const percentages = slices.map(c => {
    const base = c.ingreso != null ? Number(c.ingreso) : Number(c.reservas || 0);
    return totalIngreso > 0 ? Math.round((base / totalIngreso) * 100) : 0;
  });
  const adr = metrics.adr_promedio ?? metrics.adr_estimado ?? null;
  const roomNights = metrics.room_nights ?? null;
  const cancelPct = metrics.cancelacion_pct ?? null;

  const chartsHTML = `
    <div class="chart-card">
      <h3>Participación por canal (según el export)</h3>
      <p class="muted small panel-block-intro" style="margin:0 0 10px;">Proporción aproximada de ingresos o volumen entre canales detectados; valida contra tu PMS si ajustas precio o inventario.</p>
      <div class="mix-bars">
        ${slices.length ? slices.map((c, idx) => `
          <div class="mix-bar-row">
            <span class="mix-bar-label">${htmlEscape(c.canal || 'Canal')}</span>
            <div class="mix-bar-track">
              <div class="mix-bar-fill" style="width:${percentages[idx] || 0}%;background:${pickChartColor(idx)}"></div>
            </div>
            <span class="mix-bar-pct">${percentages[idx] != null ? percentages[idx] + '%' : '—'}</span>
          </div>
        `).join('') : '<p class="muted panel-empty-copy">Este export no trae desglose por canal en las columnas que pudimos mapear.</p>'}
      </div>
    </div>
    <div class="chart-card">
      <h3>Indicadores del export</h3>
      <p class="muted small panel-block-intro" style="margin:0 0 10px;">Cifras sacadas del archivo; si faltan, suele faltar la columna o el periodo no lo permite.</p>
      <div class="columns-wrapper">
        <div class="column" style="height: 80px;"><div class="column-inner"></div></div>
        <div class="column" style="height: 110px;"><div class="column-inner"></div></div>
        <div class="column" style="height: 60px;"><div class="column-inner"></div></div>
      </div>
      <div class="column-labels">
        <span>ADR</span>
        <span>Noches</span>
        <span>Cancelación</span>
      </div>
      <div class="mini-top" style="margin-top:8px;">
        ${adr != null ? `ADR: ${htmlEscape(adr)}` : 'ADR: no aparece claro en el export'} ·
        ${roomNights != null ? `Noches vendidas: ${htmlEscape(roomNights)}` : 'Noches vendidas: sin dato'} ·
        ${cancelPct != null ? `Cancelación: ${htmlEscape(cancelPct)}%` : 'Cancelación: sin dato'}
      </div>
    </div>
  `;
  tableroLeft.innerHTML = chartsHTML;
}

function renderListItems(items, mode = 'plain') {
  if (!items || !items.length) return '<p class="muted panel-empty-copy">Con este export no hay ítems en este apartado. Si esperabas contenido, revisa columnas o suma otro archivo en el siguiente análisis.</p>';
  if (mode === 'metrics') {
    return items.map(item => `<div class="panel-item"><strong>${htmlEscape(item.nombre)} · ${htmlEscape(item.valor)}</strong><div class="muted">${htmlEscape(item.lectura)}</div></div>`).join('');
  }
  if (mode === 'priority') {
    return items.map(item => `<div class="panel-item"><strong>${htmlEscape(item.titulo)}</strong><div>${htmlEscape(item.detalle)}</div><div class="muted">Gravedad para el negocio: ${htmlEscape(item.impacto)} · Prioridad sugerida: ${htmlEscape(item.prioridad)}</div></div>`).join('');
  }
  if (mode === 'actions') {
    return items.map(item => `<div class="panel-item"><strong>${htmlEscape(item.accion)}</strong><div>${htmlEscape(item.por_que)}</div><div class="muted">Plazo sugerido: ${htmlEscape(item.urgencia)}</div></div>`).join('');
  }
  return items.map(item => `<div class="panel-item">${htmlEscape(item)}</div>`).join('');
}

function renderAnalysis(analysis) {
  if (!tableroLeft || !tableroCenter || !tableroRight) return;

  // Columna izquierda: añadir Oportunidades y Riesgos (charts ya están)
  const leftBlocks = `
    <div class="panel-block">
      <h3>Oportunidades (directo y distribución)</h3>
      <p class="muted small panel-block-intro">Dónde puede haber margen o volumen según lo que muestra el export.</p>
      ${renderListItems(analysis.oportunidades_directo_vs_ota)}
    </div>
    <div class="panel-block">
      <h3>Riesgos y puntos de atención</h3>
      <p class="muted small panel-block-intro">Concentraciones o desvíos que conviene vigilar; no implican fallo operativo por sí solos.</p>
      ${renderListItems(analysis.riesgos_detectados)}
    </div>
  `;
  tableroLeft.insertAdjacentHTML('beforeend', leftBlocks);

  // Columna centro: Resumen ejecutivo, Métricas clave, Hallazgos prioritarios
  tableroCenter.innerHTML = `
    <div class="panel-block panel-block-resumen">
      <h3>Resumen ejecutivo</h3>
      <p class="muted small panel-block-intro">Versión extendida de la lectura; arriba tienes el extracto para dirección.</p>
      <div class="resumen-ejecutivo-body">${htmlEscape(analysis.resumen_ejecutivo || '')}</div>
    </div>
    <div class="panel-block">
      <h3>Métricas y lectura</h3>
      <p class="muted small panel-block-intro">Números del export con interpretación breve.</p>
      ${renderListItems(analysis.metricas_clave, 'metrics')}
    </div>
    <div class="panel-block">
      <h3>Hallazgos prioritarios</h3>
      <p class="muted small panel-block-intro">Lo que más condiciona ingresos o riesgo en el periodo analizado.</p>
      ${renderListItems(analysis.hallazgos_prioritarios, 'priority')}
    </div>
  `;

  // Columna derecha: Recomendaciones accionables, Datos faltantes
  tableroRight.innerHTML = `
    <div class="panel-block panel-block-actions">
      <h3>Próximos pasos sugeridos</h3>
      <p class="muted small panel-block-intro">Acciones concretas; en operación real conviene validar con tu equipo comercial o revenue antes de mover tarifas o inventario.</p>
      ${renderListItems(analysis.recomendaciones_accionables, 'actions')}
    </div>
    <div class="panel-block">
      <h3>Información que faltó en el export</h3>
      <p class="muted small panel-block-intro">Huecos en los datos cargados (no fallos del hotel). Subir otro tipo de reporte suele afinar la siguiente lectura.</p>
      ${renderListItems(analysis.datos_faltantes)}
    </div>
  `;

  const gate = analysis.senal_de_upgrade;
  if (gate && gate.deberia_hacer_upgrade && paywallEl) {
    paywallEl.classList.remove('hidden');
    paywallEl.innerHTML = `<strong>Ampliar plan.</strong> ${htmlEscape(gate.motivo || '')}`;
  } else if (paywallEl) {
    paywallEl.classList.add('hidden');
    paywallEl.innerHTML = '';
  }
}

function hideAnalysisLoading() {
  stopLoadingPhaseCycle();
  if (resultsLayout) resultsLayout.classList.remove('is-loading');
  if (resultsLoading) resultsLoading.classList.add('hidden');
}

function appendToHistory(item) {
  const card = document.querySelector('.history-card');
  if (!card) return;
  const grid = card.querySelector('#historyGrid');
  const empty = card.querySelector('#historyEmpty');
  const row = document.createElement('div');
  row.className = 'history-row';
  const btn = document.createElement('button');
  btn.type = 'button';
  btn.className = 'history-item';
  btn.dataset.analysisId = String(item.id);
  const re = (item.resumen_ejecutivo || '').trim();
  const sub = re
    ? `<span class="history-title-sub">${htmlEscape(re.length > 120 ? `${re.slice(0, 120)}…` : re)}</span>`
    : '';
  btn.innerHTML = `
    <span class="history-col history-col-date">${htmlEscape(item.created_at)}</span>
    <span class="history-col history-col-title">
      <span class="history-title-main">${htmlEscape(item.title || `Lectura #${item.id}`)}</span>
      ${sub}
    </span>
    <span class="history-col history-col-files">${item.file_count}</span>
    <span class="history-col history-col-days">${item.days_covered ?? 0}</span>
    <span class="history-col history-col-reports">${item.reports_detected}</span>
  `;
  const del = document.createElement('button');
  del.type = 'button';
  del.className = 'history-delete-btn';
  del.dataset.analysisId = String(item.id);
  del.setAttribute('aria-label', 'Eliminar esta lectura del historial');
  del.title = 'Eliminar del historial';
  del.innerHTML =
    '<svg class="history-delete-icon" width="18" height="18" viewBox="0 0 24 24" fill="none" aria-hidden="true"><path d="M3 6h18M8 6V4a2 2 0 012-2h4a2 2 0 012 2v2m3 0v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6h14zM10 11v6M14 11v6" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/></svg>';
  row.appendChild(btn);
  row.appendChild(del);
  if (grid) {
    grid.insertBefore(row, grid.firstChild);
  } else if (empty) {
    const newGrid = document.createElement('div');
    newGrid.className = 'history-grid';
    newGrid.id = 'historyGrid';
    newGrid.appendChild(row);
    empty.parentNode.replaceChild(newGrid, empty);
  }
}

async function handleDeleteHistoryAnalysis(analysisId, triggerBtn) {
  const id = analysisId != null ? String(analysisId).trim() : '';
  if (!id || !window.confirm(DELETE_ANALYSIS_CONFIRM)) return;
  if (triggerBtn) triggerBtn.disabled = true;
  try {
    const res = await fetch(appUrlPath(`/analysis/${id}`), {
      method: 'DELETE',
      headers: { Accept: 'application/json' },
    });
    let data = {};
    try {
      data = await res.json();
    } catch {
      data = {};
    }
    if (!res.ok || !data.ok) {
      const msg =
        data.error ||
        (res.status === 401
          ? 'Sesión vencida o no válida. Inicia sesión de nuevo.'
          : 'No se pudo eliminar. Inténtalo de nuevo.');
      window.alert(msg);
      if (triggerBtn) triggerBtn.disabled = false;
      return;
    }
    const row =
      triggerBtn?.closest('.history-row') ||
      document.querySelector(`.history-item[data-analysis-id="${CSS.escape(id)}"]`)?.closest('.history-row');
    row?.remove();
    const grid = document.getElementById('historyGrid');
    if (grid && !grid.querySelector('.history-row')) {
      const empty = document.createElement('div');
      empty.className = 'empty-state';
      empty.id = 'historyEmpty';
      empty.textContent = 'Aún no hay lecturas guardadas. Carga un export y genera la primera.';
      grid.replaceWith(empty);
    }
    if (String(currentAnalysisId) === String(id)) {
      currentAnalysisId = null;
      currentShareUrl = null;
      if (downloadPdfBtn) downloadPdfBtn.disabled = true;
      setShareControlsEnabled(false);
      hideResultHeroAndSource();
      if (resultsCard) resultsCard.classList.add('hidden');
      if (tableroKpis) tableroKpis.innerHTML = '';
      if (tableroLeft) tableroLeft.innerHTML = '';
      if (tableroCenter) tableroCenter.innerHTML = '';
      if (tableroRight) tableroRight.innerHTML = '';
      if (paywallEl) {
        paywallEl.classList.add('hidden');
        paywallEl.innerHTML = '';
      }
      if (uploadNoticesPanel) {
        uploadNoticesPanel.classList.add('hidden');
        uploadNoticesPanel.innerHTML = '';
      }
      if (resultMeta) resultMeta.textContent = '';
    }
  } catch (err) {
    window.alert(err.message || 'Error de red.');
    if (triggerBtn) triggerBtn.disabled = false;
  }
}

async function ensureShareUrl(analysisId) {
  if (currentShareUrl) return currentShareUrl;
  const res = await fetch(appUrlPath(`/analysis/${analysisId}/share`), { method: 'POST', headers: { Accept: 'application/json' } });
  const data = await res.json().catch(() => ({}));
  if (res.ok && data.ok && data.share_url) {
    currentShareUrl = data.share_url;
    return currentShareUrl;
  }
  return null;
}

function setShareControlsEnabled(on) {
  if (copyShareBtn) copyShareBtn.disabled = !on;
  if (emailShareBtn) emailShareBtn.disabled = !on;
  if (serverEmailShareBtn) serverEmailShareBtn.disabled = !on;
  if (!on && shareFeedback) {
    shareFeedback.classList.add('hidden');
    shareFeedback.textContent = '';
  }
}

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    if (!submit) return;
    const files = fileInput && fileInput.files ? [...fileInput.files] : [];
    if (!files.length) {
      if (analyzeFormStatus) {
        analyzeFormStatus.textContent = 'Elige al menos un CSV o Excel con datos de operación antes de generar la lectura.';
        analyzeFormStatus.classList.remove('hidden');
      }
      showFileHint('Añade archivos desde «Elegir archivos» o arrastrándolos a la zona de carga.');
      return;
    }
    const ctxMinRaw = businessContextInput && businessContextInput.dataset && businessContextInput.dataset.minContext;
    const ctxMin = ctxMinRaw != null && ctxMinRaw !== '' ? Number.parseInt(String(ctxMinRaw), 10) : 15;
    const ctxMinSafe = Number.isFinite(ctxMin) && ctxMin > 0 ? ctxMin : 15;
    const ctxVal = businessContextInput && businessContextInput.value ? businessContextInput.value.trim() : '';
    if (ctxVal.length < ctxMinSafe) {
      if (analyzeFormStatus) {
        analyzeFormStatus.textContent = `El contexto es obligatorio: indica qué quieres entender o priorizar (mínimo ${ctxMinSafe} caracteres).`;
        analyzeFormStatus.classList.remove('hidden');
      }
      businessContextInput?.focus();
      return;
    }
    if (analyzeFormStatus) {
      analyzeFormStatus.textContent = '';
      analyzeFormStatus.classList.add('hidden');
    }
    submit.disabled = true;
    submit.textContent = 'Generando lectura…';
    form.setAttribute('aria-busy', 'true');
    currentShareUrl = null;
    setShareControlsEnabled(false);
    hideResultHeroAndSource();
    if (resultsCard) resultsCard.classList.remove('hidden');
    if (resultsLayout) resultsLayout.classList.add('is-loading');
    if (resultsLoading) resultsLoading.classList.remove('hidden');
    startLoadingPhaseCycle();
    if (tableroKpis) tableroKpis.innerHTML = '';
    if (tableroLeft) tableroLeft.innerHTML = '';
    if (tableroCenter) tableroCenter.innerHTML = '';
    if (tableroRight) tableroRight.innerHTML = '';
    if (paywallEl) paywallEl.classList.add('hidden');
    if (uploadNoticesPanel) {
      uploadNoticesPanel.classList.add('hidden');
      uploadNoticesPanel.innerHTML = '';
    }
    try {
      const res = await fetch(appUrlPath('/analyze'), { method: 'POST', body: new FormData(form) });
      let data = {};
      try {
        data = await res.json();
      } catch {
        data = { ok: false, error: 'El servidor devolvió una respuesta inesperada. Revisa la conexión e inténtalo de nuevo.' };
      }
      if (!res.ok || !data.ok) {
        if (data.redirect) {
          followAppRedirect(data.redirect);
          return;
        }
        hideAnalysisLoading();
        hideResultHeroAndSource();
        currentAnalysisId = null;
        if (downloadPdfBtn) downloadPdfBtn.disabled = true;
        setShareControlsEnabled(false);
        let rawErr = data.error || 'No se completó la lectura. Revisa el mensaje o inténtalo más tarde.';
        if (res.status === 401) {
          rawErr = 'Sesión vencida o no válida. Inicia sesión de nuevo y repite la carga.';
        }
        if (tableroCenter) {
          tableroCenter.innerHTML =
            res.status === 402 ? buildPlanLimitErrorHtml(rawErr) : `<div class="alert error"><p>${htmlEscape(rawErr)}</p></div>`;
        }
        resultsCard?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
      hideAnalysisLoading();
      currentAnalysisId = data.analysis_id || null;
      currentShareUrl = data.share_url || null;
      if (downloadPdfBtn) {
        downloadPdfBtn.disabled = !currentAnalysisId;
      }
      setShareControlsEnabled(!!currentAnalysisId);
      renderSummary(data.summary, data.effective_plan ?? data.plan ?? 'free');
      renderCharts(data.summary);
      renderAnalysis(data.analysis);
      renderResultHero(data.title, data.created_at, data.analysis, data.summary);
      const nFuentes = data.summary.reports_detected;
      const fallbackTitle = `Lectura · ${nFuentes} fuente${nFuentes === 1 ? '' : 's'}`;
      appendToHistory({
        id: data.analysis_id,
        title: data.title || fallbackTitle,
        created_at: data.created_at || new Date().toLocaleString('es-MX', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).replace(',', ''),
        file_count: data.summary.total_files,
        days_covered: data.summary.overall_days_covered ?? 0,
        reports_detected: data.summary.reports_detected,
        resumen_ejecutivo: (data.analysis && data.analysis.resumen_ejecutivo) ? data.analysis.resumen_ejecutivo : '',
      });
      if (currentAnalysisId) markHistorySelection(currentAnalysisId);
      resultsCard?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      hideAnalysisLoading();
      hideResultHeroAndSource();
      setShareControlsEnabled(false);
      if (tableroCenter) tableroCenter.innerHTML = `<div class="alert error">${htmlEscape(err.message)}</div>`;
      resultsCard?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } finally {
      submit.disabled = false;
      submit.textContent = 'Generar lectura';
      form.removeAttribute('aria-busy');
    }
  });
}

async function openCheckout(cycle, planTier) {
  const body = new FormData();
  body.append('billing_cycle', cycle || 'monthly');
  body.append('plan_tier', planTier || 'pro');
  const res = await fetch(appUrlPath('/billing/create-checkout-session'), { method: 'POST', body });
  const data = await res.json();
  if (!res.ok || !data.ok) throw new Error(data.detail || data.error || 'No se pudo abrir Stripe Checkout.');
  window.location.href = data.url;
}

document.querySelectorAll('[data-billing-cycle], [data-plan-tier]').forEach(btn => {
  const cycle = btn.dataset.billingCycle || 'monthly';
  const tier = btn.dataset.planTier || 'pro';
  btn.addEventListener('click', async () => {
    const original = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'Abriendo…';
    try { await openCheckout(cycle, tier); }
    catch (err) { alert(err.message); btn.disabled = false; btn.textContent = original; }
  });
});

const portalBtn = document.getElementById('openPortalBtn');
if (portalBtn) {
  portalBtn.addEventListener('click', async () => {
    const original = portalBtn.textContent;
    portalBtn.disabled = true;
    portalBtn.textContent = 'Abriendo…';
    try {
      const res = await fetch(appUrlPath('/billing/create-portal-session'), { method: 'POST' });
      const data = await res.json();
      if (!res.ok || !data.ok) throw new Error(data.detail || 'No se pudo abrir el portal de Stripe.');
      window.location.href = data.url;
    } catch (err) {
      alert(err.message);
      portalBtn.disabled = false;
      portalBtn.textContent = original;
    }
  });
}

// Tablero: controles mobile para colapsar columnas (landing, mockup y panel)
document.querySelectorAll('.tablero-toggle-bar').forEach(bar => {
  const card = bar.closest('.results-card-tablero');
  if (!card) return;
  const container = card.querySelector('[data-tablero-columns]');
  if (!container) return;
  const buttons = bar.querySelectorAll('.tablero-toggle');
  buttons.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.dataset.target || 'center';
      container.dataset.active = target;
      buttons.forEach(b => b.classList.toggle('is-active', b === btn));
    });
  });
});

document.querySelector('.history-card')?.addEventListener('click', async e => {
  const delBtn = e.target.closest('.history-delete-btn');
  if (delBtn) {
    e.preventDefault();
    e.stopPropagation();
    await handleDeleteHistoryAnalysis(delBtn.dataset.analysisId, delBtn);
    return;
  }
  const item = e.target.closest('.history-item');
  if (!item || !item.dataset.analysisId) return;
  const id = item.dataset.analysisId;
  markHistorySelection(id);
  const res = await fetch(appUrlPath(`/analysis/${id}`));
  let data = {};
  try {
    data = await res.json();
  } catch {
    return;
  }
  if (!res.ok || !data.ok) return;
  if (resultsCard) resultsCard.classList.remove('hidden');
  currentAnalysisId = data.id || id;
  currentShareUrl = data.share_url || null;
  if (downloadPdfBtn) {
    downloadPdfBtn.disabled = !currentAnalysisId;
  }
  setShareControlsEnabled(!!currentAnalysisId);
  renderSummary(data.summary, data.effective_plan ?? data.plan ?? 'free');
  renderCharts(data.summary);
  renderAnalysis(data.analysis);
  renderResultHero(data.title, data.created_at, data.analysis, data.summary);
  resultsCard?.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

if (downloadPdfBtn) {
  downloadPdfBtn.addEventListener('click', async () => {
    if (!currentAnalysisId) return;
    const pdfHref = appUrlPath(`/analysis/${currentAnalysisId}/pdf`);
    const originalLabel = downloadPdfBtn.textContent;
    downloadPdfBtn.disabled = true;
    downloadPdfBtn.textContent = 'Generando PDF…';
    try {
      const res = await fetch(pdfHref, {
        method: 'GET',
        credentials: 'same-origin',
        headers: { Accept: 'application/pdf' },
      });
      if (res.status === 401) {
        let msg = 'Sesión vencida o no válida. Inicia sesión de nuevo e intenta descargar el PDF otra vez.';
        try {
          const j = await res.json();
          if (j && j.redirect) {
            followAppRedirect(j.redirect);
            return;
          }
          if (j && j.error) msg = String(j.error);
        } catch {
          /* ignore */
        }
        alert(msg);
        return;
      }
      if (!res.ok) {
        alert('No se pudo generar el PDF. Intenta de nuevo o recarga la página.');
        return;
      }
      const blob = await res.blob();
      const cd = res.headers.get('Content-Disposition') || '';
      const m = cd.match(/filename="([^"]+)"/);
      const fname = m && m[1] ? m[1] : `pullso-lectura-${currentAnalysisId}.pdf`;
      const objectUrl = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = objectUrl;
      a.download = fname;
      a.rel = 'noopener';
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(objectUrl);
    } catch (err) {
      alert(err && err.message ? err.message : 'Error al descargar el PDF.');
    } finally {
      downloadPdfBtn.disabled = false;
      downloadPdfBtn.textContent = originalLabel;
    }
  });
}

if (copyShareBtn) {
  copyShareBtn.addEventListener('click', async () => {
    if (!currentAnalysisId) return;
    shareFeedback?.classList.add('hidden');
    const url = currentShareUrl || await ensureShareUrl(currentAnalysisId);
    if (!url) {
      if (shareFeedback) {
        shareFeedback.textContent = 'No se pudo generar el enlace. Intenta de nuevo.';
        shareFeedback.classList.remove('hidden');
      }
      return;
    }
    currentShareUrl = url;
    try {
      await navigator.clipboard.writeText(url);
      if (shareFeedback) {
        shareFeedback.textContent = 'Enlace copiado. Quien lo tenga puede ver el tablero en solo lectura.';
        shareFeedback.classList.remove('hidden');
      }
    } catch {
      prompt('Copia este enlace:', url);
    }
  });
}

if (emailShareBtn) {
  emailShareBtn.addEventListener('click', async () => {
    if (!currentAnalysisId) return;
    const url = currentShareUrl || await ensureShareUrl(currentAnalysisId);
    if (!url) {
      if (shareFeedback) {
        shareFeedback.textContent = 'No se pudo generar el enlace. Intenta de nuevo.';
        shareFeedback.classList.remove('hidden');
      }
      return;
    }
    currentShareUrl = url;
    const subject = encodeURIComponent('Pullso — lectura comercial (enlace de solo lectura)');
    const body = encodeURIComponent(
      `Te comparto la lectura generada con Pullso:\n\n${url}\n\nQuien tenga el enlace puede ver el tablero sin iniciar sesión.`
    );
    window.location.href = `mailto:?subject=${subject}&body=${body}`;
  });
}

if (serverEmailShareBtn) {
  serverEmailShareBtn.addEventListener('click', async () => {
    if (!currentAnalysisId) return;
    shareFeedback?.classList.add('hidden');
    const addr = window.prompt('Correo del destinatario (Pullso enviará el enlace público):');
    if (!addr || !addr.trim()) return;
    const fd = new FormData();
    fd.append('to_email', addr.trim());
    try {
      const res = await fetch(appUrlPath(`/analysis/${currentAnalysisId}/share-email`), { method: 'POST', body: fd });
      const data = await res.json().catch(() => ({}));
      if (!res.ok || !data.ok) {
        if (shareFeedback) {
          shareFeedback.textContent = data.detail || data.error || 'No se pudo enviar el correo.';
          shareFeedback.classList.remove('hidden');
        }
        return;
      }
      if (shareFeedback) {
        shareFeedback.textContent = 'Listo: enviamos el enlace al correo que indicaste.';
        shareFeedback.classList.remove('hidden');
      }
    } catch (e) {
      if (shareFeedback) {
        shareFeedback.textContent = e.message || 'Error de red.';
        shareFeedback.classList.remove('hidden');
      }
    }
  });
}

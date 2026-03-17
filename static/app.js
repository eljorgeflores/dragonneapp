const fileInput = document.getElementById('files');
const fileList = document.getElementById('fileList');
const dropzone = document.getElementById('dropzone');
const form = document.getElementById('analyzeForm');
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
const downloadPdfBtn = document.getElementById('downloadPdfBtn');
let currentAnalysisId = null;

function renderFiles() {
  if (!fileInput || !fileList) return;
  fileList.innerHTML = '';
  [...fileInput.files].forEach(file => {
    const chip = document.createElement('div');
    chip.className = 'file-chip';
    chip.textContent = `${file.name} · ${(file.size / 1024).toFixed(1)} KB`;
    fileList.appendChild(chip);
  });
}

if (dropzone) {
  ['dragenter', 'dragover'].forEach(ev => dropzone.addEventListener(ev, e => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  }));
  ['dragleave', 'drop'].forEach(ev => dropzone.addEventListener(ev, e => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
  }));
}
if (fileInput) fileInput.addEventListener('change', renderFiles);

function htmlEscape(value) {
  return String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
}

function renderSummary(summary, plan) {
  if (resultMeta) resultMeta.textContent = `${summary.reports_detected} reporte(s) detectado(s) · ${summary.total_files} archivo(s) subidos · ${summary.overall_days_covered || 0} días cubiertos`;
  if (planBadge) {
    planBadge.textContent = plan === 'pro_plus' ? 'Pro+' : plan === 'pro' ? 'PRO' : 'GRATIS';
  }
  const cards = [
    { label: 'Archivos', value: summary.total_files },
    { label: 'Reportes', value: summary.reports_detected },
    { label: 'Días cubiertos', value: summary.overall_days_covered || 0 },
    { label: 'Máx. rango', value: summary.max_days_covered || 0 },
  ];
  if (tableroKpis) {
    tableroKpis.innerHTML = cards.map(item => `<div class="kpi"><div class="label">${item.label}</div><div class="value">${htmlEscape(item.value)}</div></div>`).join('');
  }
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
      <h3>Mix por canal (estimado)</h3>
      <div class="mix-bars">
        ${slices.length ? slices.map((c, idx) => `
          <div class="mix-bar-row">
            <span class="mix-bar-label">${htmlEscape(c.canal || 'Canal')}</span>
            <div class="mix-bar-track">
              <div class="mix-bar-fill" style="width:${percentages[idx] || 0}%;background:${pickChartColor(idx)}"></div>
            </div>
            <span class="mix-bar-pct">${percentages[idx] != null ? percentages[idx] + '%' : '—'}</span>
          </div>
        `).join('') : '<p class="muted panel-empty-copy">No hay canales en el resumen.</p>'}
      </div>
    </div>
    <div class="chart-card">
      <h3>Indicadores operativos</h3>
      <div class="columns-wrapper">
        <div class="column" style="height: 80px;"><div class="column-inner"></div></div>
        <div class="column" style="height: 110px;"><div class="column-inner"></div></div>
        <div class="column" style="height: 60px;"><div class="column-inner"></div></div>
      </div>
      <div class="column-labels">
        <span>ADR</span>
        <span>Room nights</span>
        <span>Cancelación</span>
      </div>
      <div class="mini-top" style="margin-top:8px;">
        ${adr != null ? `ADR estimado: ${htmlEscape(adr)}` : 'ADR estimado: sin datos claros'} ·
        ${roomNights != null ? `Room nights: ${htmlEscape(roomNights)}` : 'Room nights: sin datos'} ·
        ${cancelPct != null ? `Cancelación: ${htmlEscape(cancelPct)}%` : 'Cancelación: sin datos'}
      </div>
    </div>
  `;
  tableroLeft.innerHTML = chartsHTML;
}

function renderListItems(items, mode = 'plain') {
  if (!items || !items.length) return '<p class="muted panel-empty-copy">No hay datos para este apartado en el reporte subido.</p>';
  if (mode === 'metrics') {
    return items.map(item => `<div class="panel-item"><strong>${htmlEscape(item.nombre)} · ${htmlEscape(item.valor)}</strong><div class="muted">${htmlEscape(item.lectura)}</div></div>`).join('');
  }
  if (mode === 'priority') {
    return items.map(item => `<div class="panel-item"><strong>${htmlEscape(item.titulo)}</strong><div>${htmlEscape(item.detalle)}</div><div class="muted">Impacto: ${htmlEscape(item.impacto)} · Prioridad: ${htmlEscape(item.prioridad)}</div></div>`).join('');
  }
  if (mode === 'actions') {
    return items.map(item => `<div class="panel-item"><strong>${htmlEscape(item.accion)}</strong><div>${htmlEscape(item.por_que)}</div><div class="muted">Urgencia: ${htmlEscape(item.urgencia)}</div></div>`).join('');
  }
  return items.map(item => `<div class="panel-item">${htmlEscape(item)}</div>`).join('');
}

function renderAnalysis(analysis) {
  if (!tableroLeft || !tableroCenter || !tableroRight) return;

  // Columna izquierda: añadir Oportunidades y Riesgos (charts ya están)
  const leftBlocks = `
    <div class="panel-block">
      <h3>Oportunidades directo vs OTA</h3>
      ${renderListItems(analysis.oportunidades_directo_vs_ota)}
    </div>
    <div class="panel-block">
      <h3>Riesgos detectados</h3>
      ${renderListItems(analysis.riesgos_detectados)}
    </div>
  `;
  tableroLeft.insertAdjacentHTML('beforeend', leftBlocks);

  // Columna centro: Resumen ejecutivo, Métricas clave, Hallazgos prioritarios
  tableroCenter.innerHTML = `
    <div class="panel-block panel-block-resumen">
      <h3>Resumen ejecutivo</h3>
      <div class="resumen-ejecutivo-body">${htmlEscape(analysis.resumen_ejecutivo || '')}</div>
    </div>
    <div class="panel-block">
      <h3>Métricas clave</h3>
      ${renderListItems(analysis.metricas_clave, 'metrics')}
    </div>
    <div class="panel-block">
      <h3>Hallazgos prioritarios</h3>
      ${renderListItems(analysis.hallazgos_prioritarios, 'priority')}
    </div>
  `;

  // Columna derecha: Recomendaciones accionables, Datos faltantes
  tableroRight.innerHTML = `
    <div class="panel-block">
      <h3>Recomendaciones accionables</h3>
      ${renderListItems(analysis.recomendaciones_accionables, 'actions')}
    </div>
    <div class="panel-block">
      <h3>Datos faltantes</h3>
      ${renderListItems(analysis.datos_faltantes)}
    </div>
  `;

  const gate = analysis.senal_de_upgrade;
  if (gate && gate.deberia_hacer_upgrade && paywallEl) {
    paywallEl.classList.remove('hidden');
    paywallEl.innerHTML = `<strong>Upgrade recomendado.</strong> ${htmlEscape(gate.motivo || '')}`;
  } else if (paywallEl) {
    paywallEl.classList.add('hidden');
    paywallEl.innerHTML = '';
  }
}

function hideAnalysisLoading() {
  if (resultsLayout) resultsLayout.classList.remove('is-loading');
  if (resultsLoading) resultsLoading.classList.add('hidden');
}

function appendToHistory(item) {
  const card = document.querySelector('.history-card');
  if (!card) return;
  const grid = card.querySelector('#historyGrid');
  const empty = card.querySelector('#historyEmpty');
  const btn = document.createElement('button');
  btn.className = 'history-item';
  btn.dataset.analysisId = String(item.id);
  btn.innerHTML = `
    <span class="history-col history-col-date">${htmlEscape(item.created_at)}</span>
    <span class="history-col history-col-files">${item.file_count}</span>
    <span class="history-col history-col-days">${item.days_covered ?? 0}</span>
    <span class="history-col history-col-reports">${item.reports_detected}</span>
  `;
  if (grid) {
    grid.insertBefore(btn, grid.firstChild);
  } else if (empty) {
    const newGrid = document.createElement('div');
    newGrid.className = 'history-grid';
    newGrid.id = 'historyGrid';
    newGrid.appendChild(btn);
    empty.parentNode.replaceChild(newGrid, empty);
  }
}

if (form) {
  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const submit = form.querySelector('button[type="submit"]');
    submit.disabled = true;
    submit.textContent = 'Analizando…';
    resultsCard.classList.remove('hidden');
    if (resultsLayout) resultsLayout.classList.add('is-loading');
    if (resultsLoading) resultsLoading.classList.remove('hidden');
    if (tableroKpis) tableroKpis.innerHTML = '';
    if (tableroLeft) tableroLeft.innerHTML = '';
    if (tableroCenter) tableroCenter.innerHTML = '';
    if (tableroRight) tableroRight.innerHTML = '';
    if (paywallEl) paywallEl.classList.add('hidden');
    try {
      const res = await fetch('/analyze', { method: 'POST', body: new FormData(form) });
      const data = await res.json();
      if (!res.ok || !data.ok) {
        if (data.redirect) {
          window.location.href = data.redirect;
          return;
        }
        hideAnalysisLoading();
        currentAnalysisId = null;
        if (downloadPdfBtn) downloadPdfBtn.disabled = true;
        if (tableroCenter) tableroCenter.innerHTML = `<div class="alert error">${htmlEscape(data.error || 'No se pudo correr el análisis.')}</div>`;
        resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
        return;
      }
      hideAnalysisLoading();
      currentAnalysisId = data.analysis_id || null;
      if (downloadPdfBtn) {
        downloadPdfBtn.disabled = !currentAnalysisId;
      }
      renderSummary(data.summary, data.plan);
      renderCharts(data.summary);
      renderAnalysis(data.analysis);
      appendToHistory({
        id: data.analysis_id,
        title: data.title || `${data.summary.reports_detected} reporte(s)`,
        created_at: data.created_at || new Date().toLocaleString('es-MX', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' }).replace(',', ''),
        file_count: data.summary.total_files,
        days_covered: data.summary.overall_days_covered ?? 0,
        reports_detected: data.summary.reports_detected,
        resumen_ejecutivo: (data.analysis && data.analysis.resumen_ejecutivo) ? data.analysis.resumen_ejecutivo : '',
      });
      resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } catch (err) {
      hideAnalysisLoading();
      if (tableroCenter) tableroCenter.innerHTML = `<div class="alert error">${htmlEscape(err.message)}</div>`;
      resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } finally {
      submit.disabled = false;
      submit.textContent = 'Analizar reportes';
    }
  });
}

async function openCheckout(cycle, planTier) {
  const body = new FormData();
  body.append('billing_cycle', cycle || 'monthly');
  body.append('plan_tier', planTier || 'pro');
  const res = await fetch('/billing/create-checkout-session', { method: 'POST', body });
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
      const res = await fetch('/billing/create-portal-session', { method: 'POST' });
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

document.querySelector('.history-card')?.addEventListener('click', async (e) => {
  const item = e.target.closest('[data-analysis-id]');
  if (!item) return;
  const id = item.dataset.analysisId;
  const res = await fetch(`/analysis/${id}`);
  const data = await res.json();
  if (!res.ok || !data.ok) return;
  resultsCard.classList.remove('hidden');
  currentAnalysisId = data.id || id;
  if (downloadPdfBtn) {
    downloadPdfBtn.disabled = !currentAnalysisId;
  }
  renderSummary(data.summary, data.plan || 'free');
  renderCharts(data.summary);
  renderAnalysis(data.analysis);
  resultsCard.scrollIntoView({ behavior: 'smooth', block: 'start' });
});

if (downloadPdfBtn) {
  downloadPdfBtn.addEventListener('click', () => {
    if (!currentAnalysisId) return;
    window.location.href = `/analysis/${currentAnalysisId}/pdf`;
  });
}

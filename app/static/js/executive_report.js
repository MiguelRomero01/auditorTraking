/**
 * executive_report.js — JS engine for the per-auditor executive report
 * Fetches /api/executive-report and renders rich accordion cards per auditor.
 */

"use strict";

// ─── State ───────────────────────────────────────────────────────────────────
let reportData = null;
let currentSort = "name";
let activeFilter = "all";

// Instance maps for chart destruction
const chartInstances = {};

// Color palette
const PALETTE = [
  "#be185d",
  "#7c3aed",
  "#2563eb",
  "#0891b2",
  "#059669",
  "#d97706",
  "#dc2626",
  "#db2777",
  "#9333ea",
  "#1d4ed8",
];

const BUCKET_COLORS = {
  "0-25": "#ef4444",
  "26-50": "#f97316",
  "51-75": "#f59e0b",
  "76-99": "#3b82f6",
  100: "#10b981",
};

const ERROR_TYPE_COLORS = {
  "Celda Vacía": "#be185d",
  "ID Duplicado": "#7c3aed",
  "Avance Inválido": "#dc2626",
  "Enlace Inválido": "#0891b2",
  "Mes Incorrecto": "#d97706",
  "Nombre Auditor": "#9333ea",
  "Fecha Inválida": "#2563eb",
  "Error Entregable": "#f97316",
  "Inconsistencia BD": "#059669",
  "Comentario Incoherente": "#db2777",
};

const ERROR_PILL_CLASSES = {
  "Celda Vacía": "pink",
  "ID Duplicado": "blue",
  "Avance Inválido": "",
  "Enlace Inválido": "blue",
  "Mes Incorrecto": "orange",
  "Nombre Auditor": "blue",
  "Fecha Inválida": "orange",
  "Error Entregable": "orange",
  "Inconsistencia BD": "gray",
  "Comentario Incoherente": "blue",
};

// ─── Utils ───────────────────────────────────────────────────────────────────
function s(val) {
  if (val === null || val === undefined) return "Vacío";
  const str = String(val).trim();
  return !str || str.toLowerCase() === "nan" || str.toLowerCase() === "none"
    ? "Vacío"
    : str;
}

function pct(val) {
  return Math.min(Math.max(Number(val) || 0, 0), 100);
}

/** Compact ring SVG that updates its stroke-dashoffset after a tick */
function buildRing(id, progress, color) {
  const r = 30,
    c = 2 * Math.PI * r;
  const offset = c - (c * pct(progress)) / 100;
  return `
    <div class="progress-ring-wrap">
        <svg width="76" height="76" viewBox="0 0 76 76">
            <circle class="ring-bg" cx="38" cy="38" r="${r}"/>
            <circle id="ring-${id}" class="ring-fill" cx="38" cy="38" r="${r}"
                stroke="${color}"
                stroke-dasharray="${c.toFixed(2)}"
                stroke-dashoffset="${c.toFixed(2)}"
                data-offset="${offset.toFixed(2)}"/>
        </svg>
        <div class="ring-text">
            <strong>${Math.round(progress)}%</strong>
            <span>avance</span>
        </div>
    </div>`;
}

function animateRings() {
  document.querySelectorAll(".ring-fill").forEach((el) => {
    const target = parseFloat(el.dataset.offset);
    if (!isNaN(target)) {
      requestAnimationFrame(() => {
        el.style.strokeDashoffset = target;
      });
    }
  });
}

function statusColor(color) {
  const map = {
    green: "var(--green)",
    yellow: "var(--yellow)",
    orange: "var(--orange)",
    red: "var(--red)",
  };
  return map[color] || "var(--muted)";
}

// ─── Loading ─────────────────────────────────────────────────────────────────
const overlay = document.getElementById("loading-overlay");
function showLoading() {
  overlay.classList.remove("hidden");
}
function hideLoading() {
  overlay.classList.add("hidden");
}

// ─── Fetch ───────────────────────────────────────────────────────────────────
async function fetchReport() {
  showLoading();
  try {
    const res = await fetch("/api/executive-report");
    if (!res.ok) throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    reportData = await res.json();
    renderAll();
  } catch (err) {
    console.error("Error fetching executive report:", err);
    alert("Error al obtener el informe ejecutivo: " + err.message);
  } finally {
    hideLoading();
  }
}

async function refreshData() {
  const btn = document.getElementById("refresh-btn");
  btn.disabled = true;
  btn.innerHTML =
    '<span style="display:inline-block;animation:spin 0.75s linear infinite">⟳</span> Actualizando...';
  showLoading();
  try {
    const res = await fetch("/api/refresh", { method: "POST" });
    const result = await res.json();
    if (result.status === "success") {
      await fetchReport();
    } else {
      throw new Error(result.detail || "Error desconocido");
    }
  } catch (err) {
    console.error("Refresh failed:", err);
    alert("No se pudo refrescar: " + err.message);
    hideLoading();
  } finally {
    btn.disabled = false;
    btn.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" width="15" height="15" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg> Actualizar`;
  }
}

// ─── Main Render ─────────────────────────────────────────────────────────────
function renderAll() {
  if (!reportData) return;
  renderGlobalKPIs(reportData.global);
  populateFilterDropdown(reportData.auditors || []);
  renderGrid(reportData.auditors || []);

  document.getElementById("report-date").textContent =
    `📅 Generado: ${reportData.generated_at || "—"}`;
  const g = reportData.global || {};
  document.getElementById("report-scope").textContent =
    `${g.total_auditors || 0} auditores · ${g.total_activities || 0} actividades`;

  setTimeout(animateRings, 100);
}

// ─── KPIs ─────────────────────────────────────────────────────────────────────
function renderGlobalKPIs(g) {
  if (!g) return;
  txt("kpi-auditores", g.total_auditors || 0);
  txt("kpi-actividades", g.total_activities || 0);
  txt("kpi-avance", (g.avg_progress || 0) + "%");
  txt("kpi-limpias", g.clean_activities || 0);
  txt("kpi-errores", g.total_errors || 0);
  txt("kpi-criticos", g.critical_count || 0);
  txt("kpi-obs", g.with_obs_count || 0);
  txt("kpi-optimo", g.clean_count || 0);
}
function txt(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}

// ─── Dropdown ────────────────────────────────────────────────────────────────
function populateFilterDropdown(auditors) {
  const sel = document.getElementById("auditor-filter-exec");
  // clear old options except the first
  while (sel.options.length > 1) sel.remove(1);
  auditors
    .map((a) => a.name)
    .sort()
    .forEach((name) => {
      const opt = document.createElement("option");
      opt.value = name;
      opt.textContent = name;
      sel.appendChild(opt);
    });
}

// ─── Grid ────────────────────────────────────────────────────────────────────
function renderGrid(auditors) {
  // Apply filter
  let list =
    activeFilter === "all"
      ? [...auditors]
      : auditors.filter((a) => a.name === activeFilter);

  // Apply sort
  if (currentSort === "name") list.sort((a, b) => a.name.localeCompare(b.name));
  else if (currentSort === "errors")
    list.sort((a, b) => b.total_errors - a.total_errors);
  else if (currentSort === "progress")
    list.sort((a, b) => b.avg_progress - a.avg_progress);

  const grid = document.getElementById("auditor-grid");
  // Destroy old charts
  Object.keys(chartInstances).forEach((k) => {
    try {
      chartInstances[k].destroy();
    } catch (e) {}
    delete chartInstances[k];
  });
  grid.innerHTML = "";

  const badge = document.getElementById("auditor-count-badge");
  badge.textContent = `${list.length} auditor${list.length !== 1 ? "es" : ""}`;

  if (list.length === 0) {
    grid.innerHTML = `<div class="no-data"><div class="emoji">🔍</div><p>No se encontraron auditores.</p></div>`;
    return;
  }

  list.forEach((a) => {
    const card = buildAuditorCard(a);
    grid.appendChild(card);
  });

  // Animate rings after DOM is ready
  setTimeout(animateRings, 80);
  // Auto-open if single auditor
  if (list.length === 1) {
    const first = grid.querySelector(".auditor-card");
    if (first) openCard(first, list[0]);
  }
}

// ─── Card Build ───────────────────────────────────────────────────────────────
function buildAuditorCard(a) {
  const id = a.name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9_]/g, "");
  const ringColor = statusColor(a.status_color);
  const ringHtml = buildRing(id, a.avg_progress, ringColor);

  const errRate = a.error_rate || 0;

  const card = document.createElement("div");
  card.className = "auditor-card";
  card.dataset.auditor = a.name;

  card.innerHTML = `
    <div class="card-header" onclick="toggleCard(this)">
        ${ringHtml}
        <div class="card-header-info">
            <div class="auditor-name">${s(a.name)}</div>
            <span class="status-badge ${a.status_color}">
                ${statusDot(a.status_color)} ${s(a.status)}
            </span>
            <div class="card-mini-stats">
                <span class="mini-stat"><strong>${a.total_activities}</strong> actividades</span>
                <span class="mini-stat"><strong>${a.total_observations}</strong> observaciones</span>
                <span class="mini-stat"><strong>${a.total_actions}</strong> acciones</span>
                <span class="mini-stat"><strong style="color:var(--red)">${a.rows_with_errors}</strong> filas con error</span>
                <span class="mini-stat"><strong>${errRate}%</strong> tasa error</span>
            </div>
        </div>
        <div class="card-toggle">▾</div>
    </div>
    <div class="card-body">
        <div class="card-body-inner" id="body-${id}">
            <!-- Rendered on open -->
        </div>
    </div>`;

  return card;
}

function statusDot(color) {
  const c =
    { green: "#10b981", yellow: "#f59e0b", orange: "#f97316", red: "#ef4444" }[
      color
    ] || "#94a3b8";
  return `<span style="width:7px;height:7px;border-radius:50%;background:${c};display:inline-block;"></span>`;
}

// ─── Toggle Card ─────────────────────────────────────────────────────────────
function toggleCard(header) {
  const card = header.closest(".auditor-card");
  const isOpen = card.classList.contains("open");

  if (isOpen) {
    card.classList.remove("open");
  } else {
    openCard(card, getAuditorData(card.dataset.auditor));
  }
}

function openCard(card, auditor) {
  if (!auditor) return;
  card.classList.add("open");
  const id = auditor.name.replace(/\s+/g, "_").replace(/[^a-zA-Z0-9_]/g, "");
  const body = document.getElementById(`body-${id}`);
  if (body && body.children.length === 0) {
    renderCardBody(body, auditor, id);
  }
  setTimeout(animateRings, 80);
}

function getAuditorData(name) {
  if (!reportData || !reportData.auditors) return null;
  return reportData.auditors.find((a) => a.name === name) || null;
}

// ─── Card Body ────────────────────────────────────────────────────────────────
function renderCardBody(container, a, id) {
  container.innerHTML = ""; // clear

  // ── Progress distribution ──
  container.appendChild(buildProgressDist(a.progress_dist));

  // ── Charts row ──
  const chartsRow = document.createElement("div");
  chartsRow.className = "charts-row";

  // Error types donut
  const errPanel = document.createElement("div");
  errPanel.className = "chart-panel";
  errPanel.innerHTML = `<h4>Tipología de Errores</h4><div class="chart-wrap"><canvas id="chart-err-${id}"></canvas></div>`;
  chartsRow.appendChild(errPanel);

  // Errors by month bar
  const monthPanel = document.createElement("div");
  monthPanel.className = "chart-panel";
  monthPanel.innerHTML = `<h4>Errores por Periodo</h4><div class="chart-wrap"><canvas id="chart-month-${id}"></canvas></div>`;
  chartsRow.appendChild(monthPanel);

  container.appendChild(chartsRow);

  // ── Top observations ──
  if (a.top_observations && a.top_observations.length > 0) {
    container.appendChild(buildTopObs(a.top_observations));
  }

  // ── Error detail table ──
  container.appendChild(buildErrorTable(a.error_detail || [], a.total_errors));

  // ── Render charts (after DOM is attached) ──
  requestAnimationFrame(() => {
    renderErrorTypePie(id, a.error_type_dist || {});
    renderErrorsByMonthBar(id, a.errors_by_month || {});
  });
}

// ─── Progress Distribution ────────────────────────────────────────────────────
function buildProgressDist(dist) {
  const wrap = document.createElement("div");
  wrap.className = "progress-dist";
  const total = Object.values(dist || {}).reduce((s, v) => s + v, 0) || 1;
  const buckets = ["0-25", "26-50", "51-75", "76-99", "100"];
  const labels = ["0–25%", "26–50%", "51–75%", "76–99%", "100%"];

  let html = "<h4>Distribución de Avance</h4>";
  buckets.forEach((b, i) => {
    const count = (dist || {})[b] || 0;
    const pctW = ((count / total) * 100).toFixed(1);
    const color = BUCKET_COLORS[b];
    html += `
        <div class="bucket-row">
            <div class="bucket-label">${labels[i]}</div>
            <div class="bucket-bar-bg">
                <div class="bucket-bar-fill" style="width:${pctW}%; background:${color}"></div>
            </div>
            <div class="bucket-count">${count}</div>
        </div>`;
  });
  wrap.innerHTML = html;
  return wrap;
}

// ─── Top Observations ─────────────────────────────────────────────────────────
function buildTopObs(topObs) {
  const wrap = document.createElement("div");
  wrap.className = "top-obs";
  let html = "<h4>Top Observaciones con más Inconsistencias</h4>";
  topObs.forEach((o) => {
    html += `
        <div class="obs-item">
            <span class="obs-label" title="${s(o.label)}">${s(o.label)}</span>
            <span class="obs-count">${o.count} error${o.count !== 1 ? "es" : ""}</span>
        </div>`;
  });
  wrap.innerHTML = html;
  return wrap;
}

// ─── Error Table ──────────────────────────────────────────────────────────────
function buildErrorTable(errors, totalErrors) {
  const wrap = document.createElement("div");
  wrap.className = "error-table-section";

  const shown = errors.length;
  const remaining = (totalErrors || 0) - shown;

  let html = `<h4>Detalle de Inconsistencias (${totalErrors || shown} encontradas${remaining > 0 ? `, mostrando ${shown}` : ""})</h4>`;

  if (!errors || errors.length === 0) {
    html += `<p style="color: var(--green); font-size:0.82rem; padding:12px 0;">✅ Sin inconsistencias registradas</p>`;
  } else {
    html += `<div style="overflow-x:auto"><table class="err-table">
            <thead><tr>
                <th>Fila</th><th>Tipo de Error</th><th>Descripción</th><th>Periodo</th>
            </tr></thead><tbody>`;
    errors.forEach((e) => {
      const pillClass = ERROR_PILL_CLASSES[e.type] || "";
      html += `<tr>
                <td style="font-variant-numeric:tabular-nums; color:var(--muted)">${s(e.row)}</td>
                <td><span class="err-type-pill ${pillClass}">${s(e.type)}</span></td>
                <td style="max-width:280px">${s(e.message)}</td>
                <td><span class="month-tag">${s(e.month)}</span></td>
            </tr>`;
    });
    html += `</tbody></table></div>`;
    if (remaining > 0) {
      html += `<p style="font-size:0.72rem; color:var(--muted); margin-top:8px; font-style:italic;">... y ${remaining} inconsistencia(s) adicional(es) no mostrada(s).</p>`;
    }
  }
  wrap.innerHTML = html;
  return wrap;
}

// ─── Charts ───────────────────────────────────────────────────────────────────
function renderErrorTypePie(id, dist) {
  const canvas = document.getElementById(`chart-err-${id}`);
  if (!canvas) return;
  const labels = Object.keys(dist);
  const values = Object.values(dist);
  if (!labels.length) {
    canvas.parentElement.innerHTML +=
      '<p style="font-size:0.78rem;color:var(--muted);text-align:center;margin-top:30px">Sin errores ✅</p>';
    return;
  }

  const colors = labels.map((l) => ERROR_TYPE_COLORS[l] || "#94a3b8");
  const key = `err-${id}`;
  if (chartInstances[key]) chartInstances[key].destroy();
  chartInstances[key] = new Chart(canvas, {
    type: "doughnut",
    data: {
      labels,
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          hoverOffset: 8,
          borderWidth: 2,
          borderColor: "#fff",
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      cutout: "55%",
      plugins: {
        legend: {
          position: "right",
          labels: {
            font: { size: 10, family: "Outfit" },
            boxWidth: 12,
            padding: 8,
          },
        },
        tooltip: { callbacks: { label: (ctx) => ` ${ctx.label}: ${ctx.raw}` } },
      },
    },
  });
}

function renderErrorsByMonthBar(id, dist) {
  const canvas = document.getElementById(`chart-month-${id}`);
  if (!canvas) return;
  const labels = Object.keys(dist);
  const values = Object.values(dist);
  if (!labels.length) {
    canvas.parentElement.innerHTML +=
      '<p style="font-size:0.78rem;color:var(--muted);text-align:center;margin-top:30px">Sin errores ✅</p>';
    return;
  }

  const colors = labels.map((_, i) => PALETTE[i % PALETTE.length]);
  const key = `month-${id}`;
  if (chartInstances[key]) chartInstances[key].destroy();
  chartInstances[key] = new Chart(canvas, {
    type: "bar",
    data: {
      labels,
      datasets: [
        {
          label: "Errores",
          data: values,
          backgroundColor: colors,
          borderRadius: 6,
          borderWidth: 0,
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          ticks: { font: { size: 10, family: "Outfit" }, maxRotation: 35 },
          grid: { display: false },
        },
        y: {
          beginAtZero: true,
          ticks: { stepSize: 1, font: { size: 10, family: "Outfit" } },
          grid: { color: "rgba(0,0,0,0.04)" },
        },
      },
    },
  });
}

// ─── Sort ─────────────────────────────────────────────────────────────────────
window.sortCards = function (by) {
  currentSort = by;
  document
    .querySelectorAll(".sort-btn")
    .forEach((b) => b.classList.remove("active"));
  const map = {
    name: "sort-name",
    errors: "sort-errors",
    progress: "sort-progress",
  };
  const btn = document.getElementById(map[by]);
  if (btn) btn.classList.add("active");
  if (reportData) renderGrid(reportData.auditors || []);
};

// ─── Card toggle (global) ─────────────────────────────────────────────────────
window.toggleCard = function (header) {
  const card = header.closest(".auditor-card");
  const isOpen = card.classList.contains("open");
  if (isOpen) {
    card.classList.remove("open");
  } else {
    const name = card.dataset.auditor;
    const auditor = getAuditorData(name);
    openCard(card, auditor);
  }
};

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  document.getElementById("refresh-btn").addEventListener("click", refreshData);

  document
    .getElementById("auditor-filter-exec")
    .addEventListener("change", function () {
      activeFilter = this.value;
      if (reportData) renderGrid(reportData.auditors || []);
    });

  fetchReport();
});

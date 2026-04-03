document.addEventListener("DOMContentLoaded", function () {
  const refreshBtn = document.getElementById("refresh-btn");
  const lastUpdateSpan = document.getElementById("last-update");
  const auditorFilter = document.getElementById("auditor-filter");
  const loadingOverlay = document.getElementById("loading-overlay");
  const fallbackSpinner = document.getElementById("fallback-spinner");
  const lottieContainer = document.getElementById("lottie-container");

  let cachedData = null;
  let auditorChart = null;
  let errorsByAuditorChart = null;
  let errorTypeChart = null;
  let auditorMonthChart = null;
  let auditorEvolutionChart = null;

  // Pagination/Batch loading state
  let currentErrors = [];
  let visibleCount = 0;
  const PAGE_SIZE = 25;

  // --- Lottie initialization (optional) ---
  // Place your Lottie JSON file at /static/js/loading.json to enable animation.
  // Until then, the CSS spinner is used as fallback.
  lottieContainer.style.display = "none"; // Hidden by default

  fetch("/static/js/loading.json", { method: "HEAD" })
    .then((res) => {
      if (res.ok && typeof lottie !== "undefined") {
        lottieContainer.style.display = "block";
        fallbackSpinner.style.display = "none";
        lottie.loadAnimation({
          container: lottieContainer,
          renderer: "svg",
          loop: true,
          autoplay: true,
          path: "/static/js/loading.json",
        });
      }
    })
    .catch(() => {
      /* Lottie file not found, CSS spinner serves as fallback */
    });

  // --- Loading helpers ---
  function showLoading() {
    loadingOverlay.classList.remove("hidden");
  }
  function hideLoading() {
    loadingOverlay.classList.add("hidden");
  }

  // --- Sanitize display values ---
  function sanitize(val) {
    if (val === null || val === undefined) return "Vacío";
    const s = String(val).trim();
    if (s === "" || s.toLowerCase() === "nan" || s.toLowerCase() === "none")
      return "Vacío";
    return s;
  }

  // --- Circular Progress Helper ---
  function getProgressRing(pct, size = 60, stroke = 6) {
    const radius = (size - stroke) / 2;
    const circumference = radius * 2 * Math.PI;
    const offset = circumference - (Math.min(pct, 100) / 100) * circumference;
    
    // Color based on percentage
    let color = "#10b981"; // green
    if (pct < 50) color = "#ef4444"; // red
    else if (pct < 80) color = "#f59e0b"; // yellow
    
    return `
      <div class="progress-ring-wrap" style="width:${size}px; height:${size}px;">
        <svg width="${size}" height="${size}">
          <circle class="ring-bg" cx="${size/2}" cy="${size/2}" r="${radius}" />
          <circle class="ring-fill" cx="${size/2}" cy="${size/2}" r="${radius}" 
            stroke="${color}"
            style="stroke-dasharray: ${circumference}; stroke-dashoffset: ${offset};" />
        </svg>
        <div class="ring-text">
          ${Math.round(pct)}%
          <span>avance</span>
        </div>
      </div>
    `;
  }

  // --- Data fetching ---
  async function fetchData() {
    showLoading();
    try {
      const response = await fetch("/api/data");
      cachedData = await response.json();

      // Populate filter dropdown if empty
      if (auditorFilter.options.length <= 1) {
        Object.keys(cachedData.auditors)
          .sort()
          .forEach((auditor) => {
            const opt = document.createElement("option");
            opt.value = auditor;
            opt.innerText = auditor;
            opt.classList.add("text-gray-800");
            auditorFilter.appendChild(opt);
          });
      }

      updateUI();
    } catch (error) {
      console.error("Error fetching data:", error);
      alert(
        "Error al conectar con la API. Verifica que el servidor esté corriendo.",
      );
    } finally {
      hideLoading();
    }
  }

  async function refreshData() {
    refreshBtn.classList.add("opacity-50", "pointer-events-none");
    refreshBtn.innerHTML =
      '<span class="animate-spin inline-block mr-2">⟳</span> Refrescando...';
    showLoading();

    try {
      const response = await fetch("/api/refresh", { method: "POST" });
      const result = await response.json();
      if (result.status === "success") {
        // Reset dropdown so it repopulates
        while (auditorFilter.options.length > 1) auditorFilter.remove(1);
        await fetchData();
      } else {
        throw new Error(result.detail);
      }
    } catch (error) {
      console.error("Refresh failed:", error);
      alert("Fallo al refrescar desde Google Sheets: " + error.message);
    } finally {
      refreshBtn.classList.remove("opacity-50", "pointer-events-none");
      refreshBtn.innerHTML = `
                <svg xmlns="http://www.w3.org/2000/svg" class="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2.2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                </svg>
                Actualizar`;
      hideLoading();
    }
  }

  // --- UI update with filter support ---
  function updateUI() {
    const filter = auditorFilter.value;
    let data = cachedData;
    if (!data || !data.summary) return;

    let summary = data.summary;
    let errors = data.error_list || [];
    let errorTypes = data.errors_by_type || {};

    const auditorGrid = document.getElementById("auditor-grid");
    const auditorGridTitle = document.getElementById("auditor-grid-title");
    const globalCharts = document.getElementById("global-charts-section");

    if (
      filter !== "all" &&
      data.per_auditor_data &&
      data.per_auditor_data[filter]
    ) {
      const auditorInfo = data.per_auditor_data[filter];
      summary = {
        total_activities: auditorInfo.total,
        activities_with_errors: auditorInfo.errors,
        rows_with_errors: auditorInfo.rows_with_errors,
        clean_activities: auditorInfo.total - auditorInfo.rows_with_errors,
        avg_progress: auditorInfo.progress,
        activities_with_entregable: auditorInfo.activities_with_entregable,
        activities_at_90_plus: auditorInfo.activities_at_90_plus,
        last_update: data.summary.last_update,
      };
      errors = (data.error_list || []).filter((e) => e.auditor === filter);

      // Recalculate error types for this auditor
      errorTypes = {};
      errors.forEach((e) => {
        errorTypes[e.type] = (errorTypes[e.type] || 0) + 1;
      });
    }

    // Always show/update auditor grid and global charts
    if(auditorGrid) {
        auditorGrid.style.display = "grid";
        renderAuditorGrid(data.per_auditor_data, filter);
    }
    if(auditorGridTitle) auditorGridTitle.style.display = "flex";
    if(globalCharts) globalCharts.style.display = "grid";

    // Update cards
    document.getElementById("total-activities").innerText =
      summary.total_activities;
    document.getElementById("total-errors").innerText =
      summary.rows_with_errors;
    document.getElementById("clean-activities").innerText =
      summary.clean_activities;
    document.getElementById("avg-progress").innerText =
      summary.avg_progress + "%";

    const progBar = document.getElementById("progress-bar");
    progBar.style.width = Math.min(summary.avg_progress, 100) + "%";

    const errPct =
      summary.total_activities > 0
        ? ((summary.rows_with_errors / summary.total_activities) * 100).toFixed(1)
        : 0;
    document.getElementById("error-percentage").innerText =
      errPct + "% del total";

    // C5: Tasa de error = filas con error / total actividades
    const errorRate =
      summary.total_activities > 0
        ? ((summary.rows_with_errors / summary.total_activities) * 100).toFixed(1)
        : 0;
    document.getElementById("error-rate").innerText = errorRate + "%";
    const errorRateBar = document.getElementById("error-rate-bar");
    if (errorRateBar) errorRateBar.style.width = Math.min(errorRate, 100) + "%";

    // C8: Actividades >= 90%
    const at90 = summary.activities_at_90_plus ?? 0;
    document.getElementById("activities-at-90").innerText = at90;

    // C9: Actividades con entregable
    const withEntregable = summary.activities_with_entregable ?? 0;
    document.getElementById("activities-with-entregable").innerText =
      withEntregable;

    lastUpdateSpan.innerText = "Corte: " + summary.last_update;

    // Update Charts
    renderAuditorChart(data.auditors, filter);
    renderErrorsByAuditorChart(data.errors_by_auditor, filter);
    renderErrorTypeChart(errorTypes);

    // Auditor-specific charts
    const detailSection = document.getElementById("auditor-detail-section");
    if (filter !== "all") {
      detailSection.style.display = "grid";
      document.getElementById("auditor-detail-name").innerText = filter;
      document.getElementById("auditor-evolution-name").innerText = filter;
      renderAuditorMonthChart(errors, filter);
      renderAuditorEvolutionChart(errors, filter);
    } else {
      detailSection.style.display = "none";
    }

    // Update Table - Reset pagination
    currentErrors = errors;
    renderErrorTable(true); // true = reset
  }

  // --- Charts ---
  function renderAuditorChart(auditors, filter) {
    const ctx = document.getElementById("auditorChart").getContext("2d");
    if (auditorChart) auditorChart.destroy();

    const labels = Object.keys(auditors);
    const bgColors = labels.map((l) =>
      l === filter ? "rgb(190, 24, 93)" : "rgba(190, 24, 93, 0.4)",
    );

    auditorChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Cantidad de Actividades",
            data: Object.values(auditors),
            backgroundColor: bgColors,
            borderColor: "rgb(190, 24, 93)",
            borderWidth: 1,
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true } },
      },
    });
  }

  function renderErrorsByAuditorChart(errorsByAuditor, filter) {
    const ctx = document
      .getElementById("errorsByAuditorChart")
      .getContext("2d");
    if (errorsByAuditorChart) errorsByAuditorChart.destroy();

    const labels = Object.keys(errorsByAuditor);
    const bgColors = labels.map((l) =>
      l === filter ? "rgb(239, 68, 68)" : "rgba(239, 68, 68, 0.4)",
    );

    errorsByAuditorChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Cantidad de Errores",
            data: Object.values(errorsByAuditor),
            backgroundColor: bgColors,
            borderColor: "rgb(239, 68, 68)",
            borderWidth: 1,
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        indexAxis: "y",
        scales: { x: { beginAtZero: true } },
      },
    });
  }

  function renderErrorTypeChart(errorTypes) {
    const ctx = document.getElementById("errorTypeChart").getContext("2d");
    if (errorTypeChart) errorTypeChart.destroy();

    const labels = Object.keys(errorTypes);
    const values = Object.values(errorTypes);

    const palette = [
      "#be185d",
      "#8b5cf6",
      "#3b82f6",
      "#10b981",
      "#f59e0b",
      "#ef4444",
      "#6366f1",
      "#14b8a6",
      "#f97316",
      "#e11d48",
    ];

    errorTypeChart = new Chart(ctx, {
      type: "doughnut",
      data: {
        labels: labels,
        datasets: [
          {
            data: values,
            backgroundColor: palette.slice(0, labels.length),
            hoverOffset: 10,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { position: "right", labels: { font: { size: 11 } } },
        },
      },
    });
  }

  // --- Auditor Detail Charts ---
  function groupErrorsByMonth(errors) {
    const byMonth = {};
    errors.forEach((e) => {
      const m = e.month || "Sin mes";
      byMonth[m] = (byMonth[m] || 0) + 1;
    });
    return byMonth;
  }

  function renderAuditorMonthChart(errors, auditorName) {
    const ctx = document.getElementById("auditorMonthChart").getContext("2d");
    if (auditorMonthChart) auditorMonthChart.destroy();

    const byMonth = groupErrorsByMonth(errors);
    const labels = Object.keys(byMonth);
    const values = Object.values(byMonth);

    const barColors = [
      "#be185d",
      "#8b5cf6",
      "#3b82f6",
      "#10b981",
      "#f59e0b",
      "#ef4444",
      "#6366f1",
      "#14b8a6",
      "#f97316",
      "#e11d48",
      "#84cc16",
      "#06b6d4",
      "#9ca3af",
    ];

    auditorMonthChart = new Chart(ctx, {
      type: "bar",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Errores en el mes",
            data: values,
            backgroundColor: barColors.slice(0, labels.length),
            borderRadius: 8,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } },
        plugins: { legend: { display: false } },
      },
    });
  }

  function renderAuditorEvolutionChart(errors, auditorName) {
    const ctx = document
      .getElementById("auditorEvolutionChart")
      .getContext("2d");
    if (auditorEvolutionChart) auditorEvolutionChart.destroy();

    const byMonth = groupErrorsByMonth(errors);
    const labels = Object.keys(byMonth);
    const values = Object.values(byMonth);

    // Cumulative line for evolution
    let cumulative = [];
    let acc = 0;
    values.forEach((v) => {
      acc += v;
      cumulative.push(acc);
    });

    auditorEvolutionChart = new Chart(ctx, {
      type: "line",
      data: {
        labels: labels,
        datasets: [
          {
            label: "Errores en el mes",
            data: values,
            borderColor: "#be185d",
            backgroundColor: "rgba(190, 24, 93, 0.1)",
            fill: true,
            tension: 0.3,
            pointRadius: 5,
            pointBackgroundColor: "#be185d",
          },
          {
            label: "Acumulado",
            data: cumulative,
            borderColor: "#8b5cf6",
            borderDash: [5, 5],
            tension: 0.3,
            pointRadius: 4,
            pointBackgroundColor: "#8b5cf6",
            fill: false,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        scales: { y: { beginAtZero: true } },
        plugins: {
          legend: { position: "bottom" },
        },
      },
    });
  }

  // --- Error table (with batch loading) ---

  function renderErrorTable(reset = false) {
    const tbody = document.getElementById("error-table-body");
    const countSpan = document.getElementById("error-count");
    const loadMoreContainer = document.getElementById("load-more-container");

    if (reset) {
      tbody.innerHTML = "";
      visibleCount = 0;
    }

    if (!currentErrors || currentErrors.length === 0) {
      if(countSpan) countSpan.innerText = "0";
      tbody.innerHTML =
        '<tr><td colspan="4" class="px-6 py-8 text-center text-gray-500 italic">No se encontraron inconsistencias. ¡Todo limpio!</td></tr>';
      if (loadMoreContainer) loadMoreContainer.style.display = "none";
      return;
    }

    if(countSpan) countSpan.innerText = currentErrors.length;

    const nextBatch = currentErrors.slice(
      visibleCount,
      visibleCount + PAGE_SIZE,
    );

    nextBatch.forEach((err) => {
      const row = document.createElement("tr");
      row.classList.add("hover:bg-gray-50", "transition-colors");
      row.innerHTML = `
                <td class="px-6 py-3 font-mono text-gray-400 text-sm">${err.row_index}</td>
                <td class="px-6 py-3 text-sm font-semibold text-gray-700">${sanitize(err.auditor)}</td>
                <td class="px-6 py-3"><span class="text-xs font-bold text-pink-600 uppercase bg-pink-50 px-2 py-1 rounded-full">${sanitize(err.type)}</span></td>
                <td class="px-6 py-3 text-sm text-gray-600">${sanitize(err.message)}</td>
            `;
      tbody.appendChild(row);
    });

    visibleCount += nextBatch.length;

    if (loadMoreContainer) {
      loadMoreContainer.style.display = visibleCount < currentErrors.length ? "block" : "none";
    }
  }

  // --- Auditor Grid Helper ---
  function renderAuditorGrid(perAuditorData, activeFilter = "all") {
      const container = document.getElementById("auditor-grid");
      if(!container) return;
      container.innerHTML = "";

      Object.entries(perAuditorData).forEach(([auditor, info]) => {
          const card = document.createElement("div");
          const isActive = auditor === activeFilter;
          
          card.classList.add("glass-card", "p-5", "flex", "items-center", "gap-5", "hover:scale-[1.02]", "transition-all", "cursor-pointer");
          if (isActive) {
              card.classList.add("ring-2", "ring-pink-500", "bg-pink-50/30");
          }

          card.onclick = () => {
              const prevFilter = auditorFilter.value;
              auditorFilter.value = (auditor === prevFilter) ? "all" : auditor;
              updateUI();
              // Switch to general tab to see the details of the filtered auditor
              if (typeof switchTab === 'function') switchTab('general');
              window.scrollTo({ top: 0, behavior: 'smooth' });
          };

          const errorPct = info.total > 0 ? (info.rows_with_errors / info.total * 100) : 0;
          let statusColor = "green";
          let statusText = "Óptimo";
          if (errorPct > 20) { statusColor = "red"; statusText = "Crítico"; }
          else if (errorPct > 10) { statusColor = "orange"; statusText = "Alerta"; }
          else if (errorPct > 0) { statusColor = "yellow"; statusText = "Regular"; }

          const statusBadge = `
            <span class="px-2 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider
              ${statusColor === 'green' ? 'bg-green-100 text-green-700' : ''}
              ${statusColor === 'yellow' ? 'bg-yellow-100 text-yellow-700' : ''}
              ${statusColor === 'orange' ? 'bg-orange-100 text-orange-700' : ''}
              ${statusColor === 'red' ? 'bg-red-100 text-red-700' : ''}
            ">${statusText}</span>
          `;

          card.innerHTML = `
              <div class="flex-shrink-0">${getProgressRing(info.progress, 70)}</div>
              <div class="flex-1 min-w-0">
                  <div class="flex items-center justify-between gap-2 mb-1">
                      <h4 class="font-extrabold text-gray-800 truncate ${isActive ? 'text-pink-700' : ''}">${auditor}</h4>
                      ${statusBadge}
                  </div>
                  <div class="grid grid-cols-2 gap-y-1 text-[11px] text-gray-500">
                      <div>Total: <strong class="text-gray-700">${info.total}</strong></div>
                      <div>Limpias: <strong class="text-gray-700">${info.total - info.rows_with_errors}</strong></div>
                      <div>Errores: <strong class="text-pink-600">${info.rows_with_errors}</strong></div>
                      <div>Tasa: <strong class="text-gray-700">${errorPct.toFixed(1)}%</strong></div>
                  </div>
              </div>
          `;
          container.appendChild(card);
      });
  }

  // --- Event listeners ---
  refreshBtn.addEventListener("click", refreshData);
  auditorFilter.addEventListener("change", updateUI);

  const loadMoreBtn = document.getElementById("load-more-btn");
  if (loadMoreBtn) {
    loadMoreBtn.addEventListener("click", () => renderErrorTable(false));
  }

  const observer = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && visibleCount < currentErrors.length) {
        renderErrorTable(false);
      }
    },
    { threshold: 0.1 },
  );

  if (loadMoreBtn) observer.observe(loadMoreBtn);

  fetchData();
});

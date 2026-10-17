const HEAT_LEVELS = 10;

// One level per 10%, matching the retention-heat-1 to retention-heat-10 classes.
function heatLevel(percentage) {
  return Math.max(1, Math.min(HEAT_LEVELS, Math.floor((percentage || 0) / 10) + 1));
}

function computeStartDate() {
  const d = new Date();
  d.setDate(d.getDate() - d.getDay() - 84);
  return d.toISOString().split("T")[0];
}

async function fetchAllPages(url) {
  const results = [];
  let next = url;
  while (next) {
    const response = await fetch(next);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const data = await response.json();
    results.push(...(data.results || []));
    next = data.next || null;
  }
  return results;
}

function buildGridData(allData, kind) {
  const filtered = allData.filter((item) => item.kind === kind);
  // Newest cohorts at top — sort descending by start date
  filtered.sort((a, b) => (a.start > b.start ? -1 : a.start < b.start ? 1 : 0));
  const limited = filtered.slice(0, 12);

  const points = [];
  for (const cohort of limited) {
    const cohortSize = cohort.size;
    cohort.retention_metrics.forEach((metric, idx) => {
      const percentage = cohortSize > 0 ? (metric.size / cohortSize) * 100 : 0;
      points.push({
        x: String(idx + 1),
        y: cohort.start,
        v: metric.size,
        percentage,
      });
    });
  }

  const rowLabels = limited.map((c) => c.start);
  return { points, rowLabels };
}

function buildLegend() {
  const legend = document.createElement("div");
  legend.className = "retention-legend";
  legend.style.cssText = "display:flex;flex-wrap:wrap;gap:4px;margin-top:8px;font-size:12px;";

  for (let level = 1; level <= HEAT_LEVELS; level++) {
    const span = document.createElement("span");
    span.className = `retention-heat-${level}`;
    span.style.cssText = "padding:2px 6px;border-radius:2px;";
    span.textContent = `≥${(level - 1) * 10}%`;
    legend.appendChild(span);
  }

  return legend;
}

function buildGridElement(points, rowLabels) {
  const COLUMNS = 12;
  // Index points by [row][col]
  const rowIndex = new Map(rowLabels.map((d, i) => [d, i]));
  const cells = rowLabels.map(() => new Array(COLUMNS).fill(null));
  for (const p of points) {
    const r = rowIndex.get(p.y);
    const c = parseInt(p.x, 10) - 1;
    if (r != null && c >= 0 && c < COLUMNS) cells[r][c] = p;
  }

  const grid = document.createElement("div");
  grid.className = "retention-grid";
  grid.style.cssText = `
    display: grid;
    grid-template-columns: auto repeat(${COLUMNS}, 1fr);
    gap: 1px;
    font-size: 12px;
  `;

  // Header row: top-left empty, then column labels 1..12
  const corner = document.createElement("div");
  corner.className = "retention-heading";
  corner.style.cssText = "padding:4px;";
  grid.appendChild(corner);
  for (let c = 1; c <= COLUMNS; c++) {
    const cell = document.createElement("div");
    cell.className = "retention-heading";
    cell.style.cssText = "padding:4px;text-align:center;font-weight:600;";
    cell.textContent = String(c);
    grid.appendChild(cell);
  }

  // Body rows
  for (let r = 0; r < rowLabels.length; r++) {
    const rowHeader = document.createElement("div");
    rowHeader.className = "retention-heading";
    rowHeader.style.cssText = "padding:4px;white-space:nowrap;";
    rowHeader.textContent = rowLabels[r];
    grid.appendChild(rowHeader);

    for (let c = 0; c < COLUMNS; c++) {
      const p = cells[r][c];
      const cell = document.createElement("div");
      cell.className = `retention-cell ${p ? `retention-heat-${heatLevel(p.percentage)}` : "retention-empty"}`;
      cell.style.cssText = "padding:4px;text-align:center;";
      if (p) {
        const pct = Math.round(p.percentage);
        cell.textContent = `${p.v.toLocaleString()} (${pct}%)`;
        cell.title = `${rowLabels[r]} · ${gettext("Week")} ${c + 1}: ${p.v.toLocaleString()} (${pct}%)`;
      }
      grid.appendChild(cell);
    }
  }

  return grid;
}

function renderRetentionChart(chartArea, allData, kind) {
  const { points, rowLabels } = buildGridData(allData, kind);

  // Remove any previous grid + legend, preserve inline-controls
  for (const child of Array.from(chartArea.children)) {
    if (!child.classList.contains("inline-controls")) child.remove();
  }

  if (rowLabels.length === 0) {
    const msg = document.createElement("p");
    msg.textContent = gettext("No cohort data available for this period.");
    chartArea.appendChild(msg);
    return;
  }

  const header = document.createElement("p");
  header.textContent = gettext("Weeks since cohort start");
  header.className = "retention-caption";
  header.style.cssText = "font-size:12px;margin:8px 0 4px;";
  chartArea.appendChild(header);

  const grid = buildGridElement(points, rowLabels);
  chartArea.appendChild(grid);
  chartArea.appendChild(buildLegend());
}

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("kpi-cohort-analysis");
  if (!container) return;

  const startDate = computeStartDate();
  const url = `${container.dataset.url}?start=${startDate}`;
  const defaultKind = container.dataset.contributorType || "contributor:kb:en-US";
  const chartArea = container.querySelector("#retention-chart") || container;

  fetchAllPages(url)
    .then((allData) => {
      renderRetentionChart(chartArea, allData, defaultKind);

      const select = document.getElementById("toggle-cohort-type");
      if (select) {
        select.addEventListener("change", () => {
          renderRetentionChart(chartArea, allData, select.value);
        });
      }
    })
    .catch(() => {
      for (const child of Array.from(chartArea.children)) {
        if (!child.classList.contains("inline-controls")) {
          child.remove();
        }
      }
      const err = document.createElement("p");
      err.className = "error";
      err.textContent = gettext("Error loading graph");
      chartArea.appendChild(err);
    });
});

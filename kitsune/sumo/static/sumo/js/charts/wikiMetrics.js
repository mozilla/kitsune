import { renderLineChart } from "sumo/js/charts";
import { parseISO } from "date-fns";

const COLORS = [
  "#5d84b2", "#aa4643", "#89a54e", "#80699b",
  "#3d96ae", "#db843d", "#92a8cd", "#a47d7c",
  "#b5ca92", "#c98531", "#db75c2",
];

const CHART_CONFIGS = [
  { id: "percent-localized-top100", code: "percent_localized_top100", yLabel: () => gettext("% Localized"), max: 100 },
  { id: "percent-localized-top20",  code: "percent_localized_top20",  yLabel: () => gettext("% Localized"), max: 100 },
  { id: "percent-localized-all",    code: "percent_localized_all",    yLabel: () => gettext("% Localized"), max: 100 },
  { id: "active-contributors",      code: "active_contributors",      yLabel: () => gettext("Contributors"), max: null },
];

document.addEventListener("DOMContentLoaded", () => {
  if (document.body.classList.contains("aggregated-metrics")) {
    initAggregatedMetrics();
  }
  if (document.body.classList.contains("locale-metrics")) {
    initLocaleMetrics();
  }
});

async function initAggregatedMetrics() {
  const container = document.getElementById("dashboard-readouts");
  const url = container?.dataset.url;
  if (!url) return;

  let payload;
  try {
    const response = await fetch(url);
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    payload = await response.json();
  } catch {
    const loading = document.querySelector(".loading-data");
    if (loading) loading.textContent = gettext("Error loading dashboard data");
    return;
  }

  document.querySelector(".loading-data")?.remove();
  container.style.display = "";

  // Every locale present across any code.
  const allLocales = [
    ...new Set(Object.values(payload).flatMap((byLocale) => Object.keys(byLocale))),
  ].sort();

  const picker = document.getElementById("locale-picker");
  const sidebarLocales = picker?.dataset.locales
    ? JSON.parse(picker.dataset.locales).map((l) => (Array.isArray(l) ? l[0] : l))
    : allLocales;
  // The first sidebar locale is en-US (the source); default-checked = the next 10
  const defaultLocales = new Set(sidebarLocales.slice(1, 11));

  if (picker) {
    picker.querySelectorAll("input[type=checkbox]").forEach((cb, idx) => {
      cb.checked = idx > 0 && idx <= 10;
    });
  }

  const schedule = window.requestIdleCallback || ((cb) => setTimeout(cb, 0));
  const charts = [];
  schedule(() => {
    for (const cfg of CHART_CONFIGS) {
      const section = document.getElementById(cfg.id);
      if (!section) continue;
      const byLocale = payload[cfg.code] || {};
      const chart = renderMultiLocaleChart(section, byLocale, allLocales, defaultLocales, cfg);
      if (chart) charts.push({ chart });
    }

    if (picker) {
      picker.querySelectorAll("input[type=checkbox]").forEach((cb) => {
        cb.addEventListener("change", () => updateVisibleLocales(charts));
      });
    }
  });
}

async function initLocaleMetrics() {
  const wikimetricSection = document.getElementById("active-contributors")
    || document.getElementById("localization-metrics");
  const voteSection = document.getElementById("kpi-vote");

  const schedule = window.requestIdleCallback || ((cb) => setTimeout(cb, 0));

  // Wiki-metric charts — single locale, one payload keyed by code.
  if (wikimetricSection?.dataset.url) {
    try {
      const response = await fetch(wikimetricSection.dataset.url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const byCode = seriesByCode(await response.json());

      schedule(() => {
        const localization = document.getElementById("localization-metrics");
        if (localization) {
          renderLocaleLocalizationChart(localization, byCode);
        }
        const contributors = document.getElementById("active-contributors");
        if (contributors) {
          renderLocaleContributorsChart(contributors, byCode);
        }
      });
    } catch {
      const target = wikimetricSection.querySelector(".rickshaw") || wikimetricSection;
      target.textContent = gettext("Error loading graph");
    }
  }

  // Helpful-votes chart — separate endpoint.
  if (voteSection?.dataset.url) {
    try {
      const response = await fetch(voteSection.dataset.url);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      schedule(() => renderHelpfulVotesChart(voteSection, data.objects || []));
    } catch {
      const target = voteSection.querySelector(".rickshaw") || voteSection;
      target.textContent = gettext("Error loading graph");
    }
  }
}

function seriesByCode(payload) {
  // payload is {code: {locale: [{date, value}]}} for a single locale; collapse
  // to {code: [{date, value}]} by taking that one locale's series.
  const out = {};
  for (const [code, byLocale] of Object.entries(payload)) {
    out[code] = Object.values(byLocale)[0] || [];
  }
  return out;
}

function replaceWithCanvas(section, height = 320) {
  const old = section.querySelector(".rickshaw");
  if (old) old.remove();
  const wrap = document.createElement("div");
  wrap.style.cssText = `position: relative; height: ${height}px; width: 100%; margin-bottom: 16px;`;
  const canvas = document.createElement("canvas");
  wrap.appendChild(canvas);
  section.appendChild(wrap);
  return canvas;
}

function renderLocaleLocalizationChart(section, byCode) {
  const canvas = replaceWithCanvas(section);
  const codes = [
    { code: "percent_localized_top100", label: gettext("Top 100 Articles"), color: "#5d84b2" },
    { code: "percent_localized_top20",  label: gettext("Top 20 Articles"),  color: "#aa4643" },
    { code: "percent_localized_all",    label: gettext("All Articles"),     color: "#89a54e" },
  ];

  const datasets = codes.map(({ code, label, color }) => ({
    label,
    borderColor: color,
    backgroundColor: color,
    pointRadius: 0,
    borderWidth: 1.5,
    fill: false,
    data: (byCode[code] || []).map((p) => ({ x: parseISO(p.date), y: p.value })),
  }));

  renderLineChart(canvas, lineChartOptions(datasets, {
    yTitle: gettext("% Localized"),
    max: 100,
    valueFormatter: (v) => `${v.toFixed(1)}%`,
  }));
}

function renderLocaleContributorsChart(section, byCode) {
  const canvas = replaceWithCanvas(section);
  const dataset = {
    label: gettext("Active Contributors"),
    borderColor: "#5d84b2",
    backgroundColor: "rgba(93,132,178,0.15)",
    pointRadius: 0,
    borderWidth: 1.5,
    fill: true,
    data: (byCode["active_contributors"] || []).map((p) => ({ x: parseISO(p.date), y: p.value })),
  };
  renderLineChart(canvas, lineChartOptions([dataset], {
    yTitle: gettext("Contributors"),
    max: null,
    valueFormatter: (v) => v.toLocaleString(),
  }));
}

function renderHelpfulVotesChart(section, objects) {
  const canvas = replaceWithCanvas(section);
  const sorted = [...objects].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
  const dataset = {
    label: gettext("Article Votes: % Helpful"),
    borderColor: "#aa4643",
    backgroundColor: "rgba(170,70,67,0.15)",
    pointRadius: 0,
    borderWidth: 1.5,
    fill: true,
    data: sorted.map(o => ({
      x: parseISO(o.date),
      y: o.kb_votes > 0 ? (100 * o.kb_helpful) / o.kb_votes : null,
    })),
  };
  renderLineChart(canvas, lineChartOptions([dataset], {
    yTitle: gettext("% Helpful"),
    max: 100,
    valueFormatter: (v) => `${v.toFixed(1)}%`,
  }));
}

function lineChartOptions(datasets, { yTitle, max, valueFormatter }) {
  return {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: "time",
          time: {
            tooltipFormat: "PP",
            displayFormats: { day: "MMM d", week: "MMM d", month: "MMM yyyy", quarter: "MMM yyyy", year: "yyyy" },
          },
        },
        y: {
          beginAtZero: true,
          max,
          title: { display: true, text: yTitle },
        },
      },
      plugins: {
        legend: { position: "bottom" },
        tooltip: {
          mode: "index",
          callbacks: {
            label: (ctx) => {
              const v = ctx.parsed.y;
              if (v == null) return null;
              return `${ctx.dataset.label}: ${valueFormatter(v)}`;
            },
          },
        },
      },
    },
  };
}

function renderMultiLocaleChart(section, byLocale, allLocales, visibleLocales, cfg) {
  const oldRickshaw = section.querySelector(".rickshaw");
  if (oldRickshaw) oldRickshaw.remove();

  const wrap = document.createElement("div");
  wrap.style.cssText = "position: relative; height: 320px; width: 100%; margin-bottom: 16px;";
  const canvas = document.createElement("canvas");
  wrap.appendChild(canvas);
  section.appendChild(wrap);

  const datasets = allLocales.map((locale, i) => ({
    label: locale,
    borderColor: COLORS[i % COLORS.length],
    backgroundColor: COLORS[i % COLORS.length],
    pointRadius: 0,
    borderWidth: 1.2,
    fill: false,
    hidden: !visibleLocales.has(locale),
    data: (byLocale[locale] || []).map((p) => ({ x: parseISO(p.date), y: p.value })),
  }));

  return renderLineChart(canvas, {
    type: "line",
    data: { datasets },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: "time",
          time: {
            tooltipFormat: "PP",
            displayFormats: { day: "MMM d", week: "MMM d", month: "MMM yyyy", quarter: "MMM yyyy", year: "yyyy" },
          },
        },
        y: {
          beginAtZero: true,
          max: cfg.max,
          title: { display: true, text: cfg.yLabel() },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
          display: false,
        },
        tooltip: {
          mode: "nearest",
          intersect: false,
          callbacks: {
            label: (ctx) => {
              const v = ctx.parsed.y;
              if (v == null) return null;
              const formatted = cfg.max === 100 ? `${v.toFixed(1)}%` : v.toLocaleString();
              return `${ctx.dataset.label}: ${formatted}`;
            },
          },
        },
      },
    },
  });
}

function updateVisibleLocales(charts) {
  const checkedLocales = new Set(
    Array.from(document.querySelectorAll("#locale-picker input[type=checkbox]:checked")).map(
      (cb) => cb.value,
    ),
  );
  for (const { chart } of charts) {
    chart.data.datasets.forEach((ds) => {
      ds.hidden = !checkedLocales.has(ds.label);
    });
    chart.update();
  }
}

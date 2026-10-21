import { renderLineChart } from "sumo/js/charts";
import { parseISO } from "date-fns";

const COLORS = {
  blue: "#5d84b2",
  red: "#aa4643",
  green: "#89a54e",
  purple: "#80699b",
  orange: "#C98531",
  magenta: "#DB75C2",
  cyan: "#3d96ae",
  brown: "#a47d7c",
  lime: "#b5ca92",
};

// Each entry: list of datasets to plot. Each dataset has:
//  - label: gettext-wrapped display label
//  - color: hex
//  - axis: "y" (counts) or "y1" (percent)
//  - extract: (object) -> y value (or null)
//  - dashed?: bool
//  - filled?: bool
const CHART_SPECS = {
  questions: () => [
    { label: gettext("Questions"),                 color: COLORS.blue,    axis: "y",  filled: true,  extract: (o) => o.questions },
    { label: gettext("Solved"),                    color: COLORS.red,     axis: "y",  filled: true,  extract: (o) => o.solved },
    { label: gettext("Responded in 24 hours"),     color: COLORS.green,   axis: "y",  filled: true,  extract: (o) => o.responded_24 },
    { label: gettext("Responded in 72 hours"),     color: COLORS.purple,  axis: "y",  filled: true,  extract: (o) => o.responded_72 },
    { label: gettext("Not responded in 24 hours"), color: COLORS.orange,  axis: "y",  filled: true,  extract: (o) => (o.questions || 0) - (o.responded_24 || 0) },
    { label: gettext("Not responded in 72 hours"), color: COLORS.magenta, axis: "y",  filled: true,  extract: (o) => (o.questions || 0) - (o.responded_72 || 0) },
    { label: gettext("% Solved"),                  color: COLORS.red,     axis: "y1", dashed: true,  extract: (o) => o.questions > 0 ? (100 * o.solved) / o.questions : null },
    { label: gettext("% Responded in 24 hours"),   color: COLORS.green,   axis: "y1", dashed: true,  extract: (o) => o.questions > 0 ? (100 * o.responded_24) / o.questions : null },
    { label: gettext("% Responded in 72 hours"),   color: COLORS.purple,  axis: "y1", dashed: true,  extract: (o) => o.questions > 0 ? (100 * o.responded_72) / o.questions : null },
  ],
  vote: () => [
    { label: gettext("Article Votes: % Helpful"), color: COLORS.blue, axis: "y1", extract: (o) => o.kb_votes  > 0 ? (100 * o.kb_helpful)  / o.kb_votes  : null },
    { label: gettext("Answer Votes: % Helpful"),  color: COLORS.red,  axis: "y1", extract: (o) => o.ans_votes > 0 ? (100 * o.ans_helpful) / o.ans_votes : null },
  ],
  activeContributors: () => [
    { label: gettext("en-US KB"),       color: COLORS.blue,  axis: "y", extract: (o) => o.en_us },
    { label: gettext("non en-US KB"),   color: COLORS.red,   axis: "y", extract: (o) => o.non_en_us },
    { label: gettext("Support Forums"), color: COLORS.green, axis: "y", extract: (o) => o.support_forum },
  ],
  ctr: () => [
    { label: gettext("Click Through Rate %"), color: COLORS.blue, axis: "y1", extract: (o) => o.searches > 0 ? (100 * o.clicks) / o.searches : null },
  ],
  visitors: () => [
    { label: gettext("Visitors"), color: COLORS.blue, axis: "y", filled: true, extract: (o) => o.visitors },
  ],
  l10n: () => [
    { label: gettext("L10n Coverage"), color: COLORS.blue, axis: "y1", extract: (o) => o.coverage },
  ],
};

async function fetchAllPages(url, maxPages = 60) {
  const out = [];
  let next = url;
  let count = 0;
  while (next && count < maxPages) {
    const r = await fetch(next);
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const d = await r.json();
    out.push(...(d.objects || []));
    next = d.next;
    count++;
  }
  return out;
}

function replaceWithCanvas(section, height = 320) {
  section.querySelectorAll(".rickshaw").forEach((el) => el.remove());
  const wrap = document.createElement("div");
  wrap.style.cssText = `position: relative; height: ${height}px; width: 100%; margin-bottom: 16px;`;
  const canvas = document.createElement("canvas");
  wrap.appendChild(canvas);
  section.appendChild(wrap);
  return canvas;
}

function buildConfig(datums, specFactory) {
  const specs = specFactory();
  const hasY1 = specs.some((s) => s.axis === "y1");
  const datasets = specs.map((s) => ({
    label: s.label,
    borderColor: s.color,
    backgroundColor: s.color,
    pointRadius: 0,
    borderWidth: 1.5,
    fill: !!s.filled,
    borderDash: s.dashed ? [6, 4] : undefined,
    yAxisID: s.axis,
    data: datums.map((o) => ({ x: parseISO(o.date), y: s.extract(o) })),
  }));

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
          display: specs.some((s) => s.axis === "y"),
          beginAtZero: true,
          position: "left",
          title: { display: true, text: gettext("Count") },
        },
        y1: {
          display: hasY1,
          beginAtZero: true,
          position: "right",
          min: 0,
          max: 100,
          grid: { drawOnChartArea: false },
          title: { display: true, text: gettext("Percent") },
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
              const isPct = ctx.dataset.yAxisID === "y1";
              return `${ctx.dataset.label}: ${isPct ? v.toFixed(1) + "%" : v.toLocaleString()}`;
            },
          },
        },
      },
    },
  };
}

document.addEventListener("DOMContentLoaded", () => {
  const graphDivs = document.querySelectorAll('.graph[data-chart-type="rickshaw"]');
  if (graphDivs.length === 0) return;

  const schedule = window.requestIdleCallback || ((cb) => setTimeout(cb, 0));

  graphDivs.forEach(async (div) => {
    const slug = div.dataset.slug;
    const specFactory = CHART_SPECS[slug];
    const section = div.closest("section");
    if (!specFactory || !section) return;

    const url = section.dataset.url;
    if (!url) return;

    try {
      const datums = await fetchAllPages(url);
      const sorted = [...datums].sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));
      const canvas = replaceWithCanvas(section);
      schedule(() => renderLineChart(canvas, buildConfig(sorted, specFactory)));
    } catch {
      const target = section.querySelector(".rickshaw") || section;
      target.textContent = gettext("Error loading graph");
    }
  });
});

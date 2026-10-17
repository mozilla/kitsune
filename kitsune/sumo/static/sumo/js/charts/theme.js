import { Chart } from "chart.js";
import { color } from "chart.js/helpers";

const SERIES_COUNT = 11;
const TOKEN = Symbol("chart color token");
const resolved = new Map();
const datasetTokens = new WeakMap();
let chartJsDefaults = null;

function readColor(name) {
  const value = window.getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value && color(value).valid ? value : undefined;
}

function resolveColor(name, alpha) {
  const key = `${name} ${alpha}`;
  if (!resolved.has(key)) {
    const value = readColor(name) ?? Chart.defaults.color;
    resolved.set(key, alpha === 1 ? value : color(value).alpha(alpha).rgbString());
  }
  return resolved.get(key);
}

export function chartColor(name, alpha = 1) {
  return { [TOKEN]: name, alpha };
}

export function seriesColor(index, alpha = 1) {
  return chartColor(`--chart-${(index % SERIES_COUNT) + 1}`, alpha);
}

// Plain strings keep Chart.js's shared options, which scriptable colors would turn off.
export function resolveChartColors(datasets) {
  datasets.forEach((dataset) => {
    if (!datasetTokens.has(dataset)) {
      const tokens = Object.entries(dataset)
        .filter(([, value]) => value?.[TOKEN])
        .map(([property, value]) => [property, value[TOKEN], value.alpha]);
      datasetTokens.set(dataset, tokens);
    }
    datasetTokens.get(dataset).forEach(([property, name, alpha]) => {
      dataset[property] = resolveColor(name, alpha);
    });
  });
}

export function applyChartTheme() {
  const tooltip = Chart.defaults.plugins.tooltip;
  // Chart.js's own defaults stand in for a token that is missing or isn't a color.
  if (!chartJsDefaults) {
    chartJsDefaults = {
      color: Chart.defaults.color,
      borderColor: Chart.defaults.borderColor,
      tooltip: { ...tooltip },
    };
  }
  resolved.clear();

  const tooltipText = readColor("--chart-tooltip-text");
  Chart.defaults.color = readColor("--chart-text") ?? chartJsDefaults.color;
  Chart.defaults.borderColor = readColor("--chart-grid") ?? chartJsDefaults.borderColor;
  Object.assign(tooltip, {
    backgroundColor: readColor("--chart-tooltip-bg") ?? chartJsDefaults.tooltip.backgroundColor,
    titleColor: tooltipText ?? chartJsDefaults.tooltip.titleColor,
    bodyColor: tooltipText ?? chartJsDefaults.tooltip.bodyColor,
    footerColor: tooltipText ?? chartJsDefaults.tooltip.footerColor,
    borderColor: readColor("--chart-tooltip-border") ?? chartJsDefaults.tooltip.borderColor,
    multiKeyBackground:
      readColor("--chart-tooltip-swatch-bg") ?? chartJsDefaults.tooltip.multiKeyBackground,
    // The light border is transparent, so the width only shows where a theme colors it.
    borderWidth: 1,
  });
}

function redrawCharts() {
  applyChartTheme();
  Object.values(Chart.instances).forEach((chart) => {
    resolveChartColors(chart.data?.datasets ?? []);
    // Chart.js copies default scale colors into each scale at build and update() keeps them, so clear them.
    Object.values(chart.config?.options?.scales ?? {}).forEach((scale) => {
      delete scale.ticks?.color;
      delete scale.title?.color;
      delete scale.grid?.color;
      delete scale.border?.color;
    });
    chart.update("none");
  });
}

document.addEventListener("sumo:themechange", redrawCharts);
// Print uses the light theme, and a canvas only shows it once it is drawn again.
window.matchMedia?.("print")?.addEventListener?.("change", redrawCharts);

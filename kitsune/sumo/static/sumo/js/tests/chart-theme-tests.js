import { expect } from "chai";
import sinon from "sinon";
import { Chart } from "chart.js";

import "sumo/js/charts";
import { applyChartTheme, resolveChartColors, seriesColor } from "sumo/js/charts/theme";

describe("chart theme", () => {
  const root = document.documentElement;
  const tooltip = Chart.defaults.plugins.tooltip;
  let style;
  let saved;

  beforeEach(() => {
    saved = {
      color: Chart.defaults.color,
      borderColor: Chart.defaults.borderColor,
      tooltip: { ...tooltip },
    };
    style = document.createElement("style");
    style.textContent = `
      :root {
        --chart-text: #111111;
        --chart-grid: #cccccc;
        --chart-tooltip-bg: #222222;
        --chart-tooltip-text: #ffffff;
        --chart-1: #aa0000;
      }
      [data-theme="dark"] {
        --chart-text: #eeeeee;
        --chart-grid: #444444;
        --chart-tooltip-bg: #333333;
        --chart-tooltip-text: #fafafa;
        --chart-1: #00aa00;
      }`;
    document.head.appendChild(style);
  });

  afterEach(() => {
    style.remove();
    root.removeAttribute("data-theme");
    delete Chart.instances.stub;
    Chart.defaults.color = saved.color;
    Chart.defaults.borderColor = saved.borderColor;
    Object.assign(tooltip, saved.tooltip);
  });

  it("reads the tokens and re-applies them to live charts on sumo:themechange", () => {
    const dataset = { borderColor: seriesColor(0), backgroundColor: seriesColor(11, 0.15) };
    // Chart.js copies the default scale colors into each scale config when a chart is built.
    const scale = { ticks: { color: "#111111" }, grid: { color: "#cccccc" } };
    let atUpdate;
    const chart = {
      data: { datasets: [dataset] },
      config: { options: { scales: { y: scale } } },
      update: sinon.spy(() => {
        atUpdate = {
          line: dataset.borderColor,
          staleScaleColors: [scale.ticks.color, scale.grid.color].filter(Boolean),
        };
      }),
    };
    Chart.instances.stub = chart;

    applyChartTheme();
    resolveChartColors([dataset]);
    expect(Chart.defaults.color).to.equal("#111111");
    expect(Chart.defaults.borderColor).to.equal("#cccccc");
    expect(tooltip.backgroundColor).to.equal("#222222");
    expect(tooltip.bodyColor).to.equal("#ffffff");
    expect(dataset.borderColor).to.equal("#aa0000");
    expect(dataset.backgroundColor).to.equal("rgba(170, 0, 0, 0.15)");

    root.setAttribute("data-theme", "dark");
    document.dispatchEvent(
      new CustomEvent("sumo:themechange", { detail: { theme: "dark", preference: "dark" } })
    );

    expect(Chart.defaults.color).to.equal("#eeeeee");
    expect(Chart.defaults.borderColor).to.equal("#444444");
    expect(tooltip.backgroundColor).to.equal("#333333");
    expect(tooltip.bodyColor).to.equal("#fafafa");
    expect(dataset.borderColor).to.equal("#00aa00");
    expect(dataset.backgroundColor).to.equal("rgba(0, 170, 0, 0.15)");
    expect(chart.update.calledOnceWithExactly("none")).to.equal(true);
    expect(atUpdate).to.deep.equal({ line: "#00aa00", staleScaleColors: [] });
  });
});

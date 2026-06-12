import { renderLineChart } from "sumo/js/charts";
import { parseISO } from "date-fns";

document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("questions-metrics");
  if (!container) return;

  fetch(container.dataset.url)
    .then((response) => response.json())
    .then((data) => {
      const objects = data.objects
        .map((o) => ({
          date: o.date,
          questions: o.questions || 0,
          solved: o.solved || 0,
          responded_24: o.responded_24 || 0,
          responded_72: o.responded_72 || 0,
        }))
        .sort((a, b) => (a.date < b.date ? -1 : a.date > b.date ? 1 : 0));

      container.innerHTML = "";
      const wrap = document.createElement("div");
      wrap.style.position = "relative";
      wrap.style.height = "300px";
      wrap.style.width = "100%";
      const canvas = document.createElement("canvas");
      wrap.appendChild(canvas);
      container.appendChild(wrap);

      const schedule = window.requestIdleCallback || ((cb) => setTimeout(cb, 0));
      schedule(() => {
        renderLineChart(canvas, buildConfig(objects));
      });
    })
    .catch(() => {
      container.textContent = gettext("Error loading graph");
    });
});

function buildConfig(objects) {
  return {
    type: "line",
    data: {
      datasets: [
        {
          label: gettext("Questions"),
          borderColor: "#5d84b2",
          backgroundColor: "#5d84b2",
          yAxisID: "y",
          pointRadius: 0,
          borderWidth: 1.5,
          fill: true,
          data: objects.map((o) => ({ x: parseISO(o.date), y: o.questions })),
        },
        {
          label: gettext("Solved"),
          borderColor: "#aa4643",
          backgroundColor: "#aa4643",
          yAxisID: "y",
          pointRadius: 0,
          borderWidth: 1.5,
          fill: true,
          data: objects.map((o) => ({ x: parseISO(o.date), y: o.solved })),
        },
        {
          label: gettext("Responded in 24 hours"),
          borderColor: "#89a54e",
          backgroundColor: "#89a54e",
          yAxisID: "y",
          pointRadius: 0,
          borderWidth: 1.5,
          fill: true,
          data: objects.map((o) => ({ x: parseISO(o.date), y: o.responded_24 })),
        },
        {
          label: gettext("Responded in 72 hours"),
          borderColor: "#80699b",
          backgroundColor: "#80699b",
          yAxisID: "y",
          pointRadius: 0,
          borderWidth: 1.5,
          fill: true,
          data: objects.map((o) => ({ x: parseISO(o.date), y: o.responded_72 })),
        },
        {
          label: gettext("% Solved"),
          borderColor: "#aa4643",
          backgroundColor: "#aa4643",
          borderDash: [6, 4],
          yAxisID: "y1",
          pointRadius: 0,
          borderWidth: 1.5,
          fill: false,
          data: objects.map((o) => ({
            x: parseISO(o.date),
            y: o.questions > 0 ? (100 * o.solved) / o.questions : null,
          })),
        },
        {
          label: gettext("% Responded in 24 hours"),
          borderColor: "#89a54e",
          backgroundColor: "#89a54e",
          borderDash: [6, 4],
          yAxisID: "y1",
          pointRadius: 0,
          borderWidth: 1.5,
          fill: false,
          data: objects.map((o) => ({
            x: parseISO(o.date),
            y: o.questions > 0 ? (100 * o.responded_24) / o.questions : null,
          })),
        },
        {
          label: gettext("% Responded in 72 hours"),
          borderColor: "#80699b",
          backgroundColor: "#80699b",
          borderDash: [6, 4],
          yAxisID: "y1",
          pointRadius: 0,
          borderWidth: 1.5,
          fill: false,
          data: objects.map((o) => ({
            x: parseISO(o.date),
            y: o.questions > 0 ? (100 * o.responded_72) / o.questions : null,
          })),
        },
      ],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      scales: {
        x: {
          type: "time",
          time: {
            tooltipFormat: "PP",
            displayFormats: {
              day: "MMM d",
              week: "MMM d",
              month: "MMM yyyy",
              quarter: "MMM yyyy",
              year: "yyyy",
            },
          },
        },
        y: {
          position: "left",
          beginAtZero: true,
          title: {
            display: true,
            text: gettext("Questions"),
          },
        },
        y1: {
          position: "right",
          min: 0,
          max: 100,
          grid: { drawOnChartArea: false },
          title: {
            display: true,
            text: gettext("Percent"),
          },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
        },
        tooltip: {
          mode: "index",
          callbacks: {
            label: (ctx) => {
              const v = ctx.parsed.y;
              if (v == null) return null;
              const isPct = ctx.dataset.yAxisID === "y1";
              const formatted = isPct ? `${v.toFixed(1)}%` : v.toLocaleString();
              return `${ctx.dataset.label}: ${formatted}`;
            },
          },
        },
      },
    },
  };
}

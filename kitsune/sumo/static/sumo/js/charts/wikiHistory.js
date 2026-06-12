import { renderLineChart } from "sumo/js/charts";
import { parseISO } from "date-fns";

document.addEventListener("DOMContentLoaded", () => {
  const helpfulGraph = document.getElementById("helpful-graph");
  if (!helpfulGraph) return;

  fetch(helpfulGraph.dataset.url)
    .then((response) => response.json())
    .then((data) => {
      if (data.datums.length === 0) {
        helpfulGraph.textContent = gettext("No votes data");
        return;
      }

      helpfulGraph.innerHTML = "";
      const wrap = document.createElement("div");
      wrap.style.position = "relative";
      wrap.style.height = "300px";
      wrap.style.width = "100%";
      const canvas = document.createElement("canvas");
      wrap.appendChild(canvas);
      helpfulGraph.appendChild(wrap);

      const schedule = window.requestIdleCallback || ((cb) => setTimeout(cb, 0));
      schedule(() => renderLineChart(canvas, buildConfig(data.datums)));
    })
    .catch(() => {
      helpfulGraph.textContent = gettext("Error loading graph");
    });
});

function buildConfig(datums) {
  return {
    type: "line",
    data: {
      datasets: [
        {
          label: gettext("Yes"),
          borderColor: "#21de2b",
          backgroundColor: "#21de2b",
          yAxisID: "y",
          pointRadius: 0,
          data: datums.map((d) => ({ x: parseISO(d.date), y: d.yes })),
        },
        {
          label: gettext("No"),
          borderColor: "#de2b21",
          backgroundColor: "#de2b21",
          yAxisID: "y",
          pointRadius: 0,
          data: datums.map((d) => ({ x: parseISO(d.date), y: d.no })),
        },
        {
          label: gettext("% Helpful"),
          borderColor: "#2b21de",
          backgroundColor: "#2b21de",
          yAxisID: "y1",
          pointRadius: 0,
          data: datums.map((d) => ({
            x: parseISO(d.date),
            // Avoid division by zero for days with no votes
            y: d.yes + d.no > 0 ? (100 * d.yes) / (d.yes + d.no) : null,
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
            text: gettext("Votes"),
          },
        },
        y1: {
          position: "right",
          min: 0,
          max: 100,
          // Suppress grid lines on the right axis to avoid double grid rendering
          grid: { drawOnChartArea: false },
          title: {
            display: true,
            text: gettext("% Helpful"),
          },
        },
      },
      plugins: {
        legend: {
          position: "bottom",
        },
        tooltip: {
          mode: "index",
        },
      },
    },
  };
}

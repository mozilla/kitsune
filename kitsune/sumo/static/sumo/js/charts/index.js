import {
  Chart,
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Legend,
  Tooltip,
  Title,
  Filler,
  CategoryScale,
} from "chart.js";
// Side-effect import: registers the date-fns adapter with Chart.js
import "chartjs-adapter-date-fns";

Chart.register(
  LineController,
  LineElement,
  PointElement,
  LinearScale,
  TimeScale,
  Legend,
  Tooltip,
  Title,
  Filler,
  CategoryScale
);

Tooltip.positioners.cursor = function (active, eventPosition) {
  const { left, right, top, bottom } = this.chart.chartArea;
  return {
    x: Math.max(left, Math.min(eventPosition.x, right)),
    y: Math.max(top, Math.min(eventPosition.y, bottom)),
  };
};

export function renderLineChart(el, config) {
  return new Chart(el, config);
}

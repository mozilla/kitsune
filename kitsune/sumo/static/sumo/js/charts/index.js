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

export function renderLineChart(el, config) {
  return new Chart(el, config);
}

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
import { MatrixController, MatrixElement } from "chartjs-chart-matrix";

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
  CategoryScale,
  MatrixController,
  MatrixElement
);

export function renderLineChart(el, config) {
  return new Chart(el, config);
}

export function renderMatrixChart(el, config) {
  return new Chart(el, config);
}

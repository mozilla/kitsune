import Alpine from "@alpinejs/csp";
import trackEvent from "sumo/js/analytics";
// we need to import surveyForm here so it's available to Alpine components
import surveyForm from "sumo/js/survey_form";

window.Alpine = Alpine;
// Add trackEvent to the window object so it's available to Alpine components
window.trackEvent = trackEvent;

Alpine.start();

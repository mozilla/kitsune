import Alpine from 'alpinejs';
import trackEvent from "sumo/js/analytics";

window.Alpine = Alpine;
// Add trackEvent to the window object so it's available to Alpine components
window.trackEvent = trackEvent;

Alpine.start();

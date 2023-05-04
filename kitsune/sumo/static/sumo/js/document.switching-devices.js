import UITour from "./libs/uitour";
import trackEvent from "sumo/js/analytics";
import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";

$(document).ready(function() {
  new SwitchingDevicesWizardManager($("#switching-devices-wizard"))
});

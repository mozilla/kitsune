import UITour from "./libs/uitour";
import trackEvent from "sumo/js/analytics";
import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";
import "sumo/js/form-wizard";

$(document).ready(function () {
  new SwitchingDevicesWizardManager(document.querySelector("#switching-devices-wizard"));
});

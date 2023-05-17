import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";
import { BaseFormStep } from "sumo/js/form-wizard";
import { SignInStep } from "sumo/js/form-wizard-sign-in-step";
import { ConfigureStep } from "sumo/js/form-wizard-configure-step";
import { SetupDeviceStep } from "sumo/js/form-wizard-setup-device-step";

document.addEventListener("DOMContentLoaded", function () {
  new SwitchingDevicesWizardManager(
    document.querySelector("#switching-devices-wizard")
  );
  kbTabsInit();
});

// This function initializes the tabs on the switching-devices page
// and adds click event listener
function kbTabsInit() {
  const tabs = document.querySelectorAll('.tabs--link');
  const tabContents = document.querySelectorAll('.switching-devices.topic-list');

  tabs.forEach(function(tab) {
    tab.addEventListener('click', function() {
      // Remove active class from all tabs and hide all tab contents
      tabs.forEach(function(tab) {
        tab.classList.remove('is-active');
      });

      tabContents.forEach(function(content) {
        content.classList.remove('is-active');
      });
      
      // Add active class to the selected tab and show its content
      tab.classList.add('is-active');
      const targetContent = document.getElementById('tab-' + tab.getAttribute('data-event-label'));
      if (targetContent) {
        targetContent.classList.add('is-active');
      }
    })
  })};
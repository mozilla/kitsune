import trackEvent from "sumo/js/analytics";
import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";
import { BaseFormStep } from "sumo/js/form-wizard";

class SignInStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div>
          <p>This is where the sign in/sign up form will go.</p>
          <p id="email"></p>
        </div>
      </template>
    `;
  }

  render() {
    if (this.state.email) {
      let emailEl = this.shadowRoot.getElementById("email");
      emailEl.textContent = this.state.email;
    }
  }
}
customElements.define("sign-in-step", SignInStep);

class ConfigureStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div>
          <p>This is where the sync step will go.</p>
          <p id="sync-status"></p>
        </div>
      </template>
    `;
  }

  render(prevState, state) {
    if (this.state.syncEnabled !== prevState.syncEnabled) {
      let statusEl = this.shadowRoot.getElementById("sync-status");
      statusEl.textContent = this.state.syncEnabled
        ? "Syncing: ON"
        : "Syncing: OFF";
    }
  }
}
customElements.define("configure-step", ConfigureStep);
``;

class SetupDeviceStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div>
          <p>This is where the link info will go.</p>
        </div>
      </template>
    `;
  }

  render() {
    // NOOP
  }
}
customElements.define("setup-device-step", SetupDeviceStep);

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
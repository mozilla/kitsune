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

$(document).ready(function () {
  new SwitchingDevicesWizardManager(
    document.querySelector("#switching-devices-wizard")
  );
});

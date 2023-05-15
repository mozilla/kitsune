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
  let tabItems = document.querySelectorAll('.tabs--link');
  tabItems.forEach((item) => {
    item.addEventListener("click", (ev) => {
      toggleTabContent(ev);
    });
  });
}

// This function toggles the visibility of the tab content based on 
// clicked tab 
function toggleTabContent(ev) {
  // Remove the active state from the previously selected tab / tab content
  let oldSelectedTabContent = document.querySelector(".switching-devices.topic-list.is-active");
  let oldSelectedTab = document.querySelector(".tabs--link.is-active");

  oldSelectedTabContent.classList.remove("is-active");
  oldSelectedTab.classList.remove("is-active");

  // Put the newly selected tab / tab content into the active state.
  let selectedTab = ev.target.parentElement;
  let selectedTabContent = document.querySelector(`#tab-${ev.target.parentElement.dataset.eventLabel}`);

  selectedTab.classList.add("is-active");
  selectedTabContent.classList.add("is-active");
}
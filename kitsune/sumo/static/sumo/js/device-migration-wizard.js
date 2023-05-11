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
  document.getElementById("tab-view-all").style.display = "block";
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
  let tabContent = document.getElementsByClassName("topic-list");
  [].forEach.call(tabContent, (el) => {
    el.style.display = "none";
  });

  let tabItems = document.getElementsByClassName("tabs--link");
  [].forEach.call(tabItems, (item) => {
    item.classList.remove("is-active");
  });

  ev.target.parentElement.classList.add("is-active");
  document.getElementById("tab-" + ev.target.parentElement.dataset.eventLabel).style.display = "block";
}
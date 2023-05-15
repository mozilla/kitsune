import trackEvent from "sumo/js/analytics";
import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";
import { BaseFormStep } from "sumo/js/form-wizard";

import keyImageURL from "sumo/img/key.svg";

class SignInStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div id="sign-in-step-root">
          <p>
            ${gettext("Body provide short value of the account other than the bookmarks/password/history line, what else could they get out of it that would be good to know here?")}
          </p>

          <p class="for-sign-up">
            <strong>${gettext("Create an account")}</strong>
          </p>
          <p class="for-sign-in">
            <strong>${gettext("Sign in to your account")}</strong>
          </p>

          <form method="get">
            <input name="service" value="sync" type="hidden"/>
            <input name="action" value="email" type="hidden"/>
            <input name="context" value="" type="hidden"/>
            <input name="flow_id" value="" type="hidden"/>
            <input name="flow_begin_time" value="" type="hidden"/>
            <input name="utm_source" value="" type="hidden"/>
            <input name="utm_medium" value="" type="hidden"/>
            <input name="entrypoint" value="" type="hidden"/>
            <input name="redirect_immediately" value="true" type="hidden"/>
            <input name="redirect_to" value="" type="hidden"/>

            <label for="email">${gettext("Email")}</label>
            <input id="email" name="email" type="email" required="true" placeholder="${gettext("Enter your email")}"/>

            <button class="for-sign-up" type="submit" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="signup-button">${gettext("Sign up")}</button>
            <button class="for-sign-in" type="submit" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="sign-in-button">${gettext("Sign in")}</button>
          </form>

          <p class="for-sign-up">
            ${gettext("Already have an account?")} <a class='alternative-link' href='#' data-event-category="device-migration-wizard" data-event-action="click" data-event-label="sign-in-link">${gettext("Sign in")}</a>
          </p>
          <p class="for-sign-in">
            ${gettext("Don’t have an account?")} <a class='alternative-link' href='#' data-event-category="device-migration-wizard" data-event-action="click" data-event-label="signup-link">${gettext("Sign up")}</a>
          </p>

          <p class="warning">
            <img class="key-icon" src="${keyImageURL}" aria-hidden="true"></img>
            ${gettext("Provide any warnings about unexpected password situations (like noted in mock)")}
          </p>
        </div>
      </template>
    `;
  }

  get styles() {
    let style = document.createElement("style");
    style.textContent = `
      #sign-in-step-root[mode="sign-in"] .for-sign-up,
      #sign-in-step-root[mode="sign-up"] .for-sign-in {
        display: none;
      }

      .key-icon {
        width: 16px;
        height: 8px;
      }
    `;
    return style;
  }

  render() {
    let root = this.shadowRoot.querySelector("#sign-in-step-root");

    if (this.state.email) {
      let emailEl = this.shadowRoot.querySelector("#email");
      // If the user somehow has managed to type something into the email
      // field before we were able to get the email address, let's not
      // overwrite what the user had typed in.
      if (!emailEl.value) {
        emailEl.value = this.state.email;
      }
      root.setAttribute("mode", "sign-in");
    } else {
      root.setAttribute("mode", "sign-up");
    }

    let form = this.shadowRoot.querySelector("form");
    form.action = this.state.fxaRoot;

    const STATE_FIELDS = [
      "context",
      "flow_id",
      "flow_begin_time",
      "utm_source",
      "utm_medium",
      "entrypoint",
      "redirect_to",
    ];

    for (let fieldName of STATE_FIELDS) {
      let fieldEl = this.shadowRoot.querySelector(`input[name=${fieldName}]`);
      if (this.state[fieldName]) {
        fieldEl.disabled = false;
        fieldEl.value = this.state[fieldName];
      } else {
        fieldEl.disabled = true;
      }
    }

    let alternativeLinks = this.shadowRoot.querySelectorAll(".alternative-link");
    for (let link of alternativeLinks) {
      link.href = this.state.linkHref;
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

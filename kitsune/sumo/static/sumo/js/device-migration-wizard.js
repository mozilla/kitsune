import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";
import { BaseFormStep } from "sumo/js/form-wizard";

import keyImageURL from "sumo/img/key.svg";
import infoImageURL from "sumo/img/info.svg";
import syncingImageURL from "sumo/img/syncing.svg";

import signInStepStylesURL from "../scss/form-wizard-sign-in-step.styles.scss";
import configurationStepStylesURL from "../scss/form-wizard-configuration-step.styles.scss";

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
            <input name="redirect_immediately" value="" type="hidden"/>
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
    let linkEl = document.createElement("link");
    linkEl.rel = "stylesheet";
    linkEl.href = signInStepStylesURL;
    return linkEl;
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
      "redirect_immediately",
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
          <p id="header">
            <img class="icon" src="${infoImageURL}" aria-hidden="true"></img>
            <span>${gettext("You are now logged in to Firefox Accounts")}</span>
            <a href="#" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="forgot-password">${gettext("Forgot password?")}</a>
          </p>
          <p id="sync-status-container">
            <img class="icon" src="${syncingImageURL}" aria-hidden="true"></img>
            <span><strong>${gettext("Syncing:")}</strong></span>
            <span id="sync-status"></span>
          </p>
          <ul id="instructions">
            <li>${gettext("We may not need to say that it’s “off” at the beginning, but rather a “get set up” - type of introduction")}</li>
            <li>${gettext("Make sure there ‘s context for how it works - ex/ timing, frequency, limitations")}</li>
            <li>${gettext("set expectations we sync all data across all devices - can’t pick and choose")}</li>
          </ul>
          <p id="buttons">
            <button id="turn-on-sync" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="turn-on-sync">${gettext("Turn on sync")}</button>
            <button id="change-sync-prefs" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="change-sync-prefs">${gettext("Change what you are syncing")}</button>
            <button id="next" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="configuration-next">${gettext("Next")}</button>
          </p>
        </div>
      </template>
    `;
  }

  get styles() {
    let linkEl = document.createElement("link");
    linkEl.rel = "stylesheet";
    linkEl.href = configurationStepStylesURL;
    return linkEl;
  }

  connectedCallback() {
    let buttons = this.shadowRoot.querySelector("#buttons");
    buttons.addEventListener("click", this);
  }

  disconnectedCallback() {
    let buttons = this.shadowRoot.querySelector("#buttons");
    buttons.removeEventListener("click", this);
  }

  render(prevState, state) {
    if (this.state.syncEnabled !== prevState.syncEnabled) {
      let statusEl = this.shadowRoot.getElementById("sync-status");
      statusEl.textContent = this.state.syncEnabled
        ? gettext("On")
        : gettext("Off");
      statusEl.toggleAttribute("sync-enabled", this.state.syncEnabled);

      let buttons = this.shadowRoot.getElementById("buttons");
      buttons.toggleAttribute("sync-enabled", this.state.syncEnabled);
    }
  }

  handleEvent(event) {
    switch (event.target.id) {
      case "turn-on-sync": {
        this.dispatch("DeviceMigrationWizard:ConfigureStep:TurnOnSync");
        break;
      }
      case "change-sync-prefs": {
        this.dispatch("DeviceMigrationWizard:ConfigureStep:ChangeSyncPrefs");
        break;
      }
      case "next": {
        this.dispatch("DeviceMigrationWizard:ConfigureStep:Next");
        break;
      }
    }
  }

  dispatch(eventName) {
    let event = new CustomEvent(eventName, { bubbles: true });
    this.dispatchEvent(event);
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
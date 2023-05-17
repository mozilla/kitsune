import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";
import { BaseFormStep } from "sumo/js/form-wizard";
import { ConfigureStep } from "sumo/js/form-wizard-configure-step";

import keyImageURL from "sumo/img/key.svg";

import signInStepStylesURL from "../scss/form-wizard-sign-in-step.styles.scss";

class SignInStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div id="sign-in-step-root">
          <p>
            ${gettext("Body provide short value of the account other than the bookmarks/password/history line, what else could they get out of it that would be good to know here?")}
          </p>

          <p class="for-sign-up form-title">
            <strong>${gettext("Create an account")}</strong>
          </p>
          <p class="for-sign-in form-title">
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

            <button class="for-sign-up mzp-c-button mzp-t-product" type="submit" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="signup-button">${gettext("Sign up")}</button>
            <button class="for-sign-in mzp-c-button mzp-t-product" type="submit" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="sign-in-button">${gettext("Sign in")}</button>
          </form>

          <p class="for-sign-up form-footer">
            ${gettext("Already have an account?")} <a class='alternative-link' href='#' data-event-category="device-migration-wizard" data-event-action="click" data-event-label="sign-in-link">${gettext("Sign in")}</a>
          </p>
          <p class="for-sign-in form-footer">
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
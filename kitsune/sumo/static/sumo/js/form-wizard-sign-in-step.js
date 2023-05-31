import { BaseFormStep } from "sumo/js/form-wizard";

import keyImageURL from "sumo/img/key.svg";
import signInStepStylesURL from "../scss/form-wizard-sign-in-step.styles.scss";

export class SignInStep extends BaseFormStep {
  #formEl = null;
  #emailEl = null;
  #emailErrorEl = null;

  get template() {
    return `
      <template>
        <div id="sign-in-step-root">
          <h3 class="for-sign-up">${gettext("Create an account")}</h3>
          <h3 class="for-sign-in">${gettext("Sign in to your account")}</h3>

          <p class="for-sign-up">
            ${gettext("With an account, your data remains encrypted and protected, while also giving you access to other Mozilla products and services like Firefox Relay and Pocket.")}
          </p>

          <p class="for-sign-in">
            ${gettext("A Firefox account allows you to securely sync your data when signing in from other devices and gives access to other fantastic Mozilla services.")}
          </p>

          <form method="get" novalidate>
            <input name="service" value="" type="hidden"/>
            <input name="action" value="" type="hidden"/>
            <input name="context" value="" type="hidden"/>
            <input name="flow_id" value="" type="hidden"/>
            <input name="flow_begin_time" value="" type="hidden"/>
            <input name="utm_source" value="" type="hidden"/>
            <input name="utm_medium" value="" type="hidden"/>
            <input name="utm_campaign" value="" type="hidden"/>
            <input name="entrypoint" value="" type="hidden"/>
            <input name="entrypoint_experiment" value="" type="hidden"/>
            <input name="entrypoint_variation" value="" type="hidden"/>
            <input name="redirect_immediately" value="" type="hidden"/>
            <input name="redirect_to" value="" type="hidden"/>

            <label for="email">${gettext("Email")}</label>
            <div class="tooltip-container">
              <aside id="email-error" class="tooltip">${gettext("Valid email required")}</aside>
              <input id="email" name="email" type="email" required="true" placeholder="${gettext("Enter your email address")}"/>
            </div>

            <button class="for-sign-up mzp-c-button mzp-t-product" type="submit" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="signup-button">${gettext("Sign up")}</button>
            <button class="for-sign-in mzp-c-button mzp-t-product" type="submit" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="sign-in-button">${gettext("Sign in")}</button>
          </form>

          <p class="for-sign-up form-footer">
            ${gettext("Already have an account?")} <a class='alternative-link' href='#' data-event-category="device-migration-wizard" data-event-action="click" data-event-label="sign-in-link">${gettext("Sign in")}</a>
          </p>
          <p class="for-sign-in form-footer">
            ${gettext("Don’t have an account?")} <a class='alternative-link' href='#' data-event-category="device-migration-wizard" data-event-action="click" data-event-label="signup-link">${gettext("Sign up")}</a>
          </p>

          <p class="warning for-sign-up">
            <img class="key-icon" src="${keyImageURL}" aria-hidden="true"></img>
            <span><strong>${gettext("Important:")}</strong> ${gettext("Make sure to create a recovery key in case you need to reset your password. For security purposes, Firefox is only able to keep synced data if a recovery key is set up.")}</span>
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

  connectedCallback() {
    super.connectedCallback();
    this.#formEl = this.shadowRoot.querySelector("form");
    this.#emailEl = this.shadowRoot.getElementById("email");
    this.#emailErrorEl = this.shadowRoot.getElementById("email-error");

    this.#formEl.addEventListener("submit", this);
    this.#emailEl.addEventListener("blur", this);
    this.#emailEl.addEventListener("input", this);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.#formEl.removeEventListener("submit", this);
    this.#emailEl.removeEventListener("blur", this);
    this.#emailEl.removeEventListener("input", this);
  }

  handleEvent(event) {
    switch (event.type) {
      case "blur": {
        if (!this.#emailEl.validity.valid) {
          this.#emailErrorEl.classList.add("visible");
        }
        break;
      }
      case "input": {
        if (this.#emailEl.value?.trim()) {
          this.#emailErrorEl.classList.remove("visible");
        }
        break;
      }
      case "submit": {
        if (!this.#emailEl.validity.valid) {
          this.#emailErrorEl.classList.add("visible");
          event.preventDefault();
        }
        break;
      }
    }
  }

  render() {
    let root = this.shadowRoot.querySelector("#sign-in-step-root");

    if (this.state.email) {
      // If the user somehow has managed to type something into the email
      // field before we were able to get the email address, let's not
      // overwrite what the user had typed in.
      if (!this.#emailEl.value) {
        this.#emailEl.value = this.state.email;
      }
      root.setAttribute("mode", "sign-in");
    } else {
      root.setAttribute("mode", "sign-up");
    }

    let form = this.shadowRoot.querySelector("form");
    form.action = this.state.fxaRoot;

    const STATE_FIELDS = [
      "service",
      "action",
      "context",
      "flow_id",
      "flow_begin_time",
      "utm_source",
      "utm_medium",
      "utm_campaign",
      "entrypoint",
      "entrypoint_experiment",
      "entrypoint_variation",
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

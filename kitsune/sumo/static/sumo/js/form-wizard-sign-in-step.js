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
          <p>
            ${gettext("Body provide short value of the account other than the bookmarks/password/history line, what else could they get out of it that would be good to know here?")}
          </p>

          <p class="for-sign-up form-title">
            <strong>${gettext("Create an account")}</strong>
          </p>
          <p class="for-sign-in form-title">
            <strong>${gettext("Sign in to your account")}</strong>
          </p>

          <form method="get" novalidate>
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
            <div class="tooltip-container">
              <aside id="email-error" class="error-tooltip hidden">${gettext("Valid email required")}</aside>
              <input id="email" name="email" type="email" required="true" placeholder="${gettext("Enter your email")}"/>
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

  connectedCallback() {
    this.#formEl = this.shadowRoot.querySelector("form");
    this.#emailEl = this.shadowRoot.getElementById("email");
    this.#emailErrorEl = this.shadowRoot.getElementById("email-error");

    this.#formEl.addEventListener("submit", this);
    this.#emailEl.addEventListener("blur", this);
    this.#emailEl.addEventListener("input", this);
  }

  disconnectedCallback() {
    this.#formEl.removeEventListener("submit", this);
    this.#emailEl.removeEventListener("blur", this);
    this.#emailEl.removeEventListener("input", this);
  }

  handleEvent(event) {
    switch (event.type) {
      case "blur": {
        if (!this.#emailEl.validity.valid) {
          this.#emailErrorEl.classList.remove("hidden");
        }
        break;
      }
      case "input": {
        if (this.#emailEl.value?.trim()) {
          this.#emailErrorEl.classList.add("hidden");
        }
        break;
      }
      case "submit": {
        if (!this.#emailEl.validity.valid) {
          this.#emailErrorEl.classList.remove("hidden");
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

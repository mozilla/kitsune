import { BaseFormStep } from "sumo/js/form-wizard";

import signInStepStylesURL from "../scss/form-wizard-sign-in-step.styles.scss";

export class SignInStep extends BaseFormStep {
  #formEl = null;
  #emailEl = null;
  #emailErrorEl = null;

  get template() {
    return `
      <template>
        <div id="sign-in-step-root">
          <h3 class="for-sign-up">${gettext("Sign up for an account")}</h3>
          <h3 class="for-sign-in">${gettext("Sign in to your account")}</h3>

          <p>
            ${gettext("You’ll be able to sign in to this account on another device to sync your data.")}
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

            <label for="email">${gettext("Enter your email")}</label>
            <div class="tooltip-container">
              <aside id="email-error" class="tooltip">${gettext("Valid email required")}</aside>
              <input id="email" name="email" type="email" required="true" placeholder="${gettext("user@example.com")}"/>
            </div>

            <button id="continue" class="mzp-c-button mzp-t-product" type="submit" data-event-category="device-migration-wizard" data-event-action="click">${gettext("Continue")}</button>
          </form>

          <p class="for-sign-up form-footer">
            ${gettext("Already have an account?")} <a class='alternative-link' href='#' data-event-category="device-migration-wizard" data-event-action="click" data-event-label="sign-in-link">${gettext("Sign in")}</a>
          </p>
          <p class="for-sign-in form-footer">
            ${gettext("Don’t have an account?")} <a class='alternative-link' href='#' data-event-category="device-migration-wizard" data-event-action="click" data-event-label="signup-link">${gettext("Sign up")}</a>
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
    this.#emailEl.focus();
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    this.#formEl.removeEventListener("submit", this);
    this.#emailEl.removeEventListener("blur", this);
    this.#emailEl.removeEventListener("input", this);
  }

  deactivate() {
    if (this.shadowRoot.activeElement == this.#emailEl) {
      this.#emailEl.blur();
      this.#emailErrorEl.classList.remove("visible");
    }
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
        } else {
          // The email is valid and we're about to redirect to FxA login.
          // Let's quickly stash the email address in session storage so
          // that we can prefill the email field in Step 3 for getting
          // the reminder email.
          try {
            sessionStorage.setItem("switching-devices-email", this.#emailEl.value);
          } catch (e) {
            // We wrap this in a try/catch because session storage methods might
            // throw if the user has disabled cookies or other types of site
            // data storage, and we want this to be non-fatal.
          }
        }
        break;
      }
    }
  }

  render() {
    let root = this.shadowRoot.querySelector("#sign-in-step-root");
    let continueBtn = this.shadowRoot.querySelector("#continue");

    if (this.state.email) {
      // If the user somehow has managed to type something into the email
      // field before we were able to get the email address, let's not
      // overwrite what the user had typed in.
      if (!this.#emailEl.value) {
        this.#emailEl.value = this.state.email;
      }
      root.setAttribute("mode", "sign-in");
      continueBtn.dataset.eventLabel = "sign-in-button";
    } else {
      root.setAttribute("mode", "sign-up");
      continueBtn.dataset.eventLabel = "signup-button";
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

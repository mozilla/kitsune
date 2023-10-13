import trackEvent from "sumo/js/analytics";
import { BaseFormStep } from "sumo/js/form-wizard";
import { ReminderDialog } from "sumo/js/form-wizard-reminder-dialog"
import setupDeviceStepStyles from "../scss/form-wizard-setup-device-step.styles.scss";
import successIconUrl from "sumo/img/success-white.svg";

const ERROR_TYPES = Object.freeze({
  INVALID_EMAIL: "invalid-email",
  OTHER: "other",
});

export class SetupDeviceStep extends BaseFormStep {
  #reminderDialog = null;
  #formEl = null;
  #emailEl = null;
  #emailErrorEl = null;
  #submitButton = null;

  get template() {
    return `
      <template>
        <div id="setup-device-root">
          <h3>${gettext("Download Firefox on your new device")}</h3>
          <ul>
            <li>${gettext("To finish the back-up, you’ll need to install Firefox and sign in to your account. Find it in your app store or send a download link to your email.")}</li>
          </ul>
          <div class="email-calendar-wrapper">
            <form id="email-reminder-form" action="https://basket.mozilla.org/news/subscribe/" method="POST" novalidate="">
              <input type="hidden" name="newsletters" value="download-firefox-desktop-migration">
              <input type="hidden" name="source-url" value="${window.location.href}">
              <input type="hidden" name="lang" value="${navigator.language}">

              <label for="email">${gettext("Enter your email address")}</label>
              <div class="tooltip-container">
                <aside id="email-error" class="tooltip">
                  <span class="invalid-email error">${gettext("Invalid email address")}</span>
                  <span class="other error">${gettext("An error occurred in our system. Please try again later.")}</span>
                </aside>
                <input id="email" name="email" type="email" required="true" placeholder="${gettext("example@example.com")}"/>
                <button id="submit" type="submit" class="mzp-c-button mzp-t-product mzp-t-lg" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="send-email-reminder" disabled="">
                  <span class="not-success">${gettext("Send link")}</span>
                  <img class="success" src="${successIconUrl}" aria-hidden="true"/>
                  <span class="success">${gettext("Sent")}</span>
                </button>
              </div>
              <div id="email-consent-message">${interpolate(
                gettext("The intended recipient of the email must have consented. <a href='%s'>Learn more</a>"),
                ["https://www.mozilla.org/en-US/privacy/websites/#campaigns"]
              )}</div>
            </form>
            <button id="open-reminder-dialog-button" class="mzp-c-button mzp-t-product mzp-t-secondary" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="open-reminder-dialog">${gettext("Add to calendar")}</button>
          </div>
        </div>
      </template>
    `;
  }

  get styles() {
    let linkEl = document.createElement("link");
    linkEl.rel = "stylesheet";
    linkEl.href = setupDeviceStepStyles;
    return linkEl;
  }

  constructor() {
    super();
  }

  connectedCallback() {
    super.connectedCallback();
    let reminderDialogButton = this.shadowRoot.getElementById("open-reminder-dialog-button");
    reminderDialogButton.addEventListener("click", this);

    this.#formEl = this.shadowRoot.getElementById("email-reminder-form");
    this.#emailEl = this.shadowRoot.getElementById("email");
    this.#emailErrorEl = this.shadowRoot.getElementById("email-error");

    this.#formEl.addEventListener("submit", this);
    this.#emailEl.addEventListener("blur", this);
    this.#emailEl.addEventListener("input", this);
    this.#submitButton = this.shadowRoot.getElementById("submit");
  }

  handleEvent(event) {
    switch (event.type) {
      case "click": {
        this.#onClick(event);
        break;
      }
      case "blur": {
        if (!this.#emailEl.validity.valid) {
          this.#showError(ERROR_TYPES.INVALID_EMAIL);
        }
        break;
      }
      case "input": {
        if (this.#emailEl.value?.trim()) {
          this.#hideError();
        }

        this.#submitButton.toggleAttribute("success", false);
        this.#submitButton.disabled = !this.#emailEl.validity.valid;
        break;
      }
      case "submit": {
        if (!this.#emailEl.validity.valid) {
          this.#showError(ERROR_TYPES.INVALID_EMAIL);
          event.preventDefault();
          return;
        }

        event.preventDefault();
        this.#submitEmail();

        break;
      }
    }
  }

  #onClick(event) {
    if (event.target.id == "open-reminder-dialog-button") {
      this.#hideError();
      this.openReminderDialog();
    }
  }

  /**
   * Submits the provided email to Basket to subscribe the user to a one-time
   * newsletter that gives them a link to download Firefox on their new device.
   */
  async #submitEmail() {
    trackEvent(
      "device-migration-wizard",
      "submit",
      "reminder-email"
    );

    let params = new URLSearchParams();
    for (let element of this.#formEl.elements) {
      // Since the button is inside of the <form> element, it'll get included as one
      // of the form elements, but it's of no value to the request we're sending.
      if (element.id != "submit") {
        params.set(element.name, element.value);
      }
    }


    let response;
    let responseBody;

    try {
      response = await fetch(this.#formEl.action, {
        method: this.#formEl.method,
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
        body: params,
      });
      responseBody = await response.json();
    } catch (e) {
      this.#showError(ERROR_TYPES.OTHER);
      return;
    }

    if (response.status >= 200 &&
        response.status < 300 &&
        responseBody.status == "ok") {
      this.#submitButton.toggleAttribute("success", true);
      this.#submitButton.disabled = true;
      trackEvent(
        "device-migration-wizard",
        "success",
        "reminder-email"
      );
    } else {
      this.#showError(ERROR_TYPES.OTHER);

      if (responseBody.status) {
        trackEvent(
          "device-migration-wizard",
          "error",
          "reminder-email",
          responseBody.status
        );
      } else {
        trackEvent(
          "device-migration-wizard",
          "error",
          "reminder-email",
          response.status
        );
      }
    }
  }

  #showError(errorType) {
    this.#emailErrorEl.setAttribute("error-type", errorType);
    this.#emailErrorEl.classList.add("visible");
  }

  #hideError() {
    this.#emailErrorEl.classList.remove("visible");
  }

  /**
   * Opens the dialog to create calendar events to remind the user
   * to download and install Firefox in the future.
   *
   * This is currently a public method to facilitate easier manual
   * testing, as the step that will eventually present a button for
   * opening the dialog isn't ready yet.
   */
  openReminderDialog() {
    if (!this.#reminderDialog) {
      let dialog = new ReminderDialog();
      dialog.classList.add("reminder-dialog");
      document.body.appendChild(dialog);

      this.#reminderDialog = dialog;
    }

    this.#reminderDialog.showModal();
  }
}
customElements.define("setup-device-step", SetupDeviceStep);

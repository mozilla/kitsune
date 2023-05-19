import { BaseFormStep } from "sumo/js/form-wizard";
import infoImageURL from "sumo/img/info.svg";
import syncingImageURL from "sumo/img/syncing.svg";
import configureStepStylesURL from "../scss/form-wizard-configure-step.styles.scss";

export class ConfigureStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div class="configure-step-wrapper">
          <p id="header">
            <img class="icon" src="${infoImageURL}" aria-hidden="true"></img>
            <span>${gettext("You’re now logged in to your Firefox account.")}</span>
            <a id="forgot-password" href="#" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="forgot-password">${gettext("Forgot password?")}</a>
          </p>
          <p id="sync-status-container">
            <img class="icon" src="${syncingImageURL}" aria-hidden="true"></img>
            <span><strong>${gettext("Syncing:")}</strong></span>
            <span id="sync-status"></span>
          </p>
          <ul id="instructions">
            <li class="not-syncing">${gettext("Turn on sync to access your bookmarks, add-ons, browsing history and more.")}</li>
            <li class="not-syncing">${gettext("When you sign in using the Firefox browser, you’ll access all your synced tabs on the devices you sign in with your Firefox account.")}</li>
            <li class="not-syncing">${gettext("Syncing your data may take a few minutes.")}</li>

            <li class="syncing">${gettext("Choose the data you want to sync, including bookmarks, history, passwords and more,  for seamless access on other devices where you sign in with your Firefox account.")}</li>
          </ul>
          <p id="buttons">
            <button id="turn-on-sync" class="mzp-c-button mzp-t-product" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="turn-on-sync">${gettext("Turn on sync")}</button>
            <button id="change-sync-prefs" class="mzp-c-button" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="change-sync-prefs">${gettext("Change sync options")}</button>
            <button id="next" class="mzp-c-button mzp-t-product" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="configuration-next">${gettext("Next")}</button>
          </p>
        </div>
      </template>
    `;
  }

  get styles() {
    let linkEl = document.createElement("link");
    linkEl.rel = "stylesheet";
    linkEl.href = configureStepStylesURL;
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
      let nextButton = this.shadowRoot.getElementById("next");
      nextButton.disabled = !this.state.syncEnabled;
      let instructions = this.shadowRoot.getElementById("instructions");
      instructions.toggleAttribute("sync-enabled", this.state.syncEnabled);
    }

    if (this.state.forgotPasswordLinkHref !== prevState.forgotPasswordLinkHref) {
      let linkEl = this.shadowRoot.querySelector("#forgot-password");
      linkEl.href = this.state.forgotPasswordLinkHref;
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


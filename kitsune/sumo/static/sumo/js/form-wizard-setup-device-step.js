import { BaseFormStep } from "sumo/js/form-wizard";
import setupDeviceStepStyles from "../scss/form-wizard-setup-device-step.styles.scss";
import copyIconUrl from "protocol/img/icons/copy.svg"

export class SetupDeviceStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div>
          <h3>${gettext("Congratulatory headline they’ve done all they need to do on THIS device")}</h3>
          <ul>
            <li>${gettext("Let user know this is the point in the flow they will need to access their new device - if they don’t have it yet, that’s okay but.. (give next step - come back here when __ , do ___ until")}</li>
          </ul>
          <div class="download-link-wrapper">
            <a id="download-link" href="https://mzl.la/newdevice" target="_blank">https://mzl.la/newdevice</a>
            <div class="tooltip-container">
              <button id="copy-button" aria-label=${gettext("Copy to clipboard")}>
                <img src=${copyIconUrl} aria-hidden="true"></img>
              </button>
              <aside id="copy-message" class="tooltip tooltip-right">${gettext("Copy to clipboard")}</aside>
            </div>
          </div>
          <ul>
            <li>${gettext("if they do have their device here’s how they can get it")}</li>
            <li>${gettext("Try to let user know where the link goes so they don’t have to click it to understand it’s an app download - maybe in language, maybe we can do this visually?")}</li>
          </ul>
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
    this.copyLink = this.copyLink.bind(this);
  }

  connectedCallback() {
    let copyButton = this.shadowRoot.getElementById("copy-button");
    copyButton.addEventListener("click", this.copyLink);
  }

  disconnectedCallback() {
    let copyButton = this.shadowRoot.getElementById("copy-button");
    copyButton.removeEventListener("click", this.copyLink);
  }

  copyLink() {
    let downloadLink = this.shadowRoot.getElementById("download-link");
    navigator.clipboard.writeText(downloadLink.href);
  }

  render() {
    // NOOP
  }
}
customElements.define("setup-device-step", SetupDeviceStep);

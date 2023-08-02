import { BaseFormStep } from "sumo/js/form-wizard";
import setupDeviceStepStyles from "../scss/form-wizard-setup-device-step.styles.scss";
import successIconUrl from "sumo/img/success.svg";

export class SetupDeviceStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div id="setup-device-root">
          <h3>${gettext("Start browsing!")}</h3>
          <ul>
            <li>${gettext("Enter this URL directly into the address bar on your new device to start the Firefox download, or keep it somewhere safe for when you’re ready to continue.")}</li>
          </ul>
          <div class="download-link-wrapper">
            <a id="download-link" href="https://mzl.la/newdevice" target="_blank">https://mzl.la/newdevice</a>
            <button id="copy-button" class="mzp-c-button mzp-t-md button-secondary" data-event-category="device-migration-wizard" data-event-action="click" data-event-label="copy-link-to-clipboard-button">${gettext("Copy")}</button>
            <span id="copied-message"><img src="${successIconUrl}" aria-hidden="true">${gettext("Copied!")}</span>
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
    this.copyLink = this.copyLink.bind(this);
  }

  connectedCallback() {
    super.connectedCallback();
    let copyButton = this.shadowRoot.getElementById("copy-button");
    copyButton.addEventListener("click", this.copyLink);
  }

  disconnectedCallback() {
    super.disconnectedCallback();
    let copyButton = this.shadowRoot.getElementById("copy-button");
    copyButton.removeEventListener("click", this.copyLink);
  }

  copyLink() {
    let root = this.shadowRoot.getElementById("setup-device-root");
    let downloadLink = this.shadowRoot.getElementById("download-link");
    navigator.clipboard.writeText(downloadLink.href);
    root.toggleAttribute("data-copied", true);
    setTimeout(() => {
      root.toggleAttribute("data-copied", false);
    }, 5000);
  }
}
customElements.define("setup-device-step", SetupDeviceStep);

import { BaseFormStep } from "sumo/js/form-wizard";
import setupDeviceStepStyles from "../scss/form-wizard-setup-device-step.styles.scss";
import copyIconUrl from "protocol/img/icons/copy.svg"

export class SetupDeviceStep extends BaseFormStep {
  get template() {
    return `
      <template>
        <div>
          <h3>${gettext("You’re all set on this device!")}</h3>
          <ul>
            <li>${gettext("To continue with the download and sync process on your new device, click the copy-paste button and save the link in a place that you will remember, such as a note-taking app or send it to your email. When you're on your new device, simply paste the download link into the default browser of your new device to download Firefox and we'll be there to assist you with the next steps.")}</li>
            <li>${gettext("You can save the link to this article in a convenient location, and we'll be here to help you pick up where you left off whenever you're ready.")}</li>
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
}
customElements.define("setup-device-step", SetupDeviceStep);

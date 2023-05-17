import { BaseFormStep } from "sumo/js/form-wizard";

export class SetupDeviceStep extends BaseFormStep {
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

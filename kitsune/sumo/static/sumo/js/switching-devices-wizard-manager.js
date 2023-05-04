/**
 * This class is responsible for managing the state for a wizard that
 * guides a user through setting up a Firefox Account for the purposes
 * of migrating their data to a new device that they're switching to.
 *
 * This class will ingest events and callbacks, update its internal state,
 * and then call into a <form-wizard> customElement to represent that state.
 */
export default class SwitchingDevicesWizardManager {
  #formWizard = null;
  #state = {};

  constructor(formWizard) {
    this.#formWizard = formWizard;
  }
}

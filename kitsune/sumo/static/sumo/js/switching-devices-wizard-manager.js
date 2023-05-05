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
  #fxaRoot = null;
  #state = {
    // These UTM parameters are fallback values in the event that we
    // don't get any passed through to us from the entrypoint to this
    // SUMO page. These are what will ultimately get passed through the
    // FxA sign-in flow.
    utm_source: "support.mozilla.org",
    utm_campaign: "migration",
    utm_medium: "mozilla-websites",

    entrypoint: "fx-new-device-sync",
    entrypoint_experiment: null,
    entrypoint_variation: null,
    flow_id: null,
    flow_begin_time: null,
    context: null,
  };

  constructor(formWizard) {
    this.#formWizard = formWizard;

    if (!this.#formWizard.hasAttribute("fxa-root")) {
      throw new Error(
        "Expected fxa-root on element passed to " +
          "SwitchingDevicesWizardManager constructor."
      );
    }
    this.#fxaRoot = this.#formWizard.getAttribute("fxa-root");

    // If the page was loaded with any UTM or entrypoint parameters, we'll want
    // to pass those along, so now we check for those and add them to our state
    // if need be. Since this occurs during construction, we don't need to call
    // #updateState().
    let searchParams = new URLSearchParams(window.location.search);

    for (let paramName of [
      "utm_source",
      "utm_campaign",
      "utm_medium",
      "entrypoint",
      "entrypoint_experiment",
      "entrypoint_variation",
    ]) {
      if (searchParams.has(paramName)) {
        this.#state[paramName] = searchParams.get(paramName);
      }
    }

    // We need to get some query parameters from the FxA server before we
    // show the user any kind of form to create or sign-in to an account.
    // See https://mozilla.github.io/ecosystem-platform/relying-parties/reference/metrics-for-relying-parties#relying-party-hosted-email-form.
    this.#requestMetricsParams();
  }

  /**
   * Returns a fresh copy of the internal state object. This is mainly
   * for testing.
   *
   * @type {object}
   */
  get state() {
    return Object.assign({}, this.#state);
  }

  /**
   * Updates the internal state object by applying the changes from
   * stateDiff to a copy of the existing state, and then setting that
   * copy as the new state.
   *
   * @param {object} stateDiff
   *   Changes to make to the internal state. This uses the same patching
   *   mechanism as when using `Object.assign`.
   */
  #updateState(stateDiff) {
    this.#state = Object.assign(this.#state, stateDiff);
  }

  /**
   * Makes contact with the FxA endpoint pointed at by #fxaRoot/metrics-flow to
   * get the flow_id and flow_begin_time parameters. Once those parameters are
   * returned, this triggers a state update.
   *
   * @returns {Promise<undefined>}
   */
  async #requestMetricsParams() {
    let params = new URLSearchParams();
    for (let paramName of [
      "utm_source",
      "utm_campaign",
      "entrypoint",
      "entrypoint_variation",
      "entrypoint_experiment",
    ]) {
      if (this.#state[paramName]) {
        params.set(paramName, this.#state[paramName]);
      }
    }
    let response = await window.fetch(
      `${this.#fxaRoot}/metrics-flow?${params}`
    );

    if (response.status == 200) {
      let { flowId, flowBeginTime } = await response.json();

      let stateDiff = {
        flow_id: flowId,
        flow_begin_time: flowBeginTime,
      };
      this.#updateState(stateDiff);
    }
  }
}

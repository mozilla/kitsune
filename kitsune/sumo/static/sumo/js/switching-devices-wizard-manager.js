import BrowserDetect from "./browserdetect";

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

  // Some of these #state properties use snake_case since there are some
  // properties that are going to be sent as queryParameters, and this
  // lets us not worry about translating them from camelCase to snake_case.
  //
  // It does mean there's some inconsistency in the casing, but it's
  // intentional.
  #defaultState = {
    // These UTM parameters are fallback values in the event that we
    // don't get any passed through to us from the entrypoint to this
    // SUMO page. These are what will ultimately get passed through the
    // FxA sign-in flow.
    utm_source: "support.mozilla.org",
    utm_campaign: "migration",
    utm_medium: "mozilla-websites",

    // These are the other parameters that are sent through the FxA sign-in
    // flow.
    entrypoint: "fx-new-device-sync",
    entrypoint_experiment: null,
    entrypoint_variation: null,
    flow_id: null,
    flow_begin_time: null,
    context: null,

    // The rest of these are internal state variables used by this class
    // to determine which step to show the user in the <form-wizard>.
    fxaRoot: null,
    fxaSignedIn: false,
    sumoEmail: "",
    syncEnabled: false,
    confirmedSyncChoices: false,
  };

  #state = Object.assign({}, this.#defaultState);

  /**
   * @typedef {object} SwitchingDevicesWizardStep
   * @property {string} name
   *   The name of the step to pass to <form-wizard>.setStep if this
   *   SwitchingDevicesWizardStep is the one we're entering.
   * @property {function} exitConditionsMet
   *   A function that accepts the state object from
   *   SwitchingDevicesWizardManager. Returns true the
   *   SwitchingDevicesWizardStep can be skipped over because the
   *   conditions for completing it are met.
   * @property {function} enter
   *   A function that accepts the state object from
   *   SwitchingDevicesWizardManager. Returns another object that
   *   is passed to the <form-wizard>.setStep method as the payload
   *   for configuring the displayed step.
   */

  // An array of SwitchingDevicesWizardSteps that are evaluated during each
  // state change to determine which step we should put the user in with the
  // <form-wizard>. This is intentionally public so that the steps can be
  // unit tested individually.
  steps = Object.freeze([
    {
      name: "sign-into-fxa",
      exitConditionsMet(state) {
        return state.fxaSignedIn;
      },
      enter(state) {
        return {
          fxaRoot: state.fxaRoot,
          email: state.sumoEmail,

          utm_source: state.utm_source,
          utm_campaign: state.utm_campaign,
          utm_medium: state.utm_medium,
          entrypoint: state.entrypoint,
          entrypoint_experiment: state.entrypoint_experiment,
          entrypoint_variation: state.entrypoint_variation,
          flow_id: state.flow_id,
          flow_begin_time: state.flow_begin_time,
          context: state.context,
        };
      },
    },
    {
      name: "configure-sync",
      exitConditionsMet(state) {
        return state.syncEnabled && state.confirmedSyncChoices;
      },
      enter(state) {
        return {
          syncEnabled: state.syncEnabled,
        };
      },
    },
    {
      name: "setup-new-device",
      exitConditionsMet(state) {
        return false;
      },
      enter(state) {
        return {};
      },
    },
  ]);

  /**
   * @param {Element} formWizard
   *   The <form-wizard> element to set which step the user should be viewing
   *   on.
   * @param {string} [fakeUA=undefined]
   *   An optional fake user agent string to supply for testing. If this is
   *   not supplied, the actual navigator.userAgent string is used.
   * @param {object} [fakeTroubleshooting=undefined]
   *   An optional fake object to pass to the BrowserDetect library to simulate
   *   what is returned from a WebChannel on a Firefox Desktop browser for
   *   a request for troubleshooting data.
   */
  constructor(formWizard, fakeUA, fakeTroubleshooting) {
    this.#formWizard = formWizard;

    if (!this.#formWizard.hasAttribute("fxa-root")) {
      throw new Error(
        "Expected fxa-root on element passed to " +
          "SwitchingDevicesWizardManager constructor."
      );
    }

    this.#state.fxaRoot = this.#formWizard.getAttribute("fxa-root");

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

    this.#init(fakeUA, fakeTroubleshooting);
  }

  /**
   * Does the work of scanning the user agent to determine if this is one
   * that can actually use the wizard. If not, the <form-wizard> is told to
   * show the disqualified state.
   *
   * @param {string} [fakeUA=undefined]
   *   An optional fake user agent string to supply for testing. If this is
   *   not supplied, the actual navigator.userAgent string is used.
   * @param {object} [fakeTroubleshooting=undefined]
   *   An optional fake object to pass to the BrowserDetect library to simulate
   *   what is returned from a WebChannel on a Firefox Desktop browser for
   *   a request for troubleshooting data.
   */
  async #init(fakeUA, fakeTroubleshooting) {
    try {
      let detect = new BrowserDetect(fakeUA, null, fakeTroubleshooting);
      let browser = await detect.getBrowser();
      let platform = await detect.getOS();
      if (browser.mozilla && !platform.mobile) {
        // We need to get some query parameters from the FxA server before we
        // show the user any kind of form to create or sign-in to an account.
        // See https://mozilla.github.io/ecosystem-platform/relying-parties/reference/metrics-for-relying-parties#relying-party-hosted-email-form.
        await this.#requestMetricsParams();
        return;
      }
    } catch (e) {
      // Intentional fall-through - we want to do this if any part of the
      // UA computation didn't meet our criteria OR failed.
    }

    // mozilla/sumo #1270: Replace this placeholder text with final copy
    this.#formWizard.disqualify(
      gettext("Use Firefox to continue"),
      gettext(
        "Please switch to Firefox Desktop on your old " +
          "computer to begin the migration process"
      )
    );
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
    this.#recomputeCurrentStep();
  }

  /**
   * Computes which step should be shown to the user in <form-wizard> based
   * on the current state. Once that step is calculated, the setStep method
   * is called on the <form-wizard>, passing the name of the step and a
   * payload of settings to configure that step.
   */
  #recomputeCurrentStep() {
    for (let step of this.steps) {
      if (!step.exitConditionsMet(this.#state)) {
        let payload = step.enter(this.#state);
        this.#formWizard.setStep(step.name, payload);
        break;
      }
    }
  }

  /**
   * Makes contact with the FxA endpoint pointed at by state.fxaRoot/metrics-flow to
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
      `${this.#state.fxaRoot}/metrics-flow?${params}`
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

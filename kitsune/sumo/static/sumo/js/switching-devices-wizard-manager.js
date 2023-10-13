import trackEvent from "./analytics";
import BrowserDetect from "./browserdetect";
import UITour from "./libs/uitour";

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
  #formWizardEvents = Object.freeze([
    "DeviceMigrationWizard:ConfigureStep:TurnOnSync",
    "DeviceMigrationWizard:ConfigureStep:ChangeSyncPrefs",
    "DeviceMigrationWizard:ConfigureStep:Next",
  ]);

  // For versions of Firefox < 114, we use this value as a polling interval
  // to check for FxA sign-in state changes.
  #pollIntervalMs = 500;
  #pollIntervalID = null;

  // How many milliseconds to wait before we give up on UITour and presume
  // we cannot contact it. This is for users that may have disabled UITour
  // via about:config, or have a corrupt permissions database.
  #uiTourTimeoutMs = 3000;

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
    service: "sync",
    action: "email",
    entrypoint: "fx-new-device-sync",
    entrypoint_experiment: null,
    entrypoint_variation: null,
    flow_id: null,
    flow_begin_time: null,
    context: "fx_desktop_v3",
    form_type: "email",

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
      status: "active",
      label: () => {
        return this.#state.sumoEmail
          ? gettext("Sign in to your account")
          : gettext("Sign up for an account");
      },
      exitConditionsMet(state) {
        return state.fxaSignedIn;
      },
      enter(state) {
        trackEvent("device-migration-wizard", "report-state", "sign-into-fxa");
        let baseParams = {
          service: state.service,
          action: state.action,
          utm_source: state.utm_source,
          utm_campaign: state.utm_campaign,
          utm_medium: state.utm_medium,
          entrypoint: state.entrypoint,
          entrypoint_experiment: state.entrypoint_experiment,
          entrypoint_variation: state.entrypoint_variation,
          flow_id: state.flow_id,
          flow_begin_time: state.flow_begin_time,
          context: state.context,
          redirect_to: window.location.href,
          redirect_immediately: true,
        };

        let linkParams = new URLSearchParams();
        for (let param in baseParams) {
          if (baseParams[param]) {
            linkParams.set(param, baseParams[param]);
          }
        }

        return {
          fxaRoot: state.fxaRoot,
          email: state.sumoEmail,
          linkHref: `${state.fxaRoot}?${linkParams}`,

          ...baseParams,
        };
      },
    },
    {
      name: "configure-sync",
      status: "unavailable",
      label: () => gettext("Sync your data"),
      exitConditionsMet(state) {
        return state.syncEnabled && state.confirmedSyncChoices;
      },
      enter(state) {
        trackEvent("device-migration-wizard", "report-state", "configure-sync");
        return {
          syncEnabled: state.syncEnabled,
        };
      },
    },
    {
      name: "setup-new-device",
      status: "unavailable",
      label: () => gettext("Start browsing!"),
      exitConditionsMet(state) {
        return false;
      },
      enter(state) {
        trackEvent("device-migration-wizard", "report-state", "setup-new-device");
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
   * @param {number} [pollIntervalMs=undefined]
   *   The interval for polling for FxA state changes while under test.
   * @param {number} [uiTourTimeoutMs=undefined]
   *   The timeout for presuming UITour is broken if we haven't heard from it while
   *   under test.
   */
  constructor(formWizard, fakeUA, fakeTroubleshooting, pollIntervalMs, uiTourTimeoutMs) {
    this.#formWizard = formWizard;

    if (!this.#formWizard.hasAttribute("fxa-root")) {
      throw new Error(
        "Expected fxa-root on element passed to " +
          "SwitchingDevicesWizardManager constructor."
      );
    }

    this.#setupFormWizardStepIndicator();

    for (let eventName of this.#formWizardEvents) {
      this.#formWizard.addEventListener(eventName, this);
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

    this.#init(fakeUA, fakeTroubleshooting, pollIntervalMs, uiTourTimeoutMs);
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
   * @param {number} [pollIntervalMs=undefined]
   *   The interval for polling for FxA state changes while under test.
   * @param {number} [uiTourTimeoutMs=undefined]
   *   The timeout for presuming UITour is broken if we haven't heard from it while
   *   under test.
   */
  async #init(
    fakeUA,
    fakeTroubleshooting,
    pollIntervalMs = this.#pollIntervalMs,
    uiTourTimeoutMs = this.#uiTourTimeoutMs
  ) {
    try {
      let detect = new BrowserDetect(fakeUA, null, fakeTroubleshooting);
      let browser = await detect.getBrowser();
      let platform = await detect.getOS();
      if (browser.mozilla && !platform.mobile) {
        let uiTourPromise = new Promise((resolve) => {
          UITour.ping(resolve);
        });
        let timeoutPromise = new Promise((resolve, reject) => {
          setTimeout(() => reject(), uiTourTimeoutMs);
        });

        try {
          await Promise.race([uiTourPromise, timeoutPromise]);
        } catch (e) {
          // UITour ping timed out, so let's disqualify because UITour is broken.
          trackEvent("device-migration-wizard", "report-state", "uitour-broken");
          this.#formWizard.disqualify("uitour-broken");
          return;
        }

        await Promise.all([this.#checkForSUMOEmail(), this.#updateFxAState()]);

        if (browser.version.major >= 114) {
          // Firefox 114+ allows us to get notified when the FxA sign-in state
          // changes through UITour.
          await new Promise((resolve) => {
            UITour.observe((name, params) => {
              this.#onUITourNotification(name, params);
            }, resolve);
          });
        } else {
          // For older Firefox versions, we'll do polling.
          this.#pollIntervalID = window.setInterval(() => {
            this.#updateFxAState();
          }, pollIntervalMs);
        }

        this.#recomputeCurrentStep();

        // We need to get some query parameters from the FxA server before we
        // show the user any kind of form to sign-up or sign-in to an account.
        // See https://mozilla.github.io/ecosystem-platform/relying-parties/reference/metrics-for-relying-parties#relying-party-hosted-email-form.
        await this.#requestMetricsParams();
        return;
      } else if (platform.mobile) {
        this.#formWizard.classList.add("warning");
        this.#formWizard.toggleAttribute("disqualified-mobile", true);
      }
    } catch (e) {
      console.error(e);
      // Intentional fall-through - we want to do this if any part of the
      // UA computation didn't meet our criteria OR failed.
    }

    trackEvent("device-migration-wizard", "report-state", "need-fx-desktop");
    this.#formWizard.disqualify("need-fx-desktop");
  }

  /**
   * A testing-only function to do any cleanup once an instance of
   * SwitchingDevicesWizardManager is being thrown away.
   */
  destroy() {
    window.clearInterval(this.#pollIntervalID);
    this.#pollIntervalID = null;
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
    let oldState = this.state;
    let newState = Object.assign(this.#state, stateDiff);
    this.#state = newState;

    for (let prop in oldState) {
      if (oldState[prop] !== newState[prop]) {
        this.#recomputeCurrentStep();
        break;
      }
    }
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
   * Sets up the step indicator on the #formWizard based on the
   * default state of this.steps. This should be called either
   * during initialization or if the whole wizard is being reset
   * back to the starting state.
   */
  #setupFormWizardStepIndicator() {
    let fwSteps = this.steps.map(({ name, status, label }) => {
      return { name, status, label: label() };
    });
    this.#formWizard.steps = fwSteps;
  }

  /**
   * Update the #formWizard step indicator by modifying step data.
   * Currently only used to update step labels.
   *
   * @param {object} stepData
   *   Data for the step being updated. Must contain a name for
   *   identifying which step to update, can optionally contain
   *   a label or status.
   */
  #updateFormWizardStepIndicator(stepData) {
    let fwSteps = this.#formWizard.steps.map((step) => {
      if (step.name === stepData.name) {
        return Object.assign(step, stepData);
      }
      return step;
    });
    this.#formWizard.steps = fwSteps;
  }

  /**
   * Handler for UITour notifications. Specifically, this monitors
   * for changes to the FxA sign-in state.
   *
   * @param {string} name
   *   The name of the UITour notification.
   * @param {object} params
   *   Extra parameters that UITour sends with each notification.
   * @return {Promise<undefined>}
   *   Resolves after recomputing the FxA sign-in state.
   */
  async #onUITourNotification(name, params) {
    if (name == "FxA:SignedInStateChange") {
      await this.#updateFxAState();
    }
  }

  /**
   * Uses UITour to query for the current FxA sign-in state. A user
   * is considered signed in if their Mozilla account is both setup and
   * the account state is "ok" (as in, they have verified their email
   * address).
   *
   * Once the sign-in state is determined from UITour, the internal
   * state of the SwichingDevicesWizardManager is updated to reflect
   * it.
   *
   * In the event that the state is transitioning from "signed in" to
   * "signed out", the #formWizard is reset back to its starting point.
   */
  async #updateFxAState() {
    let fxaConfig = await new Promise((resolve) => {
      UITour.getConfiguration("fxa", resolve);
    });

    if (fxaConfig.setup && fxaConfig.accountStateOK) {
      let syncEnabled = !!fxaConfig.browserServices?.sync?.setup;
      // If the user had already confirmed their sync choices, but then sync
      // becomes disabled, they should reconfirm that their sync choices are
      // what they expect after they sign back in.
      let confirmedSyncChoices = this.#state.confirmedSyncChoices;
      if (this.#state.syncEnabled != syncEnabled &&
          confirmedSyncChoices) {
        // We need to do this in order for the form-wizard to go back a step.
        this.#setupFormWizardStepIndicator();
        confirmedSyncChoices = false;
      }

      this.#updateState({
        fxaSignedIn: true,
        syncEnabled,
        confirmedSyncChoices,
      });
    } else if (this.#state.fxaSignedIn) {
      // If we've gone from being signed in to signed out, we need to
      // reset some of our state.
      this.#setupFormWizardStepIndicator();
      this.#updateState({
        fxaSignedIn: false,
        syncEnabled: false,
        confirmedSyncChoices: false,
      });
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
      "form_type",
    ]) {
      if (this.#state[paramName]) {
        params.set(paramName, this.#state[paramName]);
      }
    }
    try {
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
    } catch (e) {
      // Log but intentionally ignore this case. If getting the metrics flow
      // parameters somehow failed (say, for example, a problem on the FxA
      // handler for metrics-flow), this shouldn't prevent the user from
      // completing their task.
      console.error(e);
    }
  }

  /**
   * Queries SUMO for the email address of the currently signed in SUMO
   * user viewing the page. If the user is logged into SUMO and the account
   * has a valid email address, we will update the internal state so that
   * the <form-wizard> can re-use that email address for signing into
   * a Firefox Account for syncing.
   */
  async #checkForSUMOEmail() {
    const query = `
      query {
        currentUser {
          email
        }
      }
    `;

    let response = await window.fetch("/graphql", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    });

    if (response.status == 200) {
      let responseBody = await response.json();
      let sumoEmail = responseBody.data?.currentUser?.email;
      if (sumoEmail) {
        this.#updateState({
          sumoEmail,
        });
        this.#updateFormWizardStepIndicator({
          name: "sign-into-fxa",
          label: gettext("Sign in to your account"),
        });
      }
    }
  }

  handleEvent(event) {
    switch (event.type) {
      case "DeviceMigrationWizard:ConfigureStep:TurnOnSync":
        // Intentional fall-through
      case "DeviceMigrationWizard:ConfigureStep:ChangeSyncPrefs": {
        UITour.openPreferences("sync");
        break;
      }
      case "DeviceMigrationWizard:ConfigureStep:Next": {
        this.#updateState({
          confirmedSyncChoices: true,
        });
        break;
      }
    }
  }
}

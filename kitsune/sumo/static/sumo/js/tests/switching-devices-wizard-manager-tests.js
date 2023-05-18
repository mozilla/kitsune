import { expect } from "chai";
import sinon from "sinon";
import UITour from "../libs/uitour";

import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";

const FAKE_FXA_ROOT = "https://example.local";
const FAKE_FXA_FLOW_ID = "abc123";
const FAKE_FXA_FLOW_BEGIN_TIME = "123456789";

/**
 * This is a utility class that knows how to respond to UITour-lib
 * messages that normally get processed by Firefox.
 *
 * The events are captured, and there are a series of built-in responses
 * for different UITour functions. Users of this class can use sinon to
 * override the default response.
 *
 * Users of this class need to ensure that they call `destroy` after
 * using it to remove the UITour event listener.
 */
class FakeUITourResponder {
  constructor() {
    document.addEventListener("mozUITour", this);
  }

  destroy() {
    document.removeEventListener("mozUITour", this);
  }

  handleEvent(event) {
    switch (event.detail.action) {
      case "ping": {
        this.onPing(event.detail.data);
        break;
      }
      case "getConfiguration": {
        this.onGetConfiguration(event.detail.data);
        break;
      }
    }
  }

  /**
   * Default response to the `ping` message sent by calling
   * `UITour.ping`.
   *
   * @param {object} data
   *   The data object passed through UITour-lib. This must include
   *   a callbackID field so that responses are properly mapped to
   *   the caller.
   */
  onPing(data) {
    FakeUITourResponder.respond(data.callbackID);
  }

  /**
   * Default response to the `getConfiguration` message sent by calling
   * `UITour.getConfiguration`.
   *
   * At this time, only `getConfiguration("fxa")` is supported, and the
   * default response indicates that no Firefox Account is currently
   * set up.
   *
   * @param {object} data
   *   The data object passed through UITour-lib. This must include
   *   a callbackID field so that responses are properly mapped to
   *   the caller.
   */
  onGetConfiguration(data) {
    if (data.configuration != "fxa") {
      throw new Error(
        "FakeUITourResponder only expects fxa configuration requests"
      );
    }

    FakeUITourResponder.respond(data.callbackID, {
      setup: false,
    });
  }

  /**
   * Queues a microtask to dispatch a response event. This is made
   * static in order for overrides to easily reuse this from within
   * a sinon stub override.
   *
   * @param {string} callbackID
   *   The callbackID associated with the event being responded to.
   * @param {object} data
   *   Any other data that should be passed along with the response.
   */
  static respond(callbackID, data = {}) {
    let event = new CustomEvent("mozUITourResponse", {
      bubbles: true,
      detail: {
        callbackID,
        data,
      },
    });
    queueMicrotask(() => {
      document.dispatchEvent(event);
    });
  }
}

describe("k", () => {
  describe("SwitchingDevicesWizardManager with a qualified UA", () => {
    const QUALIFIED_FX_UA =
      "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/114.0";
    const QUALIFIED_FX_TROUBLESHOOTING_DATA = Object.freeze({
      application: {
        name: "Firefox",
        version: "114.0.0",
        osVersion: "Windows_NT 10.0 22000",
      },
    });

    let gManager;

    let gOriginalLocation;
    let gSandbox = sinon.createSandbox();

    // A sinon stub for window.fetch, set up and reset in beforeEach and
    // afterEach, respectively.
    let gFetchStub;

    // A sinon stub for <form-wizard>.setStep. This is setup and reset
    // in beforeEach and afterEach, respectively.
    let gSetStepStub;

    // A Promise that gets created in beforeEach, and is awaited during
    // each afterEach. When this Promise resolves, the metrics-flow request
    // that's kicked off during SwitchingDevicesWizardManager construction
    // and the subsequent JSON parsing Promise have also both resolved.
    let gMetricsPromise;

    // gGraphQLQueryResult will be set to an object that is returned via
    // the stubbed out fetch request to /graphql, which is used to try to
    // get the email address of the user if they're already signed into
    // SUMO. This object is set in beforeEach so that subtests have the
    // option to override the default. By default, the returned object
    // indicates that the user is not signed into SUMO.
    let gGraphQLQueryResult;
    // A Promise that gets created in beforeEach, and is awaited during
    // each afterEach. When this Promise resolves, the graphql request
    // that's kicked off during SwitchingDevicesWizardManager construction
    // and the subsequent JSON parsing Promise have also both resolved.
    let gGraphQLQuery;

    // An instance of FakeUITourResponder that is setup before each subtest.
    let gFakeUITour;

    before(function() {
      // Some of the subtests here reconfigure JSDOM's notion of
      // window.location.href, so we record the original value so
      // we can restore it in the after() function.
      gOriginalLocation = window.location.href;
    });

    after(function() {
      global.jsdom.reconfigure({
        url: gOriginalLocation,
      });
    });

    beforeEach(() => {
      $("body").empty().html(`
        <form-wizard fxa-root="${FAKE_FXA_ROOT}"></form-wizard>
      `);
      let wizard = document.querySelector("form-wizard");
      wizard.disqualify = () => {};
      wizard.setStep = () => {};

      gGraphQLQueryResult = {
        data: {
          currentUser: {
            email: "",
          },
        },
      };

      gSetStepStub = gSandbox.stub(wizard, "setStep");

      gFetchStub = gSandbox.stub(window, "fetch");

      // This is a little complicated, but makes it so that each of our tests
      // can wait for both the metrics-flow request and JSON parsing Promises
      // to resolve before moving onto the next test. This helps ensure that
      // the tests are in a "steady state" before proceeding.
      gMetricsPromise = new Promise((resolve) => {
        gFetchStub
          .withArgs(sinon.match(new RegExp(`^${FAKE_FXA_ROOT}`)))
          .callsFake((url) => {
            let searchParams = new URLSearchParams(new URL(url).search);
            expect(searchParams.get("utm_source")).to.not.be.null;
            expect(searchParams.get("utm_campaign")).to.not.be.null;
            expect(searchParams.get("entrypoint")).to.not.be.null;
            expect(searchParams.get("form_type")).to.not.be.null;

            return Promise.resolve({
              json: () => {
                return new Promise((resolveInner) => {
                  resolveInner({
                    flowId: FAKE_FXA_FLOW_ID,
                    flowBeginTime: FAKE_FXA_FLOW_BEGIN_TIME,
                  });
                  // We need to defer resolving here so that the
                  // SwitchingDevicesWizardManager that made the request has the
                  // opportunity to react to the Promise resolution.
                  queueMicrotask(resolve);
                });
              },

              status: 200,
            });
          });
      });

      // Similar to the above, this also catches the /graphql query that runs
      // during initialization to get the SUMO user email address if the user
      // viewing the article is signed in. This helps ensure that the tests
      // are in a "steady state" before proceeding.
      gGraphQLQuery = new Promise((resolve) => {
        gFetchStub
          .withArgs(sinon.match(new RegExp(`^/graphql`)))
          .callsFake((url) => {
            return Promise.resolve({
              json: () => {
                return new Promise((resolveInner) => {
                  resolveInner(gGraphQLQueryResult);
                  // We need to defer resolving here so that the
                  // SwitchingDevicesWizardManager that made the request has the
                  // opportunity to react to the Promise resolution.
                  queueMicrotask(resolve);
                });
              },

              status: 200,
            });
          });
      });

      gFakeUITour = new FakeUITourResponder();
    });

    afterEach(async () => {
      await gGraphQLQuery;
      await gMetricsPromise;
      gFakeUITour.destroy();
      gManager.destroy();
      gSandbox.restore();
    });

    /**
     * A helper function to return a SwitchingDevicesWizardManager that
     * is constructed with some testing UA strings that result in the
     * manager evaluating the user agent as qualified to use the wizard.
     */
    let constructValidManager = (
      ua = QUALIFIED_FX_UA,
      troubleshootingData = QUALIFIED_FX_TROUBLESHOOTING_DATA,
      pollInterval
    ) => {
      gManager = new SwitchingDevicesWizardManager(
        document.querySelector("form-wizard"),
        ua,
        troubleshootingData,
        pollInterval
      );
      return gManager;
    };

    it("should be constructable", () => {
      expect(constructValidManager).to.not.throw();
    });

    it("should require an fxa-root attribute on the wizard to be constructable", async () => {
      let node = document.querySelector("form-wizard");
      node.removeAttribute("fxa-root");
      expect(constructValidManager).to.throw();

      // Most of the subtests in this test file cause the
      // SwitchingDevicesWizardManager to kick off an XHR to request
      // FxA flow metrics after construction. The testing hooks are set
      // up to ensure that those things proceed before moving onto the next
      // subtest.
      //
      // This subtest is a little special in that it's ensuring that the
      // SwitchingDevicesWizardManager construction doesn't succeed. In order
      // for our hooks to let the test file proceed to the next test, we fake
      // out the requests just to keep everything happy.
      let params = new URLSearchParams({
        utm_source: "support.mozilla.org",
        utm_campaign: "migration",
        entrypoint: "fx-new-device-sync",
        form_type: "email",
      });
      let response = await window.fetch(`${FAKE_FXA_ROOT}/metrics-flow?${params}`);
      await response.json();
      response = await window.fetch("/graphql");
      await response.json();
    });

    it("should have fallback UTM parameters in case none are passed", () => {
      global.jsdom.reconfigure({
        url: "https://support.mozilla.org/no-params-url",
      });

      let manager = constructValidManager();
      expect(manager.state.utm_source).to.equal("support.mozilla.org");
      expect(manager.state.utm_campaign).to.equal("migration");
      expect(manager.state.utm_medium).to.equal("mozilla-websites");
    });

    it("should read UTM parameters passed through the URL search params", () => {
      global.jsdom.reconfigure({
        url:
          "https://support.mozilla.org/params-url?utm_source=source&utm_campaign=campaign&utm_medium=medium",
      });

      let manager = constructValidManager();
      expect(manager.state.utm_source).to.equal("source");
      expect(manager.state.utm_campaign).to.equal("campaign");
      expect(manager.state.utm_medium).to.equal("medium");

      global.jsdom.reconfigure({
        url: gOriginalLocation,
      });
    });

    it("should read entrypoint parameters passed through the URL search params", () => {
      global.jsdom.reconfigure({
        url:
          "https://support.mozilla.org/params-url?entrypoint=entrypoint&entrypoint_variation=variation&entrypoint_experiment=experiment",
      });

      let manager = constructValidManager();
      expect(manager.state.entrypoint).to.equal("entrypoint");
      expect(manager.state.entrypoint_variation).to.equal("variation");
      expect(manager.state.entrypoint_experiment).to.equal("experiment");

      global.jsdom.reconfigure({
        url: gOriginalLocation,
      });
    });

    it("should request flow metrics from the FxA root and update internal state", async () => {
      let manager = constructValidManager();
      await gMetricsPromise;

      expect(manager.state.flow_id).to.equal(FAKE_FXA_FLOW_ID);
      expect(manager.state.flow_begin_time).to.equal(FAKE_FXA_FLOW_BEGIN_TIME);
      expect(manager.state.utm_source).to.equal("support.mozilla.org");
    });

    it("should send the user to the sign-into-fxa step when not signed in", async () => {
      let setStepCalled = new Promise((resolve) => {
        gSetStepStub.callsFake((name, payload) => {
          if (payload.flow_id && payload.flow_begin_time) {
            resolve({ name, payload });
          }
        });
      });

      let manager = constructValidManager();
      await gMetricsPromise;
      let { name, payload } = await setStepCalled;
      expect(name).to.equal("sign-into-fxa");
      expect(payload).to.deep.equal({
        fxaRoot: FAKE_FXA_ROOT,
        email: "",
        linkHref: `${FAKE_FXA_ROOT}?service=sync&action=email&utm_source=support.mozilla.org&utm_campaign=migration&utm_medium=mozilla-websites&entrypoint=fx-new-device-sync&flow_id=${FAKE_FXA_FLOW_ID}&flow_begin_time=${FAKE_FXA_FLOW_BEGIN_TIME}&context=fx_desktop_v3&redirect_to=https%3A%2F%2Fexample.com%2F%23search&redirect_immediately=true`,

        service: "sync",
        action: "email",
        utm_source: "support.mozilla.org",
        utm_campaign: "migration",
        utm_medium: "mozilla-websites",
        entrypoint: "fx-new-device-sync",
        entrypoint_experiment: null,
        entrypoint_variation: null,
        flow_id: FAKE_FXA_FLOW_ID,
        flow_begin_time: FAKE_FXA_FLOW_BEGIN_TIME,
        context: "fx_desktop_v3",
        redirect_to: window.location.href,
        redirect_immediately: true,
      });
    });

    it("should not let the user advance past the sign-into-fxa step unless signed in", async () => {
      let manager = constructValidManager();
      let step = manager.steps.find((s) => s.name == "sign-into-fxa");

      expect(step.exitConditionsMet({ fxaSignedIn: false })).to.be.false;
      expect(step.exitConditionsMet({ fxaSignedIn: true })).to.be.true;
    });

    it("should have the sign-into-fxa step emit the right payload if entering", async () => {
      let manager = constructValidManager();
      let step = manager.steps.find((s) => s.name == "sign-into-fxa");

      const TEST_STATE = {
        service: "sync",
        action: "email",
        utm_source: "support.mozilla.org",
        utm_campaign: "migration",
        utm_medium: "mozilla-websites",
        entrypoint: "fx-new-device-sync",
        entrypoint_experiment: "experiment",
        entrypoint_variation: "variation",
        flow_id: FAKE_FXA_FLOW_ID,
        flow_begin_time: FAKE_FXA_FLOW_BEGIN_TIME,
        context: "fx_desktop_v3",
        fxaRoot: FAKE_FXA_ROOT,
        fxaSignedIn: false,
        sumoEmail: "test@example.com",
        syncEnabled: false,
        confirmedSyncChoices: false,
      };
      const EXPECTED_PAYLOAD = {
        service: "sync",
        action: "email",
        utm_source: "support.mozilla.org",
        utm_campaign: "migration",
        utm_medium: "mozilla-websites",
        entrypoint: "fx-new-device-sync",
        entrypoint_experiment: "experiment",
        entrypoint_variation: "variation",
        flow_id: FAKE_FXA_FLOW_ID,
        flow_begin_time: FAKE_FXA_FLOW_BEGIN_TIME,
        context: "fx_desktop_v3",
        fxaRoot: FAKE_FXA_ROOT,
        email: "test@example.com",
        redirect_to: window.location.href,
        redirect_immediately: true,
        linkHref: `${FAKE_FXA_ROOT}?service=sync&action=email&utm_source=support.mozilla.org&utm_campaign=migration&utm_medium=mozilla-websites&entrypoint=fx-new-device-sync&entrypoint_experiment=experiment&entrypoint_variation=variation&flow_id=${FAKE_FXA_FLOW_ID}&flow_begin_time=${FAKE_FXA_FLOW_BEGIN_TIME}&context=fx_desktop_v3&redirect_to=https%3A%2F%2Fexample.com%2F%23search&redirect_immediately=true`,
      };
      expect(step.enter(TEST_STATE)).to.deep.equal(EXPECTED_PAYLOAD);
    });

    it("should send the user to the configure-sync step immediately if UITour says that the user is signed in", async () => {
      let setStepCalled = new Promise((resolve) => {
        gSetStepStub.callsFake((name, payload) => {
          resolve({ name, payload });
        });
      });

      gSandbox.stub(gFakeUITour, "onGetConfiguration").callsFake((data) => {
        FakeUITourResponder.respond(data.callbackID, {
          setup: true,
          accountStateOK: true,
          browserServices: {
            sync: {
              setup: true,
            },
          },
        });
      });

      let manager = constructValidManager();
      await gMetricsPromise;
      let { name, payload } = await setStepCalled;
      expect(name).to.equal("configure-sync");
      expect(payload).to.deep.equal({
        syncEnabled: true,
        forgotPasswordLinkHref: `${FAKE_FXA_ROOT}/reset_password`,
      });
    });

    it("should not let the user advance past the configure-sync step unless sync enabled and configured", async () => {
      let manager = constructValidManager();
      let step = manager.steps.find((s) => s.name == "configure-sync");
      expect(
        step.exitConditionsMet({
          syncEnabled: false,
          confirmedSyncChoices: false,
        })
      ).to.be.false;
      expect(
        step.exitConditionsMet({
          syncEnabled: true,
          confirmedSyncChoices: false,
        })
      ).to.be.false;
      expect(
        step.exitConditionsMet({
          syncEnabled: true,
          confirmedSyncChoices: true,
        })
      ).to.be.true;

      // I suppose this could occur if the user confirms their choices, and at the
      // same instant, sync gets disabled. Seems unlikely, but testing it anyway.
      expect(
        step.exitConditionsMet({
          syncEnabled: false,
          confirmedSyncChoices: true,
        })
      ).to.be.false;
    });

    it("should have the configure-sync step emit the right payload if entering", async () => {
      let manager = constructValidManager();
      let step = manager.steps.find((s) => s.name == "configure-sync");

      const TEST_STATE = {
        utm_source: "support.mozilla.org",
        utm_campaign: "migration",
        utm_medium: "mozilla-websites",
        entrypoint: "fx-new-device-sync",
        entrypoint_experiment: "experiment",
        entrypoint_variation: "variation",
        flow_id: FAKE_FXA_FLOW_ID,
        flow_begin_time: FAKE_FXA_FLOW_BEGIN_TIME,
        context: "sync",
        fxaRoot: FAKE_FXA_ROOT,
        fxaSignedIn: true,
        sumoEmail: "test@example.com",
        syncEnabled: false,
        confirmedSyncChoices: false,
      };
      const EXPECTED_PAYLOAD = {
        syncEnabled: false,
        forgotPasswordLinkHref: `${FAKE_FXA_ROOT}/reset_password`,
      };
      expect(step.enter(TEST_STATE)).to.deep.equal(EXPECTED_PAYLOAD);
    });

    it("should not let the user exit the setup-new-device step", async () => {
      let manager = constructValidManager();
      let step = manager.steps.find((s) => s.name == "setup-new-device");
      expect(step.exitConditionsMet()).to.be.false;
      expect(
        step.exitConditionsMet({
          fxaSignedIn: true,
          syncEnabled: true,
          confirmedSyncChoices: true,
        })
      ).to.be.false;
    });

    it("should not supply a payload to the setup-new-device step when entering", async () => {
      let manager = constructValidManager();
      let step = manager.steps.find((s) => s.name == "setup-new-device");

      const TEST_STATE = {
        utm_source: "support.mozilla.org",
        utm_campaign: "migration",
        utm_medium: "mozilla-websites",
        entrypoint: "fx-new-device-sync",
        entrypoint_experiment: "experiment",
        entrypoint_variation: "variation",
        flow_id: FAKE_FXA_FLOW_ID,
        flow_begin_time: FAKE_FXA_FLOW_BEGIN_TIME,
        context: "sync",
        fxaRoot: FAKE_FXA_ROOT,
        fxaSignedIn: true,
        sumoEmail: "test@example.com",
        syncEnabled: true,
        confirmedSyncChoices: true,
      };
      const EXPECTED_PAYLOAD = {};

      expect(step.enter(TEST_STATE)).to.deep.equal(EXPECTED_PAYLOAD);
    });

    it("should not poll for FxA sign-in when using a version of Firefox >= 114", async () => {
      let setIntervalStub = gSandbox.stub(window, "setInterval").callThrough();
      let manager = constructValidManager(undefined, undefined, 1);
      await gMetricsPromise;
      expect(setIntervalStub.called).to.be.false;
    });

    it("should poll for FxA sign-in when using versions of Firefox < 114", async () => {
      const QUALIFIED_OLDER_FX_UA =
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/112.0";
      const QUALIFIED_OLDER_FX_TROUBLESHOOTING_DATA = Object.freeze({
        application: {
          name: "Firefox",
          version: "112.0.0",
          osVersion: "Windows_NT 10.0 22000",
        },
      });

      let setIntervalStub = gSandbox.stub(window, "setInterval").callThrough();

      let polledForConfig = new Promise((resolve) => {
        gSandbox
          .stub(gFakeUITour, "onGetConfiguration")
          .onCall(2)
          .callsFake((data) => {
            FakeUITourResponder.respond(data.callbackID, {
              setup: true,
              accountStateOK: true,
              browserServices: {
                sync: {
                  setup: true,
                },
              },
            });
            resolve();
          })
          .callThrough();
      });

      let manager = constructValidManager(
        QUALIFIED_OLDER_FX_UA,
        QUALIFIED_OLDER_FX_TROUBLESHOOTING_DATA,
        1
      );
      await polledForConfig;
      expect(setIntervalStub.called).to.be.true;
    });

    it("should poll for FxA sign-out when using versions of Firefox < 114", async () => {
      const QUALIFIED_OLDER_FX_UA =
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/112.0";
      const QUALIFIED_OLDER_FX_TROUBLESHOOTING_DATA = Object.freeze({
        application: {
          name: "Firefox",
          version: "112.0.0",
          osVersion: "Windows_NT 10.0 22000",
        },
      });

      let setIntervalStub = gSandbox.stub(window, "setInterval").callThrough();

      let polledForConfig = new Promise((resolve) => {
        gSandbox
          .stub(gFakeUITour, "onGetConfiguration")
          .onCall(0)
          .callsFake((data) => {
            FakeUITourResponder.respond(data.callbackID, {
              setup: true,
              accountStateOK: true,
              browserServices: {
                sync: {
                  setup: true,
                },
              },
            });
          })
          .onCall(2)
          .callsFake((data) => {
            FakeUITourResponder.respond(data.callbackID, {
              setup: false,
            });
            queueMicrotask(resolve);
          });
      });

      let manager = constructValidManager(
        QUALIFIED_OLDER_FX_UA,
        QUALIFIED_OLDER_FX_TROUBLESHOOTING_DATA,
        1
      );
      await polledForConfig;
      expect(setIntervalStub.called).to.be.true;
      expect(manager.state.fxaSignedIn).to.be.false;
      expect(manager.state.syncEnabled).to.be.false;
      expect(manager.state.confirmedSyncChoices).to.be.false;
    });

    it("should be able to poll for disabling sync after confirming sync choices", async () => {
      const QUALIFIED_OLDER_FX_UA =
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:100.0) Gecko/20100101 Firefox/112.0";
      const QUALIFIED_OLDER_FX_TROUBLESHOOTING_DATA = Object.freeze({
        application: {
          name: "Firefox",
          version: "112.0.0",
          osVersion: "Windows_NT 10.0 22000",
        },
      });

      let setIntervalStub = gSandbox.stub(window, "setInterval").callThrough();

      let signedInStub;
      let polledForSignedInConfig = new Promise((resolve) => {
        signedInStub = gSandbox
          .stub(gFakeUITour, "onGetConfiguration")
          .callsFake((data) => {
            FakeUITourResponder.respond(data.callbackID, {
              setup: true,
              accountStateOK: true,
              browserServices: {
                sync: {
                  setup: true,
                },
              },
            });
            queueMicrotask(resolve);
          });
      });

      let manager = constructValidManager(
        QUALIFIED_OLDER_FX_UA,
        QUALIFIED_OLDER_FX_TROUBLESHOOTING_DATA,
        1
      );
      await polledForSignedInConfig;
      signedInStub.restore();

      // This simulates the user hitting the "Next" button on the sync
      // configuration step.
      let nextEvent = new CustomEvent(
        "DeviceMigrationWizard:ConfigureStep:Next",
        { bubbles: true }
      );
      let wizard = document.querySelector("form-wizard");
      wizard.dispatchEvent(nextEvent);

      expect(manager.state.confirmedSyncChoices).to.be.true;

      await new Promise((resolve) => {
        gSandbox.stub(gFakeUITour, "onGetConfiguration").callsFake((data) => {
          FakeUITourResponder.respond(data.callbackID, {
            setup: true,
            accountStateOK: true,
            browserServices: {
              sync: {
                setup: false,
              },
            },
          });
          queueMicrotask(resolve);
        });
      });

      expect(setIntervalStub.called).to.be.true;
      expect(manager.state.fxaSignedIn).to.be.true;
      expect(manager.state.syncEnabled).to.be.false;
      expect(manager.state.confirmedSyncChoices).to.be.false;
    });

    it("should have its state updated with the signed-in SUMO account email address if it exists", async () => {
      const TEST_EMAIL = "test@example.com";
      gGraphQLQueryResult = {
        data: {
          currentUser: {
            email: TEST_EMAIL,
          },
        },
      };
      let manager = constructValidManager();
      await gGraphQLQuery;
      expect(manager.state.sumoEmail).to.equal(TEST_EMAIL);
    });
  });

  describe("SwitchingDevicesWizardManager with a disqualified UA", () => {
    const DISQUALIFIED_FX_UA =
      "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36";

    let gSandbox = sinon.createSandbox();

    // A sinon stub for <form-wizard>.setStep. This is setup and reset
    // in beforeEach and afterEach, respectively.
    let gSetStepStub;

    // A sinon stub for <form-wizard>.disqualify. This is setup and reset
    // in beforeEach and afterEach, respectively.
    let gDisqualifyStub;

    after(function() {
      gSandbox.restore();
    });

    beforeEach(() => {
      $("body").empty().html(`
        <form-wizard fxa-root="${FAKE_FXA_ROOT}"></form-wizard>
      `);
      let wizard = document.querySelector("form-wizard");
      wizard.disqualify = () => {};
      wizard.setStep = () => {};
      gSetStepStub = gSandbox.stub(wizard, "setStep");
      gDisqualifyStub = gSandbox.stub(wizard, "disqualify");
    });

    afterEach(async () => {
      gSetStepStub.restore();
      gDisqualifyStub.restore();
    });

    /**
     * A helper function to return a SwitchingDevicesWizardManager that
     * is constructed with some testing UA strings that result in the
     * manager evaluating the user agent as NOT qualified to use the wizard.
     */
    let constructInvalidManager = () => {
      return new SwitchingDevicesWizardManager(
        document.querySelector("form-wizard"),
        DISQUALIFIED_FX_UA
      );
    };

    it("should be constructable", () => {
      expect(constructInvalidManager).to.not.throw();
    });

    it("should require an fxa-root attribute on the wizard to be constructable", async () => {
      let node = document.querySelector("form-wizard");
      node.removeAttribute("fxa-root");
      expect(constructInvalidManager).to.throw();
    });

    it("should result in the wizard being called with disqualify", async () => {
      let disqualifyCalled = new Promise((resolve) => {
        gDisqualifyStub.callsFake((header, message) => {
          resolve({ header, message });
        });
      });
      let manager = constructInvalidManager();
      let { header, message } = await disqualifyCalled;
      expect(gSetStepStub.called).to.be.false;
      expect(header).to.not.be.empty;
      expect(message).to.not.be.empty;
    });
  });
});

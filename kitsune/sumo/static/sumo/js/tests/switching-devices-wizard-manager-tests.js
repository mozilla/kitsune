import { expect } from "chai";
import sinon from "sinon";

import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";

const FAKE_FXA_ROOT = "https://example.local";
const FAKE_FXA_FLOW_ID = "abc123";
const FAKE_FXA_FLOW_BEGIN_TIME = "123456789";

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

      // This is a little complicated, but makes it so that each of our tests
      // can wait for both the metrics-flow request and JSON parsing Promises
      // to resolve before moving onto the next test. This helps ensure that
      // the tests are in a "steady state" before proceeding.
      gMetricsPromise = new Promise((resolve) => {
        gFetchStub = gSandbox.stub(window, "fetch").callsFake((url) => {
          if (!url.startsWith(FAKE_FXA_ROOT)) {
            throw new Error("Fetch called with an unexpected URL: " + url);
          }

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
    });

    afterEach(async () => {
      await gMetricsPromise;
      gFetchStub.restore();
      gSetStepStub.restore();
    });

    /**
     * A helper function to return a SwitchingDevicesWizardManager that
     * is constructed with some testing UA strings that result in the
     * manager evaluating the user agent as qualified to use the wizard.
     */
    let constructValidManager = () => {
      return new SwitchingDevicesWizardManager(
        document.querySelector("form-wizard"),
        QUALIFIED_FX_UA,
        QUALIFIED_FX_TROUBLESHOOTING_DATA
      );
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
      let response = await window.fetch(FAKE_FXA_ROOT);
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

    it("should sent the user to the sign-into-fxa step when not signed in", async () => {
      let setStepCalled = new Promise((resolve) => {
        gSetStepStub.callsFake((name, payload) => {
          resolve({ name, payload });
        });
      });

      let manager = constructValidManager();
      await gMetricsPromise;
      let { name, payload } = await setStepCalled;
      expect(name).to.equal("sign-into-fxa");
      expect(payload).to.deep.equal({
        fxaRoot: FAKE_FXA_ROOT,
        email: "",

        utm_source: "support.mozilla.org",
        utm_campaign: "migration",
        utm_medium: "mozilla-websites",
        entrypoint: "fx-new-device-sync",
        entrypoint_experiment: null,
        entrypoint_variation: null,
        flow_id: FAKE_FXA_FLOW_ID,
        flow_begin_time: FAKE_FXA_FLOW_BEGIN_TIME,
        context: null,
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
        fxaSignedIn: false,
        sumoEmail: "test@example.com",
        syncEnabled: false,
        confirmedSyncChoices: false,
      };
      const EXPECTED_PAYLOAD = {
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
        email: "test@example.com",
      };
      expect(step.enter(TEST_STATE)).to.deep.equal(EXPECTED_PAYLOAD);
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

import { expect } from "chai";
import sinon from "sinon";

import SwitchingDevicesWizardManager from "sumo/js/switching-devices-wizard-manager";

const FAKE_FXA_ROOT = "https://example.local";
const FAKE_FXA_FLOW_ID = "abc123";
const FAKE_FXA_FLOW_BEGIN_TIME = "123456789";

describe("k", () => {
  describe("SwitchingDevicesWizardManager", () => {
    let gOriginalLocation;
    let gSandbox = sinon.createSandbox();

    // A sinon stub for window.fetch, set up in beforeEach
    let gFetchStub;

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
    });

    it("should be constructable", () => {
      expect(() => {
        new SwitchingDevicesWizardManager(
          document.querySelector("form-wizard")
        );
      }).to.not.throw();
    });

    it("should require an fxa-root attribute on the wizard to be constructable", async () => {
      let node = document.querySelector("form-wizard");
      node.removeAttribute("fxa-root");
      expect(() => {
        new SwitchingDevicesWizardManager(node);
      }).to.throw();

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

      let manager = new SwitchingDevicesWizardManager(
        document.querySelector("form-wizard")
      );
      expect(manager.state.utm_source).to.equal("support.mozilla.org");
      expect(manager.state.utm_campaign).to.equal("migration");
      expect(manager.state.utm_medium).to.equal("mozilla-websites");
    });

    it("should read UTM parameters passed through the URL search params", () => {
      global.jsdom.reconfigure({
        url:
          "https://support.mozilla.org/params-url?utm_source=source&utm_campaign=campaign&utm_medium=medium",
      });

      let manager = new SwitchingDevicesWizardManager(
        document.querySelector("form-wizard")
      );
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

      let manager = new SwitchingDevicesWizardManager(
        document.querySelector("form-wizard")
      );
      expect(manager.state.entrypoint).to.equal("entrypoint");
      expect(manager.state.entrypoint_variation).to.equal("variation");
      expect(manager.state.entrypoint_experiment).to.equal("experiment");

      global.jsdom.reconfigure({
        url: gOriginalLocation,
      });
    });

    it("should request flow metrics from the FxA root and update internal state", async () => {
      let manager = new SwitchingDevicesWizardManager(
        document.querySelector("form-wizard")
      );
      await gMetricsPromise;

      expect(manager.state.flow_id).to.equal(FAKE_FXA_FLOW_ID);
      expect(manager.state.flow_begin_time).to.equal(
        FAKE_FXA_FLOW_BEGIN_TIME
      );
      expect(manager.state.utm_source).to.equal(
        "support.mozilla.org"
      );
    });
  });
});

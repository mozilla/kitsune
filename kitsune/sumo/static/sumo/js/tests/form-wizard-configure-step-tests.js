import { expect } from "chai";
import { ConfigureStep } from "sumo/js/form-wizard-configure-step";

async function waitForEvent(target, eventName) {
  return new Promise(resolve => {
    target.addEventListener(eventName, resolve, { once: true });
  })
}

describe("configure-step custom element", () => {
  let step;
  let slot;

  beforeEach(() => {
    step = new ConfigureStep();
    $("body").empty().append(step);
  });

  it("should render a configure-step custom element", () => {
    expect(step).to.exist;
    expect(step).to.be.an.instanceof(ConfigureStep);
  });

  it("should properly render the not-syncing state", () => {
    step.setState({
      syncEnabled: false,
    });
    let shadow = step.shadowRoot;
    expect(shadow.querySelector("#sync-status").hasAttribute("sync-enabled")).to.be.false;
    expect(shadow.querySelector("#buttons").hasAttribute("sync-enabled")).to.be.false;
    expect(shadow.querySelector("#next").disabled).to.be.true;
  });

  it("should properly render the syncing state", () => {
    step.setState({
      syncEnabled: true,
    });
    let shadow = step.shadowRoot;
    expect(shadow.querySelector("#sync-status").hasAttribute("sync-enabled")).to.be.true;
    expect(shadow.querySelector("#buttons").hasAttribute("sync-enabled")).to.be.true;
    expect(shadow.querySelector("#next").disabled).to.be.false;
  });

  it("should send the expected events when buttons are clicked", async () => {
    step.setState({
      syncEnabled: false,
    });
    let shadow = step.shadowRoot;

    let sawTurnOnSyncEvent = waitForEvent(step, "DeviceMigrationWizard:ConfigureStep:TurnOnSync");
    shadow.querySelector("#turn-on-sync").click();
    expect(await sawTurnOnSyncEvent).to.not.be.null;

    let sawChangeSyncPrefsEvent = waitForEvent(step, "DeviceMigrationWizard:ConfigureStep:ChangeSyncPrefs");
    shadow.querySelector("#change-sync-prefs").click();
    expect(await sawChangeSyncPrefsEvent).to.not.be.null;

    let listener = event => {
      expect.fail("Did not expect next button to fire event.");
    }
    let nextButton = shadow.querySelector("#next");
    nextButton.addEventListener("click", listener);
    nextButton.click();
    nextButton.removeEventListener("click", listener);
  });
});

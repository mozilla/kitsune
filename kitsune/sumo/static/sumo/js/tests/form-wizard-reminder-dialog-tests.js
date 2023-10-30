import { expect } from "chai";
import sinon from "sinon";
import { ReminderDialog } from "sumo/js/form-wizard-reminder-dialog";

describe("reminder-dialog custom element", () => {
  const DOWNLOAD_LINK = "https://mzl.la/newdevice"
  const TEST_BLOB_URL = "blob:test123";

  let sandbox;
  let clock;

  before(() => {
    sandbox = sinon.createSandbox();
    // The ICS file is generated as a Blob and linked to as a Blob URL.
    // Neither of these things are currently supported in the jsdom
    // environment, so instead we stub out the return value of createObjectURL
    // to return a constant that we can test for.
    sandbox.stub(global.window.URL, "createObjectURL").returns(TEST_BLOB_URL);

    // The reminder events that the dialog creates are relative to
    // the current date. To make testing managable, we use Sinon's
    // capability of faking out the current date and time to something
    // stable from test run to test run.
    sandbox.useFakeTimers({
      now: new Date(Date.parse("1 Oct 2023")).getTime(),
      shouldClearNativeTimers: true,
    });
  });

  after(() => {
    sandbox.restore();
  });

  let dialog;

  beforeEach(() => {
    dialog = new ReminderDialog();
    dialog.close = () => {};
    $("body").empty().append(dialog);
  });

  it("should render a reminder-dialog custom element", () => {
    expect(dialog).to.exist;
    expect(dialog).to.be.an.instanceof(ReminderDialog);
  });

  it("should have its close method called when clicking the close button", () => {
    let closeButton = dialog.shadow.querySelector("#close");
    let closeSpy = sinon.spy(dialog, "close");
    closeButton.click();
    expect(closeSpy.calledOnce).to.be.true;
    closeSpy.restore();
  });

  it("should show a select dropdown for choosing a calendar service/app", () => {
    let selector = dialog.shadow.querySelector("#choose-calendar");
    expect(selector).to.exist;

    let createButton = dialog.shadow.querySelector("#create-event");
    expect(createButton).to.exist;
  });

  it("selector should allow the user to add an event to Google Calendar", () => {
    let windowOpenSpy = sandbox.spy(window, "open");

    let selector = dialog.shadow.querySelector("#choose-calendar");
    selector.value = "gcal";

    let createButton = dialog.shadow.querySelector("#create-event");
    createButton.click();

    expect(windowOpenSpy.calledOnce).to.be.true;
    let url = new URL(windowOpenSpy.getCall(0).args[0]);
    let params = new URLSearchParams(url.search);
    expect(params.get("action")).to.equal("TEMPLATE");
    expect(params.get("dates")).to.equal("20231015/20231015");
    expect(params.get("text")).to.not.be.empty;
    expect(params.get("details")).to.not.be.empty;

    windowOpenSpy.restore();
  });

  it("selector should allow the user to add an event to Microsoft Outlook", () => {
    let windowOpenSpy = sandbox.spy(window, "open");

    let selector = dialog.shadow.querySelector("#choose-calendar");
    selector.value = "outlook";

    let createButton = dialog.shadow.querySelector("#create-event");
    createButton.click();

    expect(windowOpenSpy.calledOnce).to.be.true;
    let url = new URL(windowOpenSpy.getCall(0).args[0]);
    let params = new URLSearchParams(url.search);
    expect(params.get("body")).to.not.be.empty;
    expect(params.get("subject")).to.not.be.empty;
    expect(params.get("startdt")).to.equal("2023-10-15")
    expect(params.get("enddt")).to.equal("2023-10-16")
    expect(params.get("rru")).to.equal("addevent");
    expect(params.get("path")).to.equal("/calendar/action/compose");
    expect(params.get("allday")).to.equal("true");

    windowOpenSpy.restore();
  });

  it("selector should allow the user to download an .ics file", async () => {
    let anchorClickPromise = new Promise(resolve => {
      dialog.shadow.addEventListener("click", function onAnchorClick(event) {
        if (event.target.hasAttribute("download")) {
          event.preventDefault();
          event.stopPropagation();

          dialog.shadow.removeEventListener("click", onAnchorClick);
          resolve(event.target.href);
        }
      });
    });
    let selector = dialog.shadow.querySelector("#choose-calendar");
    selector.value = "ics";

    let createButton = dialog.shadow.querySelector("#create-event");
    createButton.click();

    let href = await anchorClickPromise;
    expect(href).to.equal(TEST_BLOB_URL);
  });

  it("should copy the download link to the clipboard if copy-link is clicked", () => {
    let writeTextSpy = sinon.spy();
    // The clipboard property is not provided by JSDom.
    Object.defineProperty(navigator, "clipboard", {
      value: {
        writeText: writeTextSpy,
      },
      configurable: true,
    });

    let copyButton = dialog.shadow.querySelector("#copy-link");
    expect(copyButton).to.exist;
    copyButton.click();
    expect(writeTextSpy.calledOnceWith(DOWNLOAD_LINK)).to.be.true;
    delete navigator.clipboard;
  });
});

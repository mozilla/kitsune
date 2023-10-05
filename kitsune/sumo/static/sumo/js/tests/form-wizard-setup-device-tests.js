import { expect } from "chai";
import sinon from "sinon";
import { SetupDeviceStep } from "sumo/js/form-wizard-setup-device-step";

describe("setup-device-step custom element", () => {
  const DOWNLOAD_LINK = "https://mzl.la/newdevice"
  let step;

  beforeEach(() => {
    step = new SetupDeviceStep();
    $("body").empty().append(step);
  });

  it("should render a setup-device-step custom element", () => {
    expect(step).to.exist;
    expect(step).to.be.an.instanceof(SetupDeviceStep);
  });

  it("should display a link to download Firefox on a new device", () => {
    let downloadLink = step.shadowRoot.getElementById("download-link");
    expect(downloadLink).to.exist;
    expect(downloadLink.textContent).to.equal(DOWNLOAD_LINK);
    expect(downloadLink.href).to.equal(DOWNLOAD_LINK);
  });

  it("should contain a button that allows for copying the download link", () => {
    let writeTextSpy = sinon.spy();
    // The clipboard property is not provided by JSDom.
    Object.defineProperty(navigator, "clipboard", {
      value: {
        writeText: writeTextSpy,
      },
      configurable: true,
    });

    let copyButton = step.shadowRoot.getElementById("copy-button");
    expect(copyButton).to.exist;
    copyButton.click();
    expect(writeTextSpy.calledOnceWith(DOWNLOAD_LINK)).to.be.true;
    delete navigator.clipboard;
  })
});

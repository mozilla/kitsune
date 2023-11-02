import { expect } from "chai";
import sinon from "sinon";
import { SetupDeviceStep } from "sumo/js/form-wizard-setup-device-step";
import { ReminderDialog } from "sumo/js/form-wizard-reminder-dialog";

function assertFormElements(form, expectedElements) {
  let expectations = Object.assign({}, expectedElements);

  for (let element of form.elements) {
    if (element.type == "submit") {
      continue;
    }

    expect(expectations[element.name], `Checking ${element.name}`).to.exist;
    expect(element.type).to.equal(expectations[element.name].type);
    expect(element.disabled).to.equal(expectations[element.name].disabled);
    expect(element.value).to.equal(expectations[element.name].value);
    delete expectations[element.name];
  }

  expect(Object.keys(expectations).length).to.equal(0);
}

describe("setup-device-step custom element", () => {
  const DOWNLOAD_LINK = "https://mzl.la/newdevice"
  let step;

  before(() => {
    ReminderDialog.prototype.showModal = () => {};
  });

  after(() => {
    delete ReminderDialog.prototype.showModal;
  })

  beforeEach(() => {
    step = new SetupDeviceStep();
    $("body").empty().append(step);
  });

  it("should render a setup-device-step custom element", () => {
    expect(step).to.exist;
    expect(step).to.be.an.instanceof(SetupDeviceStep);
  });

  it("should offer a button to open the calendar reminder dialog", async () => {
    let openDialogBtn = step.shadowRoot.querySelector("#open-reminder-dialog-button");
    openDialogBtn.click();

    expect(document.querySelector(".reminder-dialog")).to.exist;
  });

  describe("form valdiation", () => {
    let form;
    let emailErrorMessage;
    let emailField;
    let submitBtn;
    let otherBtn;

    beforeEach(() => {
      form = step.shadowRoot.querySelector("form");
      emailErrorMessage = form.querySelector("#email-error");
      emailField = form.querySelector("input[name=email]");
      submitBtn = form.querySelector("#submit");
      otherBtn = step.shadowRoot.querySelector("#open-reminder-dialog-button");
    });

    it("should have a form that can register for a one-time newsletter", () => {
      assertFormElements(form, {
        newsletters: { type: "hidden", value: "download-firefox-desktop-migration", disabled: false },
        "source-url": { type: "hidden", value: window.location.href, disabled: false },
        lang: { type: "hidden", value: navigator.language, disabled: false },
        email: { type: "email", value: "", disabled: false },
      });
    });

    it("should have the form send the document language if defined", () => {
      const TEST_LANG = "test-lang";
      document.documentElement.setAttribute("lang", TEST_LANG);

      // Setting the language from the documentElement occurs at
      // DOM binding time, so we remove and re-add the step to the
      // DOM to kick it off.
      step.remove();
      document.body.appendChild(step);
      assertFormElements(form, {
        newsletters: { type: "hidden", value: "download-firefox-desktop-migration", disabled: false },
        "source-url": { type: "hidden", value: window.location.href, disabled: false },
        lang: { type: "hidden", value: TEST_LANG, disabled: false },
        email: { type: "email", value: "", disabled: false },
      });
    });

    it("should display an error message if an incomplete email address is supplied", () => {
      expect([...emailErrorMessage.classList]).to.not.include("visible");

      emailField.value = "this-is-not-an-email-address";
      emailField.dispatchEvent(new CustomEvent("input", { bubbles: true }));
      emailField.dispatchEvent(new CustomEvent("blur", { bubbles: true }));
      expect(submitBtn.disabled).to.be.true;

      expect(emailField.validity.valid).to.be.false;
      expect([...emailErrorMessage.classList]).to.include("visible");
      expect(emailErrorMessage.getAttribute("error-type")).to.equal("invalid-email");
    });

    it("should allow a valid email address to be submitted", async () => {
      expect([...emailErrorMessage.classList]).to.not.include("visible");

      let preventSubmitListener = new Promise((resolve) => {
        form.addEventListener(
          "submit",
          (e) => {
            e.preventDefault();
            resolve();
          },
          { once: true }
        );
      });

      emailField.value = "example@example.com";
      emailField.dispatchEvent(new CustomEvent("input", { bubbles: true }));
      emailField.dispatchEvent(new CustomEvent("blur", { bubbles: true }));
      expect(submitBtn.disabled).to.be.false;

      expect(emailField.validity.valid).to.be.true;
      expect([...emailErrorMessage.classList]).to.not.include("visible");
      submitBtn.click();
      await preventSubmitListener;
    });

    it("should clear the success state if the email input is modified", async () => {
      submitBtn.toggleAttribute("success", true);

      emailField.value = "example@example.com";
      emailField.dispatchEvent(new CustomEvent("input", { bubbles: true }));
      emailField.dispatchEvent(new CustomEvent("blur", { bubbles: true }));
      expect(submitBtn.hasAttribute("success")).to.be.false;
    });

    it("should hide the error message if the reminder dialog is opened", async () => {
      emailField.value = "this-is-not-an-email-address";
      emailField.dispatchEvent(new CustomEvent("input", { bubbles: true }));
      emailField.dispatchEvent(new CustomEvent("blur", { bubbles: true }));
      expect([...emailErrorMessage.classList]).to.include("visible");

      ReminderDialog.prototype.showModal = () => {};

      let openDialogBtn = step.shadowRoot.querySelector("#open-reminder-dialog-button");
      openDialogBtn.click();
      expect([...emailErrorMessage.classList]).to.not.include("visible");

      expect(document.querySelector(".reminder-dialog")).to.exist;

      delete ReminderDialog.prototype.showModal;
    });
  });

  describe("email prefilling", () => {
    it("should not prefil if session storage is empty", async () => {
      sessionStorage.removeItem("switching-devices-email");

      // Prefilling the email address occurs when the element is bound
      // to the DOM, so we'll disconnect and reconnect.
      step.remove();
      $("body").append(step);

      let email = step.shadowRoot.querySelector("input[name=email]");
      let submitBtn = step.shadowRoot.querySelector("#submit");
      expect(email.value).to.be.empty;
      expect(submitBtn.disabled).to.be.true;
    });

    it("should not prefil if session storage is empty", async () => {
      const TEST_EMAIL = "test@test.com";
      sessionStorage.setItem("switching-devices-email", TEST_EMAIL);

      // Prefilling the email address occurs when the element is bound
      // to the DOM, so we'll disconnect and reconnect.
      step.remove();
      $("body").append(step);

      let email = step.shadowRoot.querySelector("input[name=email]");
      let submitBtn = step.shadowRoot.querySelector("#submit");
      expect(email.value).to.equal(TEST_EMAIL);
      expect(submitBtn.disabled).to.be.false;

      sessionStorage.removeItem("switching-devices-email");
    });
  });
});

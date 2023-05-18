import { expect } from "chai";
import { SignInStep } from "sumo/js/form-wizard-sign-in-step";

function assertFormElements(form, expectedElements) {
  for (let element of form.elements) {
    if (element.type == "submit") {
      continue;
    }

    expect(expectedElements[element.name], `Checking ${element.name}`).to.exist;
    expect(element.type).to.equal(expectedElements[element.name].type);
    expect(element.disabled).to.equal(expectedElements[element.name].disabled);
    expect(element.value).to.equal(expectedElements[element.name].value);
  }
}

describe("sign-in-step custom element", () => {
  let step;
  let slot;

  beforeEach(() => {
    step = new SignInStep();
    $("body")
      .empty()
      .append(step);
  });

  it("should render a sign-in-step custom element", () => {
    expect(step).to.exist;
    expect(step).to.be.an.instanceof(SignInStep);
  });

  it("should disable flow_id and flow_begin_time form fields if not yet supplied", () => {
    const TEST_STATE_NO_FLOW_METRICS = {
      utm_source: "utm_source",
      utm_campaign: "utm_campaign",
      utm_medium: "utm_medium",
      entrypoint: "entrypoint",
      entrypoint_experiment: "entrypoint_experiment",
      entrypoint_variation: "entrypoint_variation",
      context: "context",
      redirect_to: window.location.href,
      redirect_immediately: true,
    };

    const EXPECTED_FORM_ELEMENTS_NO_FLOW_METRICS = {
      utm_source: { type: "hidden", value: "utm_source", disabled: false },
      utm_campaign: { type: "hidden", value: "utm_campaign", disabled: false },
      utm_medium: { type: "hidden", value: "utm_medium", disabled: false },
      entrypoint: { type: "hidden", value: "entrypoint", disabled: false },
      entrypoint_experiment: { type: "hidden", value: "entrypoint_experiment", disabled: false },
      entrypoint_variation: { type: "hidden", value: "entrypoint_variation", disabled: false },
      context: { type: "hidden", value: "context", disabled: false },
      redirect_to: { type: "hidden", value: window.location.href, disabled: false },
      redirect_immediately: { type: "hidden", value: "true", disabled: false },

      service: { type: "hidden", value: "sync", disabled: false },
      action: { type: "hidden", value: "email", disabled: false },
      flow_id: { type: "hidden", value: "", disabled: true },
      flow_begin_time: { type: "hidden", value: "", disabled: true },
      email: { type: "email", value: "", disabled: false },
    };

    step.setState(TEST_STATE_NO_FLOW_METRICS);

    let form = step.shadowRoot.querySelector("form");
    assertFormElements(form, EXPECTED_FORM_ELEMENTS_NO_FLOW_METRICS);

    // Now add the flow metrics, which should enable the fields.

    const TEST_STATE_WITH_FLOW_METRICS = {
      ...TEST_STATE_NO_FLOW_METRICS,

      flow_id: "flow_id",
      flow_begin_time: "flow_begin_time",
    };

    const EXPECTED_FORM_ELEMENTS_WITH_FLOW_METRICS = {
      ...EXPECTED_FORM_ELEMENTS_NO_FLOW_METRICS,
      flow_id: { type: "hidden", value: "flow_id", disabled: false },
      flow_begin_time: { type: "hidden", value: "flow_begin_time", disabled: false },
    };

    step.setState(TEST_STATE_WITH_FLOW_METRICS);
    assertFormElements(form, EXPECTED_FORM_ELEMENTS_WITH_FLOW_METRICS);
  });

  it("should set an email address if one is set in the state", () => {
    const TEST_STATE = {
      utm_source: "utm_source",
      utm_campaign: "utm_campaign",
      utm_medium: "utm_medium",
      entrypoint: "entrypoint",
      entrypoint_experiment: "entrypoint_experiment",
      entrypoint_variation: "entrypoint_variation",
      context: "context",
      redirect_to: window.location.href,
      redirect_immediately: true,

      flow_id: "flow_id",
      flow_begin_time: "flow_begin_time",
      redirect_immediately: true,
      email: "test@test.com",
    };

    const EXPECTED_FORM_ELEMENTS = {
      utm_source: { type: "hidden", value: "utm_source", disabled: false },
      utm_campaign: { type: "hidden", value: "utm_campaign", disabled: false },
      utm_medium: { type: "hidden", value: "utm_medium", disabled: false },
      entrypoint: { type: "hidden", value: "entrypoint", disabled: false },
      entrypoint_experiment: { type: "hidden", value: "entrypoint_experiment", disabled: false },
      entrypoint_variation: { type: "hidden", value: "entrypoint_variation", disabled: false },
      context: { type: "hidden", value: "context", disabled: false },
      redirect_to: { type: "hidden", value: window.location.href, disabled: false },
      redirect_immediately: { type: "hidden", value: "true", disabled: false },

      service: { type: "hidden", value: "sync", disabled: false },
      action: { type: "hidden", value: "email", disabled: false },
      flow_id: { type: "hidden", value: "flow_id", disabled: false },
      flow_begin_time: { type: "hidden", value: "flow_begin_time", disabled: false },
      email: { type: "email", value: "test@test.com", disabled: false },
    };

    step.setState(TEST_STATE);

    let form = step.shadowRoot.querySelector("form");
    assertFormElements(form, EXPECTED_FORM_ELEMENTS);
  });

  it("should not overwrite email if input already has something in it", () => {
    const TEST_STATE = {
      utm_source: "utm_source",
      utm_campaign: "utm_campaign",
      utm_medium: "utm_medium",
      entrypoint: "entrypoint",
      entrypoint_experiment: "entrypoint_experiment",
      entrypoint_variation: "entrypoint_variation",
      context: "context",
      redirect_to: window.location.href,
      redirect_immediately: true,

      flow_id: "flow_id",
      flow_begin_time: "flow_begin_time",
      redirect_immediately: true,
      email: "",
    };

    const EXPECTED_FORM_ELEMENTS = {
      utm_source: { type: "hidden", value: "utm_source", disabled: false },
      utm_campaign: { type: "hidden", value: "utm_campaign", disabled: false },
      utm_medium: { type: "hidden", value: "utm_medium", disabled: false },
      entrypoint: { type: "hidden", value: "entrypoint", disabled: false },
      entrypoint_experiment: { type: "hidden", value: "entrypoint_experiment", disabled: false },
      entrypoint_variation: { type: "hidden", value: "entrypoint_variation", disabled: false },
      context: { type: "hidden", value: "context", disabled: false },
      redirect_to: { type: "hidden", value: window.location.href, disabled: false },
      redirect_immediately: { type: "hidden", value: "true", disabled: false },

      service: { type: "hidden", value: "sync", disabled: false },
      action: { type: "hidden", value: "email", disabled: false },
      flow_id: { type: "hidden", value: "flow_id", disabled: false },
      flow_begin_time: { type: "hidden", value: "flow_begin_time", disabled: false },
      email: { type: "email", value: "", disabled: false },
    };

    step.setState(TEST_STATE);

    let form = step.shadowRoot.querySelector("form");
    assertFormElements(form, EXPECTED_FORM_ELEMENTS);

    let emailField = form.querySelector("input[name=email]");
    emailField.value = "dont@overwrite.me";

    const TEST_STATE_WITH_EMAIL = {
      ...TEST_STATE,
      email: "unexpected@value.com",
    };

    const EXPECTED_FORM_ELEMENTS_WITH_EMAIL = {
      ...EXPECTED_FORM_ELEMENTS,
      email: { type: "email", value: "dont@overwrite.me", disabled: false },
    };

    step.setState(TEST_STATE_WITH_EMAIL);
    assertFormElements(form, EXPECTED_FORM_ELEMENTS_WITH_EMAIL);
  });

  it("should be in sign-up state if we didn't find a SUMO email, sign-in state otherwise", () => {
    const TEST_STATE_NO_EMAIL = {
      utm_source: "utm_source",
      utm_campaign: "utm_campaign",
      utm_medium: "utm_medium",
      entrypoint: "entrypoint",
      entrypoint_experiment: "entrypoint_experiment",
      entrypoint_variation: "entrypoint_variation",
      context: "context",
      redirect_to: window.location.href,
      redirect_immediately: true,

      flow_id: "flow_id",
      flow_begin_time: "flow_begin_time",
      redirect_immediately: true,
      email: "",
    };

    step.setState(TEST_STATE_NO_EMAIL);

    let root = step.shadowRoot.querySelector("#sign-in-step-root");
    expect(root.getAttribute("mode")).to.equal("sign-up");

    const TEST_STATE_WITH_EMAIL = {
      ...TEST_STATE_NO_EMAIL,
      email: "existing@user.com",
    };

    step.setState(TEST_STATE_WITH_EMAIL);
    expect(root.getAttribute("mode")).to.equal("sign-in");
  });

  it("should set the alternative links to linkHref", () => {
    const TEST_STATE = {
      utm_source: "utm_source",
      utm_campaign: "utm_campaign",
      utm_medium: "utm_medium",
      entrypoint: "entrypoint",
      entrypoint_experiment: "entrypoint_experiment",
      entrypoint_variation: "entrypoint_variation",
      context: "context",
      redirect_to: window.location.href,
      redirect_immediately: true,

      flow_id: "flow_id",
      flow_begin_time: "flow_begin_time",
      redirect_immediately: true,
      email: "",

      linkHref: "https://expected-url.com/",
    };

    step.setState(TEST_STATE);

    let links = step.shadowRoot.querySelectorAll(".alternative-link");
    expect(links.length).to.equal(2);
    for (let link of links) {
      expect(link.href).to.equal("https://expected-url.com/")
    }
  });

  describe("form valdiation", () => {
    let form;
    let submitBtn;
    let emailField;
    let emailErrorMessage;

    beforeEach(() => {
      form = step.shadowRoot.querySelector("form");
      submitBtn = form.querySelector("button[type=submit]");
      emailField = form.querySelector("input[name=email]");
      emailErrorMessage = form.querySelector("#email-error");
    });

    it("should display an error message if an email address is not supplied", () => {
      expect([...emailErrorMessage.classList]).to.include("hidden");

      emailField.value = "";
      submitBtn.click();

      expect(emailField.validity.valid).to.be.false;
      expect([...emailErrorMessage.classList]).to.not.include("hidden");
      expect(emailErrorMessage.textContent).to.equal("Valid email required");
    });

    it("should display an error message if an incomplete email address is supplied", () => {
      expect([...emailErrorMessage.classList]).to.include("hidden");

      emailField.value = "this-is-not-an-email-address";
      submitBtn.click();

      expect(emailField.validity.valid).to.be.false;
      expect([...emailErrorMessage.classList]).to.not.include("hidden");
      expect(emailErrorMessage.textContent).to.equal("Valid email required");
    });

    it("should submit the form when a valid email address is supplied", async () => {
      // Prevent the form from actually submitting.
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

      emailField.value = "email@email.com";
      submitBtn.click();
      await preventSubmitListener;

      expect(emailField.validity.valid).to.be.true;
      expect([...emailErrorMessage.classList]).to.include("hidden");
    });
  });
});

import { expect } from "chai";
import { FormWizard } from "sumo/js/form-wizard";

describe("form-wizard custom element", () => {
  let wizard;
  let slot;

  beforeEach(() => {
    $("body").empty().html(`
        <form-wizard>
            <div name="first">
                <p>This is the first step.</p>
            </div>
            <div name="second">
                <p>This is the second step.</p>
            </div>
            <div name="third">
                <p>This is the third step.</p>
            </div>
        </form-wizard>
    `);
    wizard = document.querySelector("form-wizard");
    slot = wizard.shadowRoot.querySelector('slot[name="active"]');
  });

  it("should render a form-wizard custom element", () => {
    expect(wizard).to.exist;
    expect(wizard).to.be.an.instanceof(FormWizard);
  });

  it("should show the first step by default", () => {
    let assignedElements = slot.assignedElements();
    let activeStep = assignedElements[0];
    expect(assignedElements.length).to.equal(1);
    expect(activeStep.getAttribute("name")).to.equal("first");
    expect(activeStep.textContent.trim()).to.equal("This is the first step.");
  });

  describe("step change behavior", () => {
    const INITIAL_STEPS = [
      { name: "first", status: "active", label: "First label" },
      { name: "second", status: "unavailable", label: "Second label" },
      { name: "third", status: "unavailable", label: "Third label" },
    ];

    // Reset the active step before each test in this block.
    beforeEach(() => {
      wizard.steps = INITIAL_STEPS;
    });

    it("should show a different step when the active step changes", () => {
      wizard.setStep("second", {});
      let assignedElements = slot.assignedElements();
      let activeStep = assignedElements[0];
      expect(assignedElements.length).to.equal(1);
      expect(activeStep.getAttribute("name")).to.equal("second");
      expect(activeStep.textContent.trim()).to.equal(
        "This is the second step."
      );
    });

    it("should show a progress bar that updates when the active step changes", () => {
      let progress = wizard.shadowRoot.querySelector("progress");
      expect(progress).to.exist;
      expect(progress.value).to.equal(10);

      wizard.activeStep = "second";
      expect(progress.value).to.equal(50);

      wizard.activeStep = "third";
      expect(progress.value).to.equal(100);
    });

    it("should show an indicator of how many steps are in the form", () => {
      let indicator = wizard.shadowRoot.getElementById("step-indicator");
      let steps = indicator.children;
      expect(indicator).to.exist;
      expect(steps.length).to.equal(INITIAL_STEPS.length);
      [...steps].forEach((step, i) => {
        let subtitle = step.querySelector(".subtitle");
        let title = step.querySelector(".title");
        expect(step.getAttribute("status")).to.equal(INITIAL_STEPS[i].status);
        expect(subtitle.textContent).to.equal(`Step ${i + 1}`);
        expect(title.textContent).to.equal(INITIAL_STEPS[i].label);
      });
    });

    it("should update the statuses of the steps when the active step changes", () => {
      let indicator = wizard.shadowRoot.getElementById("step-indicator");
      let steps = indicator.children;
      expect(steps[0].getAttribute("status")).to.equal("active");
      expect(steps[1].getAttribute("status")).to.equal("unavailable");

      wizard.setStep("second", {});

      expect(steps[0].getAttribute("status")).to.equal("done");
      expect(steps[1].getAttribute("status")).to.equal("active");
    });

    describe("form wizard `setStep` method", () => {
      it("should update 'unavailable' steps to 'active' update step data", () => {
        const EXPECTED_STEPS = [
          { name: "first", status: "done", label: "First label" },
          {
            name: "second",
            status: "active",
            label: "Second label",
            foo: "bar",
          },
          { name: "third", status: "unavailable", label: "Third label" },
        ];
        expect(wizard.steps).to.deep.equal(INITIAL_STEPS);
        wizard.setStep("second", { foo: "bar" });
        expect(wizard.steps).to.deep.equal(EXPECTED_STEPS);
      });

      it("should update data for 'active' steps", () => {
        const EXPECTED_STEPS = [
          { name: "first", status: "active", label: "First label", foo: "bar" },
          { name: "second", status: "unavailable", label: "Second label" },
          { name: "third", status: "unavailable", label: "Third label" },
        ];
        expect(wizard.steps).to.deep.equal(INITIAL_STEPS);
        wizard.setStep("first", { foo: "bar" });
        expect(wizard.steps).to.deep.equal(EXPECTED_STEPS);
      });

      it("should update data for 'done' steps without changing the 'active' step", () => {
        const TEST_STEPS = [
          { name: "first", status: "done", label: "First label" },
          { name: "second", status: "done", label: "Second label" },
          { name: "third", status: "active", label: "Third label" },
        ];
        const EXPECTED_STEPS = [
          { name: "first", status: "done", label: "First label" },
          { name: "second", status: "done", label: "Second label" },
          {
            name: "third",
            status: "active",
            label: "Third label",
            foo: "bar",
          },
        ];
        wizard.steps = TEST_STEPS;
        wizard.setStep("third", { foo: "bar" });
        expect(wizard.steps).to.deep.equal(EXPECTED_STEPS);
      });
    });
  });
});

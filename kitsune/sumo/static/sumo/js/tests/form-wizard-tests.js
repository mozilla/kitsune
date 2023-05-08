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

  it("should show a different step when the active step changes", () => {
    wizard.activeStep = "second";
    let assignedElements = slot.assignedElements();
    let activeStep = assignedElements[0];
    expect(assignedElements.length).to.equal(1);
    expect(activeStep.getAttribute("name")).to.equal("second");
    expect(activeStep.textContent.trim()).to.equal("This is the second step.");
  });
});

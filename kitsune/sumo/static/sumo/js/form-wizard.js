/**
 * A custom element for displaying multi-step forms.
 *
 * Uses a named slot and "#activeStep" state to determine which step of the form
 * should be shown. All child elements where the "name" attribute doesn't match
 * the "#activeStep" will not be assigned to the named slot.
 *
 */
export class FormWizard extends HTMLElement {
  #steps = null;
  #activeStep = null;

  constructor() {
    super();
    let shadow = this.attachShadow({ mode: "open" });
    let activeSlot = document.createElement("slot");
    activeSlot.setAttribute("name", "active");
    shadow.appendChild(activeSlot);
  }

  connectedCallback() {
    if (this.activeStep) {
      // Make sure the active step is shown.
      this.#setActiveStepAttributes();
    } else {
      // If there's no active step, default to the first step.
      this.activeStep = this.firstElementChild?.getAttribute("name");
    }
  }

  get activeStep() {
    return this.#activeStep;
  }

  set activeStep(name) {
    this.#activeStep = name;
    this.#setActiveStepAttributes();
  }

  get steps() {
    return this.#steps;
  }

  set steps(nextSteps) {
    this.#steps = nextSteps;
    this.activeStep = nextSteps.find((step) => step.status === "active")?.name;
  }

  /**
   * Set the slot attribute on all children to ensure only
   * the active step is shown.
   */
  #setActiveStepAttributes() {
    let { activeStep } = this;
    for (let step of this.children) {
      let name = step.getAttribute("name");
      if (name === activeStep) {
        step.slot = "active";
      } else {
        step.slot = "";
      }
    }
  }
}
customElements.define("form-wizard", FormWizard);

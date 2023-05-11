/**
 * A custom element for displaying multi-step forms.
 *
 * Uses a named slot and `#activeStep` state to determine which step of the form
 * wizard should be shown. All child elements where the `name` attribute doesn't
 * match the `#activeStep` will not be assigned to the named slot.
 *
 * Can be initialized with step data via the `steps` setter.
 *
 * wizard.steps = [ 
 *  { name: "first", status: "done", label: "foo" },
 *  { name: "second", status: "active", label: "bar" },
 *  { name: "third", status: "unavailable", label: "baz" },
 * ];
 *
 * The active step can be changed by calling `setStep` and passing in a step
 * name along with new data representing that step.
 *
 * wizard.setStep("third", { name: "third", status: "active", label: "baz" });
 *
 */
export class FormWizard extends HTMLElement {
  #activeStep = null;
  #progressIndicator = null;
  #stepIndicator = null;
  #steps = [];

  static get markup() {
    return `
      <template>
        <div>
          <h2>${gettext("Wizard header")}</h2>
          <section>
            <ul id="step-indicator"></ul>
            <slot name="active"></slot>
          </section>
          <footer>
            <progress max="100" value="0"></progress>
          </footer>
        </div>
      </template>
    `;
  }

  constructor() {
    super();
    let shadow = this.attachShadow({ mode: "open" });

    let parser = new DOMParser();
    let doc = parser.parseFromString(FormWizard.markup, "text/html");
    let template = doc.querySelector("template");
    shadow.appendChild(template.content.cloneNode(true));

    this.#progressIndicator = shadow.querySelector("progress");
    this.#stepIndicator = shadow.getElementById("step-indicator");
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
    this.#updateFormProgress();
  }

  /**
   * @typedef {object} FormWizardStep
   * @property {string} name
   *  The name of the step. Used as an identifier to determine which
   *  child view should be shown and help determine how far the user
   *  has progressed through the form.
   * @property {string} status
   *  Status of the step. One of "done" | "active" | "unavailable".
   *  Used to hide/show steps and update the step indicator.
   * @property {string} label
   *  Label for the form step to be shown in the step indicator.
   */

  /**
   * Stores the possible form step names and associated data.
   *
   * @param {FormWizardStep[]} nextSteps
   *  Step data representing the desired state of the wizard.
   */
  set steps(nextSteps) {
    this.#steps = nextSteps;
    // Determine whether or not we need to update activeStep.
    let nextActiveStep = nextSteps.find(
      (step) => step.status === "active"
    )?.name;
    if (nextActiveStep) {
      this.activeStep = nextActiveStep;
    }
    // Build or update the steps sidebar.
    this.#updateStepIndicator();
  }

  get steps() {
    return this.#steps;
  }

  /**
   * Updates data for the step specified by name and/or changes the currently
   * active step. Active step only changes when the step getting updated is
   * currently "unavailable".
   *
   * @param {string} name - Name of the step to be updated.
   * @param {FormWizardStep} data - Data to update the step with.
   */
  setStep(name, data) {
    let currentStatus = this.#steps.find((step) => step.name === name)?.status;
    let isUnavailable = currentStatus === "unavailable";
    let nextSteps = this.#steps.map((step) => {
      if (step.status === "active" && isUnavailable) {
        return { ...step, status: "done" };
      } else if (step.name === name && isUnavailable) {
        return { ...step, ...data, status: "active" };
      } else if (step.name === name) {
        return { ...step, ...data };
      }
      return step;
    });
    this.steps = nextSteps;
  }

  // To be implemented as part of mozilla/sumo #1274.
  disqualify(header, text) {
    // NOOP
  }

  /**
   * Populates the step indicator the first time step data is passed in,
   * otherwise updates the statuses of the steps.
   */
  #updateStepIndicator() {
    if (!this.#stepIndicator.children.length) {
      this.#steps.forEach(({ name, status, label }, index) => {
        let item = document.createElement("li");
        item.setAttribute("id", name);
        item.setAttribute("status", status);

        let subtitle = document.createElement("p");
        subtitle.classList.add("subtitle");
        subtitle.textContent = `Step ${index + 1}`;
        item.appendChild(subtitle);

        let title = document.createElement("p");
        title.classList.add("title");
        title.textContent = gettext(label);
        item.appendChild(title);

        this.#stepIndicator.appendChild(item);
      });
    } else {
      this.#steps.forEach((step) => {
        let indicator = this.shadowRoot.getElementById(step.name);
        indicator.setAttribute("status", step.status);
      });
    }
  }

  /**
   * Update the value of the progress element to show form completion.
   * Defaults to 10% for the first step.
   */
  #updateFormProgress() {
    if (this.#steps?.length) {
      let activeStepIndex = this.#steps.findIndex(
        ({ name }) => name === this.activeStep
      );
      let progress =
        Math.ceil((activeStepIndex / (this.#steps.length - 1)) * 100) || 10;
      this.#progressIndicator.value = progress;
    }
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

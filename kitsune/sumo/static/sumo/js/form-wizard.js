/**
 * A custom element for displaying multi-step forms.
 *
 * Uses a named slot and "#activeStep" state to determine which step of the form
 * should be shown. All child elements where the "name" attribute doesn't match
 * the "#activeStep" will not be assigned to the named slot.
 *
 */
export class FormWizard extends HTMLElement {
  #activeStep = null;
  #progressIndicator = null;
  #steps = [];

  static get markup() {
    return `
      <template>
        <div>
          <h2>${gettext("Wizard header")}</h2>
          <section>
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

    this.#updateSteps();
    this.observer = new MutationObserver(() => {
      this.#updateSteps();
    });
  }

  connectedCallback() {
    if (this.activeStep) {
      // Make sure the active step is shown.
      this.#setActiveStepAttributes();
    } else {
      // If there's no active step, default to the first step.
      this.activeStep = this.firstElementChild?.getAttribute("name");
    }
    this.observer.observe(this, { childList: true });
  }

  disconnectedCallback() {
    this.observer.disconnect();
  }

  get activeStep() {
    return this.#activeStep;
  }

  set activeStep(name) {
    this.#activeStep = name;
    this.#setActiveStepAttributes();
    this.#updateFormProgress();
  }

  #updateSteps() {
    this.#steps = [...this.children].map((child) => child.getAttribute("name"));
    this.#updateFormProgress();
  }

  /**
   * Update the value of the progress element to show form completion.
   * Defaults to 10% for the first step.
   */
  #updateFormProgress() {
    if (this.#steps?.length) {
      let activeStepIndex = this.#steps.indexOf(this.activeStep);
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

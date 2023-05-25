import wizardStylesURL from "../scss/form-wizard.styles.scss";
import formStepStylesURL from "../scss/form-step.styles.scss";
import warningImageURL from "sumo/img/warning.svg";

/**
 * A custom element for displaying multi-step forms. Designed to be used with
 * child elements that inherit from `BaseFormStep`, or which implement a
 * `setState` method for receiving updates.
 *
 * Uses a named slot and `#activeStep` state to determine which step of the form
 * wizard should be shown. All child elements where the `name` attribute doesn't
 * match the `#activeStep` will not be assigned to the named slot.
 *
 * Can be initialized with step data via the `steps` setter:
 *
 * wizard.steps = [
 *  { name: "first", status: "done", label: "foo" },
 *  { name: "second", status: "active", label: "bar" },
 *  { name: "third", status: "unavailable", label: "baz" },
 * ];
 *
 * The active step can be changed by calling `setStep`. Any `data` passed into
 * `setStep` will be passed along to the intended child by calling that
 * element's `setState` method.
 *
 * wizard.setStep("third", { foo: "bar", someState: true });
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
        <div class="form-wizard-root">
          <div class="form-wizard-content">
            <h2>${gettext("Setup assistant")}</h2>
            <section>
              <ul id="step-indicator"></ul>
              <slot name="active"></slot>
            </section>
          </div>
          <progress max="100" value="0"></progress>
          <div class="form-wizard-disqualified">
            <div class="disqualification" reason="need-fx-desktop">
              <span class="disqualification-header"><img class="warning-icon" src="${warningImageURL}" aria-hidden="true"/>${gettext("Use Firefox to continue")}</span>
              <div class="disqualification-message">${gettext("To use the setup assistant or access the settings for backing up your Firefox data, visit this page using Firefox on a desktop device.")}</div>
            </div>

            <div class="disqualification" reason="uitour-broken">
              <div class="disqualification-message">
                ${interpolate(
                  gettext("The setup assistant is currently unavailable for your version of Firefox. However, you can still perform a manual backup of your data by following the steps outlined in <a href='%s'>this article.</a>"),
                  ["/kb/profile-manager-create-remote-switch-firefox-profiles"]
                )}
              </div>
            </div>
          </div>
        </div>
      </template>
    `;
  }


  static get styles() {
    let stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = wizardStylesURL;
    return stylesheet;
  }

  constructor() {
    super();
    let shadow = this.attachShadow({ mode: "open" });

    let parser = new DOMParser();
    let doc = parser.parseFromString(FormWizard.markup, "text/html");
    let template = doc.querySelector("template");
    shadow.append(FormWizard.styles, template.content.cloneNode(true));

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
   * @param {object} data - Data to update the step with.
   */
  setStep(name, data) {
    // Find the step getting updated and set its state.
    let formStep = this.getRootNode().querySelector(`[name="${name}"]`);
    formStep.setState(data);

    // Determine if the statuses of the steps need to change.
    let currentStatus = this.#steps.find((step) => step.name === name)?.status;
    let isUnavailable = currentStatus === "unavailable";
    let nextSteps = this.#steps.map((step) => {
      if (step.status === "active" && isUnavailable) {
        return { ...step, status: "done" };
      } else if (step.name === name && isUnavailable) {
        return { ...step, status: "active" };
      }
      return step;
    });
    this.steps = nextSteps;
  }

  /**
   * Puts the form-wizard into the "disqualified" state with a particular
   * message. The messages are defined in the markup and displayed when their
   * reason attribute matches "reason".
   *
   * @param {string} reason
   *   A string that matches the reason attribute on the disqualification message
   *   to display.
   */
  disqualify(reason) {
    let disqualified = this.shadowRoot.querySelector(".form-wizard-disqualified");
    for (let child of disqualified.children) {
      child.toggleAttribute("active", child.getAttribute("reason") === reason);
    }

    let root = this.shadowRoot.querySelector(".form-wizard-root");
    root.toggleAttribute("disqualified", true);
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

/**
 * Base class that defines the basic re-rendering logic for form steps.
 * The`template` getter can be overridden to provide custom markup. The `render`
 * method can be overridden to define custom logic for how the DOM updates when
 * state changes.
 */
export class BaseFormStep extends HTMLElement {
  #state = {};

  /**
   * Provides markup for the form step. Default markup is not provided since
   * `BaseFormStep` should never be used directly.
   */
  get template() {
    throw new Error("template must be implemented.");
  }

  /**
   * Provides styles that are common to all form steps, mainly selected Protocol
   * styles and components.
   */
  get defaultStyles() {
    let stylesheet = document.createElement("link");
    stylesheet.rel = "stylesheet";
    stylesheet.href = formStepStylesURL;
    return stylesheet;
  }

  /**
   * Provides a <link> element to be injected into the shadow DOM at construction
   * time. Subclasses that need custom styles should override this.
   */
  get styles() {
    return document.createElement("link");
  }

  constructor() {
    super();
    this.attachShadow({ mode: "open" });

    let parser = new DOMParser();
    let doc = parser.parseFromString(this.template, "text/html");
    let template = doc.querySelector("template");
    this.shadowRoot.append(
      this.defaultStyles,
      this.styles,
      template.content.cloneNode(true)
    );

    this.render({}, this.#state);
  }

  get state() {
    return this.#state;
  }

  /**
   * Updates the element's state and tells the element to re-render.
   *
   * @param {object} nextState
   */
  setState(nextState) {
    let prevState = Object.assign({}, this.#state);
    this.#state = Object.assign(this.#state, nextState);
    this.render(prevState, this.#state);
  }

  /**
   * Method that gets run whenever the element's state changes. Can be used to
   * specify how the DOM should update in response to state changes. `prevState`
   * and `nextState` are provided for making comparisons.
   * 
   * This must be implemented in the subclass if the form step needs to respond
   * to state updates.
   *
   * @param {object} prevState
   *  The element's state before the most recent update.
   * @param {object} nextState The element's current state.
   */
  render(prevState, nextState) {
    // NOOP
  }
}

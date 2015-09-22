/* globals React:false */
import scrollTo from '../../../sumo/js/utils/scrollTo.es6.js';

export default class AAQStep extends React.Component {
  render() {
    let heading = this.heading();
    return (
      <div className="AAQApp__Step highlight-box">
        {heading
          ? <h2>{heading}</h2>
          : null}
        {this.shouldExpand()
          ? this.body()
          : null}
      </div>
    );
  }

  shouldExpand() {
    return true;
  }

  heading() {
    return null;
  }

  body() {
    return null;
  }

  scrollToNextStep() {
    let currentStep = React.findDOMNode(this); // will throw if not mounted
    let nextStep = currentStep.nextElementSibling;
    if (nextStep === null) {
      throw 'Tried to call scrollToNextStep(), but this is the last step.';
    }
    if (!nextStep.classList.contains('AAQApp__Step')) {
      throw 'Tried to call scrollToNextStep(), but the next element is not an AAQStep.';
    }
    scrollTo(nextStep);
  }
}
AAQStep.propTypes = {
  question: React.PropTypes.object.isRequired,
};

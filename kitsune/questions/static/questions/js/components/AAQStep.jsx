/* globals React:false */
import scrollTo from '../../../sumo/js/utils/scrollTo.es6.js';

export default class AAQStep extends React.Component {
  render() {
    let heading = this.heading();
    let style = {
      display: this.visible() ? 'block' : 'none'
    };
    return (
      <div className="AAQApp__Step" style={style}>
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

  visible(){
    return false;
  }

  switchToNextStep() {
    let currentStep = React.findDOMNode(this); // will throw if not mounted
    let nextStep = currentStep.nextElementSibling;
    if (nextStep === null) {
      throw 'Tried to call switchToNextStep(), but this is the last step.';
    }
    if (!nextStep.classList.contains('AAQApp__Step')) {
      throw 'Tried to call switchToNextStep(), but the next element is not an AAQStep.';
    }
    nextStep.style.display = 'block';
    currentStep.style.display = 'none';
    scrollTo(nextStep);
  }
}
AAQStep.propTypes = {
  question: React.PropTypes.object.isRequired,
};

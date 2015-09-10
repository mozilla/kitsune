/* globals React:false */
import scrollTo from '../../../sumo/js/utils/scrollTo.es6.js';

export default class AAQStep extends React.Component {
  render() {
    let heading = this.heading();
    return (
      <div className="AAQApp__Step">
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

  switchToNextStep() {
    this.props.setStep(this.props.next);
  }
}
AAQStep.propTypes = {
  question: React.PropTypes.object.isRequired
};

/* globals React:false */
import AAQActions from '../actions/AAQActions.es6.js';
import scrollTo from '../../../sumo/js/utils/scrollTo.es6.js';
import UrlStore from '../../../sumo/js/stores/UrlStore.es6.js';

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

  setPropsFromUrl() {
    let urlData = UrlStore.get('pathProps');
    if (urlData.product) {
      AAQActions.setProduct(urlData.product);
    }
    if (urlData.topic) {
      AAQActions.setTopic(urlData.topic);
    }
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
    this.props.setStep();
  }
}
AAQStep.propTypes = {
  question: React.PropTypes.object.isRequired
};

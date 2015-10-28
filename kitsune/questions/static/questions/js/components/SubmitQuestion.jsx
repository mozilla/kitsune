/* globals React:false */
import cx from 'classnames';
import AAQStep from './AAQStep.jsx';
import AAQActions from '../actions/AAQActions.es6.js';
import {questionEditState} from '../constants/AAQConstants.es6.js';
import {authStates} from '../../../users/js/constants/UserAuthConstants.es6.js';
import {aaqGa} from '../utils/';

export default class SubmitQuestion extends AAQStep {
  handleSubmit() {
    if (this.enabled()) {
      aaqGa.trackEvent('question submitted');
      AAQActions.submitQuestion();
    } else {
      // TODO: Show help
    }
  }

  enabled() {
    return this.props.questionState === questionEditState.VALID &&
      this.props.userAuth.state === authStates.LOGGED_IN;
  }

  render() {
    let buttonTexts = {
      [questionEditState.INVALID]: 'Submit',
      [questionEditState.VALID]: 'Submit',
      [questionEditState.PENDING]: 'Submitting...',
      [questionEditState.SUBMITTED]: 'Done!',
      [questionEditState.ERROR]: 'Error!',
    };

    return (
      <div>
        <button className={cx('btn', 'btn-submit', 'big', {disabled: !this.enabled()})}
                onClick={this.handleSubmit.bind(this)}>
          {buttonTexts[this.props.questionState]}
        </button>
      </div>
    );
  }
}

SubmitQuestion.propTypes = {
  question: React.PropTypes.object.isRequired,
  questionState: React.PropTypes.object.isRequired,
  validationErrors: React.PropTypes.object.isRequired,
  userAuth: React.PropTypes.object.isRequired,
};

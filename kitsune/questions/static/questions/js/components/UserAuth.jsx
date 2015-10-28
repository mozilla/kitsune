/* globals React:false */
import AAQStep from './AAQStep.jsx';
import UserAuthActions from '../../../users/js/actions/UserAuthActions.es6.js';
import {authStates} from '../../../users/js/constants/UserAuthConstants.es6.js';
import LoginForm from '../../../users/js/components/LoginForm.jsx';
import RegisterForm from '../../../users/js/components/RegisterForm.jsx';
import {aaqGa} from '../utils/';

export default class UserAuth extends AAQStep {
  constructor(props) {
    super(props);
  }

  componentDidMount() {
    UserAuthActions.checkAuthState()
    .then(authState => {
      if (authState === authStates.LOGGED_OUT) {
        UserAuthActions.showRegister();
      } else if (authState === authStates.LOGGED_IN) {
        aaqGa.trackEvent('preregistered');
      }
    });
  }

  heading() {
    const messages = {
      [authStates.LOGGED_IN]: `Signed in as ${this.props.userAuth.username}`,
      [authStates.REGISTERING]: 'Almost there! We just need to create a support forum account!',
      [authStates.LOGGING_IN]: 'Log in to an existing account',
    };

    let message = messages[this.props.userAuth.state] || '';
    if (this.props.userAuth.pending) {
      message += ' (pending)';
    }

    return message;
  }

  body() {
    if (this.props.userAuth.state === authStates.REGISTERING) {
      return <RegisterForm userAuth={this.props.userAuth}/>;
    } else if (this.props.userAuth.state === authStates.LOGGING_IN) {
      return <LoginForm userAuth={this.props.userAuth}/>;
    } else {
      return null;
    }
  }
}
UserAuth.propTypes = {
  userAuth: React.PropTypes.object.isRequired,
};

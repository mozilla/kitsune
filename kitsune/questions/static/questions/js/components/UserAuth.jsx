/* globals React:false */
import AAQStep from './AAQStep.jsx';

export default class UserAuth extends AAQStep {
  constructor(props) {
    super(props);
    this.state = {
      signingIn: false,
    };
  }

  heading() {
    if (this.props.loggedIn) {
      return `Signed in as ${this.props.username}`;
    } else {
      return 'Not signed in';
    }
  }
}

UserAuth.propTypes = {
  loggedIn: React.PropTypes.bool.isRequired,
};

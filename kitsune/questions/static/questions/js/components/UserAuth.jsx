/* globals React:false */
import AAQStep from './AAQStep.jsx';
import UserAuthActions from '../../../users/js/actions/UserAuthActions.es6.js';

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
      return 'Almost there! We just need to create a support forum account!';
    }
  }

  body() {
    if (this.props.loggedIn) {
      return null;
    }
    if (this.state.signingIn) {
      // return <LoginForm/>;
    } else {
      return <RegisterForm/>;
    }
  }
}
UserAuth.propTypes = {
  loggedIn: React.PropTypes.bool.isRequired,
};

class RegisterForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      username: '',
      email: '',
      password: '',
    };
  }

  handleChange({target: {name, value}}) {
    this.setState({[name]: value});
  }

  showLoginForm(ev) {
    ev.preventDefault();
    UserAuthActions.setAuthState('loggingIn');
  }

  render() {
    return (
      <div id="register-form">
        <h4>Having an account on the support forums lets us notify you when you get a response on your question.</h4>
        <form>
          <ul>
            <li data-validate-url="/en-US/users/validate-field" data-validate-extra='["email"]' data-valid-label="This email looks great!">
              <label htmlFor="email">Email address:</label>
              <input type="email" name="email" value={this.state.email} onChange={this.handleChange.bind(this)}/>
              <div className="validation-label"/>
            </li>
            <li data-validate-url="/en-US/users/validate-field" data-validate-label="This username is available.">
              <label htmlFor="username">Username:</label>
              <input type="text" name="username" value={this.state.username} onChange={this.handleChange.bind(this)}/>
              <div className="validation-label"/>
              <p id="username-rules">
                Your username will be shown next to your question in our public support forums.
              </p>
            </li>
            <li>
              <label htmlFor="password">Password:</label>
              <input type="password" name="password" value={this.state.password} onChange={this.handleChange.bind(this)}/>
              <div className="validation-label"/>
              <p id="password-rules">
                Password should be at least 8 characters long and contain at least 1 number.
              </p>
            </li>
          </ul>
          <p>
            <input id="show-password" type="checkbox"/>{' '}
            <label htmlFor="show-password">Reveal password to check that it's right.</label>
          </p>
          <div className="submit">
            <button className="btn btn-submit" type="submit">Create my account</button>
            <a href="#" onClick={this.showLoginForm.bind(this)}>
              I already have an account
            </a>
          </div>
        </form>
      </div>
    );
  }
}

/* globals React:false */
import UserAuthActions from '../actions/UserAuthActions.es6.js';
import {authStates} from '../constants/UserAuthConstants.es6.js';
import {Errors} from './AuthCommon.jsx';
import userGa from '../utils/userGa.es6.js';

/* A form that can register users. Users that are registered are
 * automatically logged in. */
export default class RegisterForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      username: '',
      email: '',
      password: '',
      showPassword: false,
    };
  }

  handleChange({target: {name, value}}) {
    userGa.trackEventOnce(`${name} input`);
    this.setState({[name]: value});
  }

  showLoginForm(ev) {
    ev.preventDefault();
    userGa.trackEvent('login requested');
    UserAuthActions.showLogin();
  }

  register(ev) {
    ev.preventDefault();
    UserAuthActions.register(this.state.username, this.state.email, this.state.password)
    .then(() => {
      UserAuthActions.login(this.state.username, this.state.password, {inactive: true});
    });
  }

  showPassword({target: {checked}}) {
    if (checked) {
      userGa.trackEvent('show password selected');
    }
    this.setState({showPassword: checked});
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
            <li data-validate-url="/en-US/users/validate-field" data-valid-label="This username is available.">
              <label htmlFor="username">Username:</label>
              <input type="text" name="username" value={this.state.username} onChange={this.handleChange.bind(this)}/>
              <div className="validation-label"/>
              <p id="username-rules">
                Your username will be shown next to your question in our public support forums.
              </p>
            </li>
            <li>
              <label htmlFor="password">Password:</label>
              <input
                name="password"
                type={this.state.showPassword ? 'text': 'password'}
                value={this.state.password}
                onChange={this.handleChange.bind(this)}/>
              <div className="validation-label"/>
              <p id="password-rules">
                Password should be at least 8 characters long and contain at least 1 number.
              </p>
            </li>
          </ul>
          <p>
            <input type="checkbox" onClick={this.showPassword.bind(this)}/>{' '}
            <label htmlFor="show-password">Reveal password to check that it's right.</label>
          </p>
          <div className="submit">
            <button className="btn btn-submit" type="submit" onClick={this.register.bind(this)}>Create my account</button>
            <a href="#" onClick={this.showLoginForm.bind(this)}>
              I already have an account
            </a>
            {this.props.userAuth.pending ? 'pending...' : null}
            <Errors errors={this.props.userAuth.errors}/>
          </div>
        </form>
      </div>
    );
  }
}

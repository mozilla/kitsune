/* globals React:false */
import UserAuthActions from '../actions/UserAuthActions.es6.js';
import {authStates} from '../constants/UserAuthConstants.es6.js';
import {Errors} from './AuthCommon.jsx';

export default class LoginForm extends React.Component {
  constructor(props) {
    super(props);
    this.state = {
      username: '',
      password: '',
    };
  }

  handleChange({target: {name, value}}) {
    this.setState({[name]: value});
  }

  showRegisterForm(ev) {
    ev.preventDefault();
    UserAuthActions.showRegister();
  }

  login(ev) {
    ev.preventDefault();
    UserAuthActions.login(this.state.username, this.state.password);
  }

  render() {
    return (
      <div id="login-form" style={{display: 'block'}}>
        <form>
          <fieldset>
            <ul>
              <li className="cf">
                <label for="username">Username:</label>
                <input maxlength="254" name="username" required="required" type="text" onChange={this.handleChange.bind(this)}/>
              </li>
              <li className="cf">
                <label for="password">Password:</label>
                <input name="password" required="required" type="password" onChange={this.handleChange.bind(this)}/>
              </li>
            </ul>
            <div className="submit">
              <button type="submit" className="btn btn-submit" onClick={this.login.bind(this)}>
                Log in
              </button>
            </div>
          </fieldset>
        </form>
        <Errors errors={this.props.userAuth.errors}/>
        <div id="login-help">
          <a id="reset_password" target="_blank" href="/en-US/users/pwreset">My password isn't working.</a>
        </div>
        <div>
          <a href="#" onClick={this.showRegisterForm.bind(this)}>Create a new account instead.</a>
        </div>
      </div>
    );
  }
}
LoginForm.propTypes = {
  userAuth: React.PropTypes.object.isRequired,
};

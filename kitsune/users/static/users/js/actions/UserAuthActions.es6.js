/* globals $:false */
import apiFetch, {apiFetchRaw} from '../../../sumo/js/utils/apiFetch.es6.js';
import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import {actionTypes} from '../constants/UserAuthConstants.es6.js';
import UserAuthStore from '../stores/UserAuthStore.es6.js';
import userGa from '../utils/userGa.es6.js';

export function checkAuthState() {
  return apiFetchRaw('/api/1/users/test_auth', {
    credentials: 'include',
  })
  .then(res => {
    return res.json().then(data => [res.status, data]);
  })
  .then(([status, data]) => {
    if (status === 200) {
      let username = data.username;
      return apiFetch(`/api/2/user/${username}/`, {
        method: 'GET',
      })
      .then(user => {
        Dispatcher.dispatch({
          type: actionTypes.AUTH_LOG_IN_SUCCESS,
          id: user.id,
          username,
        });
      });
    } else if (status === 401) {
      Dispatcher.dispatch({
        type: actionTypes.AUTH_LOG_OUT,
      });
    } else {
      throw new Error(`Unexpected response from test_auth: ${status}: ${JSON.stringify(data)}`);
    }
  }).then(function() {
    return UserAuthStore.getState();
  });
}

export function login(username, password, {inactive=false}={}) {
  const csrfElem = document.querySelector('input[name=csrfmiddlewaretoken]');
  const csrf = csrfElem ? csrfElem.value : null;

  Dispatcher.dispatch({
    type: actionTypes.AUTH_LOG_IN_OPTIMISTIC,
  });

  $.post('/en-US/users/login', {
    username: username,
    password: password,
    login: 1,
    csrfmiddlewaretoken: csrf,
    inactive: inactive ? '1' : '0',
  })
  .done((data, textStatus, jqXHR) => {
    /* Since we loaded another page, we need to use the new page's CSRF
     * token. */
    let newDoc = $(data.trim());
    let newCsrfElem = newDoc.find('input[name=csrfmiddlewaretoken]')[0];
    if (newCsrfElem && csrfElem) {
      csrfElem.value = newCsrfElem.value;
    } else {
      console.error("No new csrf value found! This probably won't end well!");
    }

    if (newDoc.find('#login').length === 0) {
      return apiFetch(`/api/2/user/${username}/`, {
        method: 'GET',
      })
      .then(result => {
        Dispatcher.dispatch({
          type: actionTypes.AUTH_LOG_IN_SUCCESS,
          id: result.id,
          username,
        });
      });
    } else {
      let $errorEls = newDoc.find('.errorlist > li');
      let errors = [];
      for (let i = 0; i < $errorEls.length; i++) {
        errors.push($errorEls[i].textContent);
      }

      Dispatcher.dispatch({
        type: actionTypes.AUTH_LOG_IN_FAILURE,
        errors: {_general: errors},
      });
    }
  })
  .fail((jqXHR, textStatus, errorThrown) => {
    Dispatcher.dispatch({
      type: actionTypes.AUTH_LOG_IN_FAILURE,
    });
    userGa.trackEvent('login failed');
  });
}

export function register(username, email, password) {
  Dispatcher.dispatch({
    type: actionTypes.AUTH_REGISTER_OPTIMISTIC,
  });
  return apiFetch('/api/2/user/', {
    method: 'POST',
    data: {
      username,
      email,
      password,
    },
  })
  .then(() => {
    Dispatcher.dispatch({
      type: actionTypes.AUTH_REGISTER_SUCCESS,
    });
  })
  .catch(errData => {
    Dispatcher.dispatch({
      type: actionTypes.AUTH_REGISTER_FAILURE,
      error: errData,
    });
    userGa.trackEvent('registration failed');
  });
}

export function logout() {
  Dispatcher.dispatch({
    type: actionTypes.AUTH_LOG_OUT,
  });
}

export function showLogin() {
  Dispatcher.dispatch({
    type: actionTypes.AUTH_SHOW_LOGIN,
  });
}

export function showRegister() {
  Dispatcher.dispatch({
    type: actionTypes.AUTH_SHOW_REGISTER,
  });
}

export default {
  checkAuthState,
  register,
  login,
  logout,
  showLogin,
  showRegister,
};

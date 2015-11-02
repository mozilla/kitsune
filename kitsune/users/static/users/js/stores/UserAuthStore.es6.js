/* globals _:false */

import BaseStore from '../../../sumo/js/stores/BaseStore.es6.js';
import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import {actionTypes, authStates} from '../constants/UserAuthConstants.es6.js';

var data = {
  state: null,
  id: null,
  username: null,
  pending: true,
  errors: null
};

function resetErrors() {
  data.errors = {
    _general: [],
  };
}
resetErrors();

function addError(scope, error) {
  if (!(scope in data.errors)) {
    throw new Error(`Unknown error scope: ${scope}`);
  }
  data.errors[scope].push(error);
}

function setErrors(obj) {
  for (let key in obj) {
    if (!obj.hasOwnProperty(key)) {
      continue;
    }
    addError(key, obj[key]);
  }
}

class _UserAuthStore extends BaseStore {
  getState() {
    return data.state;
  }

  getUsername() {
    return data.username;
  }

  getID() {
    return data.id;
  }

  getAll() {
    return _.clone(data);
  }
}

// Stores are singletons.
const UserAuthStore = new _UserAuthStore();

UserAuthStore.dispatchToken = Dispatcher.register((action) => {
  switch (action.type) {
    case actionTypes.AUTH_LOG_IN_OPTIMISTIC:
      data.pending = true;
      resetErrors();
      UserAuthStore.emitChange();
      break;

    case actionTypes.AUTH_LOG_IN_SUCCESS:
      data.state = authStates.LOGGED_IN;
      data.id = action.id;
      data.username = action.username;
      data.pending = false;
      resetErrors();
      UserAuthStore.emitChange();
      break;

    case actionTypes.AUTH_LOG_IN_FAILURE:
      data.pending = false;
      setErrors(action.errors);
      UserAuthStore.emitChange();
      break;

    case actionTypes.AUTH_REGISTER_OPTIMISTIC:
      data.pending = true;
      resetErrors();
      UserAuthStore.emitChange();
      break;

    case actionTypes.AUTH_REGISTER_SUCCESS:
      data.pending = false;
      resetErrors();
      UserAuthStore.emitChange();
      break;

    case actionTypes.AUTH_REGISTER_FAILURE:
      data.pending = false;
      UserAuthStore.emitChange();
      break;

    case actionTypes.AUTH_LOG_OUT:
      data.state = authStates.LOGGED_OUT;
      data.id = null;
      data.username = null;
      data.pending = false;
      UserAuthStore.emitChange();
      break;

    case actionTypes.AUTH_SHOW_LOGIN:
      data.state = authStates.LOGGING_IN;
      data.id = null;
      data.username = null;
      UserAuthStore.emitChange();
      break;

    case actionTypes.AUTH_SHOW_REGISTER:
      data.state = authStates.REGISTERING;
      data.id = null;
      data.username = null;
      UserAuthStore.emitChange();
      break;

    default:
      // do nothing
  }
});

export default UserAuthStore;

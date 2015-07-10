/* globals _:false */

import BaseStore from '../../../sumo/js/stores/BaseStore.es6';
import Dispatcher from '../../../sumo/js/Dispatcher.es6';
import {actionTypes} from '../constants/UserAuthConstants.es6';

var state = {
  isLoggedIn: null,
  username: null,
};

class _UserAuthStore extends BaseStore {
  isLoggedIn() {
    return state.isLoggedIn;
  }

  getUsername() {
    return state.username;
  }

  getToken() {
    return state.token;
  }

  getAll() {
    return _.clone(state);
  }
}

// Stores are singletons.
const UserAuthStore = new _UserAuthStore();

UserAuthStore.dispatchToken = Dispatcher.register((action) => {
  switch (action.type) {
    case actionTypes.AUTH_LOGGED_IN:
      state.isLoggedIn = true;
      state.username = action.username;
      UserAuthStore.emitChange();

    case actionTypes.AUTH_LOGGED_OUT:
      state.isLoggedIn = false;
      state.username = null;
      UserAuthStore.emitChange();

    default:
      // do nothing
  }
});

export default UserAuthStore;

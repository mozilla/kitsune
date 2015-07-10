/* globals _:false */

import BaseStore from '../../../sumo/js/stores/BaseStore.es6';
import Dispatcher from '../../../sumo/js/Dispatcher.es6';
import {actionTypes} from '../constants/UserAuthConstants.es6';

var data = {
  state: null,
  username: null,
};

class _UserAuthStore extends BaseStore {
  getState() {
    return data.state;
  }

  getUsername() {
    return data.username;
  }

  getToken() {
    return data.token;
  }

  getAll() {
    return _.clone(data);
  }
}

// Stores are singletons.
const UserAuthStore = new _UserAuthStore();

UserAuthStore.dispatchToken = Dispatcher.register((action) => {
  switch (action.type) {
    case actionTypes.AUTH_SET_STATE:
      data.state = action.state;
      data.username = action.username || null;
      UserAuthStore.emitChange();
      break;

    default:
      // do nothing
  }
});

export default UserAuthStore;

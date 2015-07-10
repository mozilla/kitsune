import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import {actionTypes} from '../constants/UserAuthConstants.es6.js';

export function setAuthState(state) {
  Dispatcher.dispatch({
    type: actionTypes.AUTH_SET_STATE,
    state,
  });
}

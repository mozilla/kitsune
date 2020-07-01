import Dispatcher from "../Dispatcher.es6.js";
import { actionTypes } from "../constants/UrlConstants.es6.js";

/**
 * Update the url path, notify any listeners, and call history.pushState.
 * @param  {object} params Variables to merge into the current path state.
 */
export function updatePath(params) {
  Dispatcher.dispatch({
    type: actionTypes.UPDATE_PATH,
    params,
  });
}

/**
 * Set the path defaults and notify listeners. If the path string
 * does not have the given values, they will be set, otherwise
 * the existing value will be kept. This will call history.replaceState.
 * @param  {object} params Default values for path.
 */
export function updatePathDefaults(params) {
  Dispatcher.dispatch({
    type: actionTypes.UPDATE_PATH_DEFAULTS,
    params,
  });
}

export default {
  updatePath,
  updatePathDefaults,
};

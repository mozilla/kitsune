import Dispatcher from '../Dispatcher.es6.js';
import {actionTypes} from '../constants/UrlConstants.es6.js';

/**
 * Update the url path string, notify any listeners, and call history.pushState.
 * @param  string pathRegex Regular expression string to test against the current path.
 * @param  [array] propNames The property names to associate with each match in the path.
 */
export function getPropsFromPath(pathRegex, propNames) {
  Dispatcher.dispatch({
    type: actionTypes.GET_PROPS_FROM_PATH,
    pathRegex,
    propNames,
  });
}

/**
 * Update the url path string, notify any listeners, and call history.pushState.
 * @param  [array] paths Variables to merge into the current url path.
 */
export function updateUrlPath(paths) {
  Dispatcher.dispatch({
    type: actionTypes.UPDATE_URL_PATH,
    paths,
  });
}

/**
 * Update the query string, notify any listeners, and call history.pushState.
 * @param  {object} params Variables to merge into the current query string state.
 */
export function updateQueryString(params) {
  Dispatcher.dispatch({
    type: actionTypes.UPDATE_QUERY_STRING,
    params,
  });
}

/**
 * Set the query string defaults and notify listeners. If the query
 * string does not have the given values, they will be set, otherwise
 * the existing value will be kept. This will call history.replaceState.
 * @param  {object} params Default values for querystrings.
 */
export function updateQueryStringDefaults(params) {
  Dispatcher.dispatch({
    type: actionTypes.UPDATE_QUERY_STRING_DEFAULTS,
    params,
  });
}

export default {
  getPropsFromPath,
  updateQueryString,
  updateQueryStringDefaults,
  updateUrlPath,
};

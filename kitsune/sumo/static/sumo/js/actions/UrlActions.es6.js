import Dispatcher from '../Dispatcher.es6.js';
import {actionTypes} from '../constants/UrlConstants.es6.js';

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
  updateQueryString,
  updateQueryStringDefaults,
};

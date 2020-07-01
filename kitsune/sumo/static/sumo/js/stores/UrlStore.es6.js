/* globals _:false */

/**
 * A shim to treat the URL query string as a Store. Listens to actions
 * to update the query string, including pushstate calls, and responds
 * to popstate events from the browser, translating them into store
 * update events.
 */

import BaseStore from "./BaseStore.es6.js";
import Dispatcher from "../Dispatcher.es6.js";
import { actionTypes, pathStructure } from "../constants/UrlConstants.es6.js";
import {
  getPathAsDict,
  pathStringFromDict,
  getQueryParamsAsDict,
  queryParamStringFromDict,
} from "../utils/urls.es6.js";

var urlData = {
  pathProps: getPathAsDict(pathStructure),
  queryParams: getQueryParamsAsDict(),
  step: "product",
};

function updateStep() {
  let pathProps = getPathAsDict(pathStructure);

  if (pathProps.product && pathProps.topic) {
    return "title";
  } else if (pathProps.product && !pathProps.topic) {
    return "topic";
  } else if (!pathProps.product && !pathProps.topic) {
    return "product";
  }
}

class _UrlStore extends BaseStore {
  get(key) {
    return urlData[key];
  }
}

// Stores are singletons.
const UrlStore = new _UrlStore();

UrlStore.dispatchToken = Dispatcher.register((action) => {
  let params, pathString, qs;
  switch (action.type) {
    case actionTypes.UPDATE_PATH:
      params = _.extend({}, urlData.pathProps, action.params);
      pathString = pathStringFromDict(params);
      window.history.pushState(
        params,
        null,
        pathString + window.location.search
      );
      urlData.step = updateStep();
      UrlStore.emitChange();
      break;

    case actionTypes.UPDATE_PATH_DEFAULTS:
      params = getPathAsDict(action.params);
      pathString = pathStringFromDict(params);
      window.history.replaceState(
        params,
        null,
        pathString + window.location.search
      );
      urlData.step = updateStep();
      UrlStore.emitChange();
      break;

    default:
    // do nothing
  }
});

/* When the user clicks back/forward, the store will return different
 * values, so notify all listeners. */
window.addEventListener("popstate", function () {
  urlData.step = updateStep();
  UrlStore.emitChange();
});

export default UrlStore;

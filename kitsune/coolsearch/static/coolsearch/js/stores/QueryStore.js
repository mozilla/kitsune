/* globals _:false */

import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import BaseStore from '../../../sumo/js/stores/BaseStore.es6.js';

import ActionConstants from '../constants/ActionConstants.js';


var queryData = {
  currentForm: 'wiki',
  wiki: {},
  question: {},
  forum: {},
};

class _QueryStore extends BaseStore {
  getCurrentQuery() {
    return _.clone(queryData[queryData.currentForm]);
  }

  getCurrentForm() {
    return queryData.currentForm;
  }
}

// Stores are singletons.
const QueryStore = new _QueryStore();

var setQuery = function (query, type) {
  queryData[type] = query;
  QueryStore.emitChange();
};

var setCurrentForm = function (currentForm) {
  queryData.currentForm = currentForm;
  QueryStore.emitChange();
};

QueryStore.dispatchToken = Dispatcher.register(function (action) {
  switch (action.type) {
    case ActionConstants.UPDATE_WIKI:
      setQuery(action.query, 'wiki');
      break;
    case ActionConstants.UPDATE_QUESTION:
      setQuery(action.query, 'question');
      break;
    case ActionConstants.UPDATE_FORUM:
      setQuery(action.query, 'forum');
      break;
    case ActionConstants.SWITCH_FORM_TAB:
      setCurrentForm(action.query);
      break;
  }
});

export default QueryStore;

/* globals _:false */

import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import BaseStore from '../../../sumo/js/stores/BaseStore.es6.js';

import ActionConstants from '../constants/ActionConstants.js';


var queryData = {
  currentForm: 'wiki',
  query: '',
  wiki: {},
  question: {},
  forum: {},
};

class _QueryStore extends BaseStore {
  getQuery() {
    return _.clone(queryData.query);
  }

  getCurrentFilters() {
    var filters = queryData[queryData.currentForm];
    // Ensure the "query" filter has the latest data the user entered.
    filters.query = queryData.query;
    return _.clone(filters);
  }

  getCurrentForm() {
    return queryData.currentForm;
  }
}

// Stores are singletons.
const QueryStore = new _QueryStore();

var setFilters = function (filters, type) {
  // `query` is a special, shared filter that we store at a global level.
  if (typeof filters.query !== 'undefined') {
    queryData.query = filters.query;
  }

  for (var filter in filters) {
    if (filters.hasOwnProperty(filter)) {
      queryData[type][filter] = filters[filter];
    }
  }

  QueryStore.emitChange();
};

var setCurrentForm = function (currentForm) {
  queryData.currentForm = currentForm;
  QueryStore.emitChange();
};

QueryStore.dispatchToken = Dispatcher.register(function (action) {
  switch (action.type) {
    case ActionConstants.UPDATE_WIKI:
      setFilters(action.data, 'wiki');
      break;
    case ActionConstants.UPDATE_QUESTION:
      setFilters(action.data, 'question');
      break;
    case ActionConstants.UPDATE_FORUM:
      setFilters(action.data, 'forum');
      break;
    case ActionConstants.SWITCH_FORM_TAB:
      setCurrentForm(action.data);
      break;
  }
});

export default QueryStore;

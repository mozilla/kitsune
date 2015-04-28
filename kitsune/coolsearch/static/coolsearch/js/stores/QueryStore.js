import SearchDispatcher from '../dispatcher/SearchDispatcher.js';
import ActionConstants from '../constants/ActionConstants.js';
import { EventEmitter } from 'events';

const CHANGE_EVENT = 'change';

var _query = {
  currentForm: 'wiki',
  wiki: {},
  question: {},
  forum: {},
};

class _QueryStore extends EventEmitter {
  emitChange() {
    this.emit(CHANGE_EVENT);
  }

  addChangeListener(callback) {
    this.on(CHANGE_EVENT, callback);
  }

  removeChangeListener(callback) {
    this.removeListener(CHANGE_EVENT, callback);
  }

  getCurrentQuery() {
    return _query[_query.currentForm];
  }
}

// Stores are singletons.
const store = new _QueryStore();

var setQuery = function (query, type) {
  _query[type] = query;
  store.emitChange();
};

var setCurrentForm = function (currentForm) {
  _query.currentForm = currentForm;
  store.emitChange();
};

store.dispatchToken = SearchDispatcher.register(function (action) {
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

export default store;

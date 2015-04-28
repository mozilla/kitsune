import SearchDispatcher from '../dispatcher/SearchDispatcher.js';
import ActionConstants from '../constants/ActionConstants.js';
import { EventEmitter } from 'events';

const CHANGE_EVENT = 'change';

var _total = 0;
var _results = [];

class ResultsStore extends EventEmitter {
  emitChange() {
    this.emit(CHANGE_EVENT);
  }

  addChangeListener(callback) {
    this.on(CHANGE_EVENT, callback);
  }

  removeChangeListener(callback) {
    this.removeListener(CHANGE_EVENT, callback);
  }

  getAll() {
    return _results;
  }

  getCount() {
    return _total;
  }
}

// Stores are singletons.
var store = new ResultsStore();

function setResults(results) {
  _total = results.num_results;
  _results = results.results;

  store.emitChange();
}

store.dispatchToken = SearchDispatcher.register(function (action) {
  switch (action.type) {
    case ActionConstants.RECEIVE_RESULTS:
      setResults(action.results);
      break;
  }
});

export default store;

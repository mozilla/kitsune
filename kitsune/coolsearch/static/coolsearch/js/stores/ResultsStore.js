/* globals _:false */

import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import BaseStore from '../../../sumo/js/stores/BaseStore.es6.js';

import ActionConstants from '../constants/ActionConstants.js';


var total = 0;
var results = [];

class _ResultsStore extends BaseStore {
  getAll() {
    return _.clone(results);
  }

  getCount() {
    return total;
  }
}

// Stores are singletons.
const ResultsStore = new _ResultsStore();

function setResults(data) {
  total = data.num_results;
  results = data.results;

  ResultsStore.emitChange();
}

ResultsStore.dispatchToken = Dispatcher.register(function (action) {
  switch (action.type) {
    case ActionConstants.RECEIVE_RESULTS:
      setResults(action.results);
      break;
  }
});

export default ResultsStore;

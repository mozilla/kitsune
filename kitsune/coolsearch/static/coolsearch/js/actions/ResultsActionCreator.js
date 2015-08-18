import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import ActionConstants from '../constants/ActionConstants.js';


export function createResults(results) {
  Dispatcher.dispatch({
    type: ActionConstants.RECEIVE_RESULTS,
    results: results
  });
}

export default {createResults};

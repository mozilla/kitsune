import SearchDispatcher from '../dispatcher/SearchDispatcher.js';
import ActionConstants from '../constants/ActionConstants.js';


var ResultsActionCreator = {
    createResults: function (results) {
        SearchDispatcher.dispatch({
            type: ActionConstants.RECEIVE_RESULTS,
            results: results
        });
    }
};

export default ResultsActionCreator;

import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import ActionConstants from '../constants/ActionConstants.js';


var _dispatch = function (action, query) {
  Dispatcher.dispatch({
    type: action,
    query: query,
  });
};

export function updateQueryWiki(query) {
  _dispatch(ActionConstants.UPDATE_WIKI, query);
}
export function updateQueryQuestion(query) {
  _dispatch(ActionConstants.UPDATE_QUESTION, query);
}
export function updateQueryForum(query) {
  _dispatch(ActionConstants.UPDATE_FORUM, query);
}
export function updateCurrentForm(currentForm) {
  _dispatch(ActionConstants.SWITCH_FORM_TAB, currentForm);
}

export default {
  updateQueryWiki,
  updateQueryQuestion,
  updateQueryForum,
  updateCurrentForm
};

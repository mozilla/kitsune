import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import ActionConstants from '../constants/ActionConstants.js';


var _dispatch = function (action, data) {
  Dispatcher.dispatch({
    type: action,
    data: data,
  });
};

export function updateFiltersWiki(filters) {
  _dispatch(ActionConstants.UPDATE_WIKI, filters);
}
export function updateFiltersQuestion(filters) {
  _dispatch(ActionConstants.UPDATE_QUESTION, filters);
}
export function updateFiltersForum(filters) {
  _dispatch(ActionConstants.UPDATE_FORUM, filters);
}
export function updateCurrentForm(currentForm) {
  _dispatch(ActionConstants.SWITCH_FORM_TAB, currentForm);
}

export default {
  updateFiltersWiki,
  updateFiltersQuestion,
  updateFiltersForum,
  updateCurrentForm
};

import SearchDispatcher from '../dispatcher/SearchDispatcher.js';
import ActionConstants from '../constants/ActionConstants.js';


var _dispatch = function (action, query) {
  SearchDispatcher.dispatch({
    type: action,
    query: query,
  });
};

var QueryActionCreator = {
  updateQueryWiki: function (query) {
    _dispatch(ActionConstants.UPDATE_WIKI, query);
  },
  updateQueryQuestion: function (query) {
    _dispatch(ActionConstants.UPDATE_QUESTION, query);
  },
  updateQueryForum: function (query) {
    _dispatch(ActionConstants.UPDATE_FORUM, query);
  },
  updateCurrentForm: function (currentForm) {
    _dispatch(ActionConstants.SWITCH_FORM_TAB, currentForm);
  },
};

export default QueryActionCreator;

/* globals _:false */

import BaseStore from '../../../sumo/js/stores/BaseStore.es6.js';
import AAQDispatcher from '../dispatchers/AAQDispatcher.es6.js';
import AAQConstants from '../constants/AAQConstants.es6.js';

var question = {
  product: null,
  topic: null,
  title: null,
  content: null,
};

var suggestions = [];
var state = 'editing';
var validationErrors = {};

class _QuestionEditStore extends BaseStore {
  getQuestion() {
    return _.clone(question);
  }

  getSuggestions() {
    return _.clone(suggestions);
  }

  getState() {
    return state;
  }

  getValidationErrors() {
    return _.clone(validationErrors);
  }
}

// Stores are singletons.
const QuestionEditStore = new _QuestionEditStore();

QuestionEditStore.dispatchToken = AAQDispatcher.register((action) => {
  switch (action.type) {
    case AAQConstants.actionTypes.SET_PRODUCT:
      if (question.product !== action.product) {
        question.product = action.product;
        question.topic = null;
        QuestionEditStore.emitChange();
      }
      break;

    case AAQConstants.actionTypes.SET_TOPIC:
      if (question.topic !== action.topic) {
        question.topic = action.topic;
        QuestionEditStore.emitChange();
      }
      break;

    case AAQConstants.actionTypes.SET_TITLE:
      if (question.title !== action.title) {
        question.title = action.title;
        QuestionEditStore.emitChange();
      }
      break;

    case AAQConstants.actionTypes.SET_CONTENT:
      if (question.content !== action.content) {
        question.content = action.content;
        QuestionEditStore.emitChange();
      }
      break;

    case AAQConstants.actionTypes.SET_SUGGESTIONS:
      suggestions = action.suggestions;
      QuestionEditStore.emitChange();
      break;

    case AAQConstants.actionTypes.QUESTION_SUBMIT_OPTIMISTIC:
      state = 'pending';
      QuestionEditStore.emitChange();
      break;

    case AAQConstants.actionTypes.QUESTION_SUBMIT_SUCCESS:
      state = 'submitted';
      validationErrors.server = {};
      QuestionEditStore.emitChange();
      break;

    case AAQConstants.actionTypes.QUESTION_SUBMIT_FAILURE:
      state = 'error';
      validationErrors.server = [action.error];
      QuestionEditStore.emitChange();
      break;

    default:
      // do nothing
  }
});

export default QuestionEditStore;

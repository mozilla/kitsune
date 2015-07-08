/* globals _:false */

import BaseStore from '../../../sumo/js/stores/BaseStore.es6.js';
import AAQDispatcher from '../dispatchers/AAQDispatcher.es6.js';
import {actionTypes, questionEditState} from '../constants/AAQConstants.es6.js';

var question = {
  product: null,
  topic: null,
  title: '',
  content: '',
};

var suggestions = [];
var state = questionEditState.QUESION_INVALID;
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

function updateState() {
  if (question.product === null) {
    state = questionEditState.INVALID;
    return;
  }
  if (question.topic === null) {
    state = questionEditState.INVALID;
    return;
  }
  if (question.title.trim() === '') {
    state = questionEditState.INVALID;
    return;
  }
  if (question.content.trim() === '') {
    state = questionEditState.INVALID;
    return;
  }
  state = questionEditState.VALID;
}

// Stores are singletons.
const QuestionEditStore = new _QuestionEditStore();

QuestionEditStore.dispatchToken = AAQDispatcher.register((action) => {
  switch (action.type) {
    case actionTypes.SET_PRODUCT:
      if (question.product !== action.product) {
        question.product = action.product;
        question.topic = null;
        updateState();
        QuestionEditStore.emitChange();
      }
      break;

    case actionTypes.SET_TOPIC:
      if (question.topic !== action.topic) {
        question.topic = action.topic;
        updateState();
        QuestionEditStore.emitChange();
      }
      break;

    case actionTypes.SET_TITLE:
      if (question.title !== action.title) {
        question.title = action.title;
        updateState();
        QuestionEditStore.emitChange();
      }
      break;

    case actionTypes.SET_CONTENT:
      if (question.content !== action.content) {
        question.content = action.content;
        updateState();
        QuestionEditStore.emitChange();
      }
      break;

    case actionTypes.SET_SUGGESTIONS:
      suggestions = action.suggestions;
      QuestionEditStore.emitChange();
      break;

    case actionTypes.QUESTION_SUBMIT_OPTIMISTIC:
      state = questionEditState.PENDING;
      QuestionEditStore.emitChange();
      break;

    case actionTypes.QUESTION_SUBMIT_SUCCESS:
      state = questionEditState.SUBMITTED;
      validationErrors.server = {};
      QuestionEditStore.emitChange();
      break;

    case actionTypes.QUESTION_SUBMIT_FAILURE:
      state = questionEditState.ERROR;
      validationErrors.server = [action.error];
      QuestionEditStore.emitChange();
      break;

    default:
      // do nothing
  }
});

export default QuestionEditStore;

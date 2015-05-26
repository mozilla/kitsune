/* globals _:false */

import BaseStore from '../../../sumo/js/stores/BaseStore.es6.js';
import AAQDispatcher from '../dispatchers/AAQDispatcher.es6.js';
import AAQConstants from '../constants/AAQConstants.es6.js';

var question = {
  product: null,
  topic: null,
};

class _QuestionEditStore extends BaseStore {
  get() {
    return _.clone(question);
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
  }
});

export default QuestionEditStore;

/* globals _:false */
import apiFetch from '../../../sumo/js/utils/apiFetch.es6.js';
import Dispatcher from '../../../sumo/js/Dispatcher.es6.js';
import {actionTypes} from '../constants/AAQConstants.es6.js';
import QuestionEditStore from '../stores/QuestionEditStore.es6.js';

export function setProduct(product) {
  Dispatcher.dispatch({
    type: actionTypes.SET_PRODUCT,
    product,
  });
}

export function setTopic(topic) {
  Dispatcher.dispatch({
    type: actionTypes.SET_TOPIC,
    topic,
  });
}

export function setTitle(title) {
  Dispatcher.dispatch({
    type: actionTypes.SET_TITLE,
    title,
  });

  searchSuggestions(title);
}

function searchSuggestions(title) {
  apiFetch('/api/2/search/suggest/', {
    data: {
      q: title,
      max_questions: 2,
      max_documents: 2,
      product: QuestionEditStore.getQuestion().product,
    },
  })
  .then(data => {
    let docSuggestions = data.documents.map((document) => {
      document.type = 'document';
      return document;
    });
    let questionSuggestions = data.questions.map((question) => {
      question.type = 'question';
      question.url = `/questions/${question.id}`;
      question.summary = '';
      return question;
    });
    let suggestions = docSuggestions.concat(questionSuggestions);
    setSuggestions(suggestions);
  })
  .catch(err => {
    console.log('suggest error');
  });
}
searchSuggestions = _.throttle(searchSuggestions, 500);

export function setSuggestions(suggestions) {
  Dispatcher.dispatch({
    type: actionTypes.SET_SUGGESTIONS,
    suggestions,
  });
}

export function setContent(content) {
  Dispatcher.dispatch({
    type: actionTypes.SET_CONTENT,
    content,
  });
}

export function submitQuestion() {
  Dispatcher.dispatch({
    type: actionTypes.QUESTION_SUBMIT_OPTIMISTIC,
  });

  const csrf = document.querySelector('input[name=csrfmiddlewaretoken]').value;
  let questionData = QuestionEditStore.getQuestion();
  let locale = document.querySelector('html').getAttribute('lang');
  questionData.locale = locale;
  let metadata = questionData.metadata || {};
  delete questionData.metadata;
  let questionUrl;

  metadata.useragent = navigator.userAgent;
  metadata.source = 'Single page AAQ';

  apiFetch('/api/2/question/?format=json', {
    method: 'post',
    data: questionData,
    credentials: 'include',
    headers: {
      'X-CSRFToken': csrf,
    },
  })
  .then(question => {
    questionUrl = `/${locale}/questions/${question.id}`;

    let promises = [];
    for (let key in metadata) {
      promises.push(apiFetch(`/api/2/question/${question.id}/set_metadata/?format=json`, {
        method: 'post',
        credentials: 'include',
        data: {
          name: key,
          value: metadata[key],
        },
        headers: {
          'X-CSRFToken': csrf,
        },
      }));
    }

    return Promise.all(promises);
  })
  .then(() => {
    Dispatcher.dispatch({type: actionTypes.QUESTION_SUBMIT_SUCCESS});
    document.location = questionUrl;
  })
  .catch((err) => {
    Dispatcher.dispatch({
      type: actionTypes.QUESTION_SUBMIT_FAILURE,
      error: err.message,
    });
  });
}

export default {
  setProduct,
  setTopic,
  setTitle,
  setContent,
  submitQuestion,
};

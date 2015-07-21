import constantMap from '../../../sumo/js/utils/constantMap.es6.js';

export const actionTypes = constantMap([
  'SET_PRODUCT',
  'SET_TOPIC',
  'SET_TITLE',
  'SET_CONTENT',
  'SET_SUGGESTIONS',
  'QUESTION_SUBMIT_OPTIMISTIC',
  'QUESTION_SUBMIT_SUCCESS',
  'QUESTION_SUBMIT_FAILURE',
]);

export const questionEditState = constantMap([
  'INVALID',
  'VALID',
  'PENDING',
  'SUBMITTED',
  'ERROR',
]);

export default {actionTypes, questionEditState};

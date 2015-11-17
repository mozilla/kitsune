import constantMap from '../../../sumo/js/utils/constantMap.es6.js';

export const actionTypes = constantMap([
  'ADD_IMAGE',
  'REMOVE_IMAGE',
  'SET_PRODUCT',
  'SET_TOPIC',
  'SET_TITLE',
  'SET_CONTENT',
  'SET_SUGGESTIONS',
  'QUESTION_SUBMIT_OPTIMISTIC',
  'QUESTION_SUBMIT_SUCCESS',
  'QUESTION_SUBMIT_FAILURE',
  'TROUBLESHOOTING_OPT_IN',
  'TROUBLESHOOTING_OPT_OUT',
  'TROUBLESHOOTING_SET_DATA',
  'TROUBLESHOOTING_AVAILABLE',
]);

export const questionEditState = constantMap([
  'INVALID',
  'VALID',
  'PENDING',
  'SUBMITTED',
  'ERROR',
]);

export default {actionTypes, questionEditState};

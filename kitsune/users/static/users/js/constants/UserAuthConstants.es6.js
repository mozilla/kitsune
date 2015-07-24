import constantMap from '../../../sumo/js/utils/constantMap.es6.js';

export const actionTypes = constantMap([
  'AUTH_LOG_IN_OPTIMISTIC',
  'AUTH_LOG_IN_SUCCESS',
  'AUTH_LOG_IN_FAILURE',

  'AUTH_REGISTER_OPTIMISTIC',
  'AUTH_REGISTER_SUCCESS',
  'AUTH_REGISTER_FAILURE',

  'AUTH_LOG_OUT',
  'AUTH_SHOW_REGISTER',
  'AUTH_SHOW_LOGIN',
]);

export const authStates = constantMap([
  'LOGGED_OUT',
  'LOGGED_IN',
  'LOGGING_IN',
  'REGISTERING',
]);

export default {
  actionTypes,
  authStates,
};

import constantMap from '../../../sumo/js/utils/constantMap.es6';

export const actionTypes = constantMap([
  'AUTH_SET_STATE',
]);

export const userAuthStates = constantMap([
  'LOGGED_IN',
  'LOGGING_IN',
  'REGISTERING',
]);

export default {
  actionTypes,
  userAuthStates,
};

class Constant {
  constructor(name) {
    this.name = name;
  }

  toString() {
    return this.name;
  }
}

function constantMap(names) {
  let constants = {};
  for (let name of names) {
    constants[name] = new Constant(name);
  }
  return constants;
}

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

export default {actionTypes};

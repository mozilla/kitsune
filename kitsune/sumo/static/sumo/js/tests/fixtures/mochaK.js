import mochaFixtureHelper from './mochaFixtureHelper.js';

export default mochaFixtureHelper(() => {
  let k = global.k || (global.window ? global.window.k : null) || {};
  return {
    k: k,
  };
});

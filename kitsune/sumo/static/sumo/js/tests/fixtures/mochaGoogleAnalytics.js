import mochaFixtureHelper from './mochaFixtureHelper.js';

export default mochaFixtureHelper(() => {
  return {
    _gaq: [],
    trackEvent: function() {},
    trackPageview: function() {}
  };
});

import mochaFixtureHelper from './mochaFixtureHelper.js';
import _ from 'underscore';

export default mochaFixtureHelper(() => {
  return {
    _: _,
  };
});

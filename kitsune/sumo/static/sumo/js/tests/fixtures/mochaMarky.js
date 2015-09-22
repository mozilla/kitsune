import {rerequire} from 'mocha-jsdom';
import mochaFixtureHelper from './mochaFixtureHelper.js';

export default mochaFixtureHelper(() => {
  rerequire('../../markup.js');
  return {
    Marky: global.window.Marky,
  };
});

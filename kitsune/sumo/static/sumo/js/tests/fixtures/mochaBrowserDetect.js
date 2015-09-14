import mochaFixtureHelper from './mochaFixtureHelper.js';

export default mochaFixtureHelper(({browser='firefox', version=25.0, OS='winxp'}={}) => {
  let BrowserDetect = {browser, version, OS};
  return {
    BrowserDetect: BrowserDetect,
  };
});

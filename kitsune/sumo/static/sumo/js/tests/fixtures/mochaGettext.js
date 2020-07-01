import mochaFixtureHelper from "./mochaFixtureHelper.js";

function fakeGettext(msgid) {
  return msgid;
}

export default mochaFixtureHelper(() => {
  return {
    gettext: fakeGettext,
  };
});

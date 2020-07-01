import mochaFixtureHelper from "./mochaFixtureHelper.js";
import jQuery from "jquery";

export default mochaFixtureHelper(() => {
  let jq = jQuery(global.window);
  return {
    $: jq,
    jQuery: jq,
  };
});

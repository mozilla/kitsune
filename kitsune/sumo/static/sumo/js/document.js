import "sumo/js/libs/jquery.lazyload";
import AjaxVote from "sumo/js/ajaxvote";
import {
  getQueryParamsAsDict,
  getReferrer,
  getSearchQuery,
} from "sumo/js/main";
import ShowFor from "sumo/js/showfor";

new ShowFor();

addReferrerAndQueryToVoteForm();
new AjaxVote(".document-vote form", {
  positionMessage: false,
  replaceFormWithMessage: true,
  removeForm: true,
});

$("img.lazy").lazyload();

function addReferrerAndQueryToVoteForm() {
  // Add the source/referrer and query terms to the helpful vote form
  var urlParams = getQueryParamsAsDict(),
    referrer = getReferrer(urlParams),
    query = getSearchQuery(urlParams, referrer);
  $(".document-vote form")
    .append($('<input type="hidden" name="referrer"/>').attr("value", referrer))
    .append($('<input type="hidden" name="query"/>').attr("value", query));
}

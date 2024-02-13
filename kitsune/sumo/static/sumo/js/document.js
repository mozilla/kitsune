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
determineLazyLoad();

new AjaxVote(".document-vote form", {
  positionMessage: false,
  replaceFormWithMessage: true,
  removeForm: true,
});

// Once the DOM is ready, dynamically load the CSRF token for the voting
// form. This allows us to cache articles without caching the CSRF token.
$(function() {
    let $placeholders = $("form > div.csrftoken-placeholder");
    if ($placeholders) {
      $.get("/csrftoken").done(function(html) {
        $placeholders.replaceWith(html);
      }).fail(function(err) {
        console.error(err);
      });
    }
});

$(window).on("load", function() {
    // Wait for all content (including images) to load
    var hash = window.location.hash;
    if (hash) {
      window.location.hash = ""; // Clear the hash initially
      setTimeout(function() {
          window.location.hash = hash; // Restore the hash after all images are loaded
      }, 0);
  }}
);

// For this singular document, we are going to load
// all images without lazy loading
// TODO: We need a fix for the whole KB that won't
// break the lazy loading.
function determineLazyLoad() {
  if(window.location.href.indexOf("relay-integration") > -1) {
    $("img.lazy").loadnow(); // Load all images
  }
  else {
    $("img.lazy").lazyload();
  }
};

function addReferrerAndQueryToVoteForm() {
  // Add the source/referrer and query terms to the helpful vote form
  var urlParams = getQueryParamsAsDict(),
    referrer = getReferrer(urlParams),
    query = getSearchQuery(urlParams, referrer);
  $(".document-vote form")
    .append($('<input type="hidden" name="referrer"/>').attr("value", referrer))
    .append($('<input type="hidden" name="query"/>').attr("value", query));
};

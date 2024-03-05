// Collect questions metrics.
import trackEvent from "sumo/js/analytics";

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", () => {
  const body = document.querySelector("body.answers");
  if (body) {
    // Track votes in GA.
    document.addEventListener("vote", (event) => {
      // This listener will respond to votes on answers to questions.
      // The url will be in the form "/{locale}/questions/{questionID}/vote/{answerID}".
      let urlParts = event.detail.url.split('/');
      let answerID = urlParts[urlParts.length - 1];
      let questionID = urlParts[urlParts.length - 3];

      if (('helpful' in event.detail) || ('not-helpful' in event.detail)) {
        trackEvent("answer_vote", {
          "answer_ID": answerID,
          "question_ID": questionID,
          "vote": ("helpful" in event.detail) ? "helpful": "not-helpful",
        });
      }
    });
    document.addEventListener("vote-for-question", (event) => {
      // This listener will respond to votes for questions ("I have this problem too").
      // The url will be in the form "/{locale}/questions/{questionID}/vote".
      let urlParts = event.detail.url.split('/');
      let questionID = urlParts[urlParts.length - 2];
      trackEvent("question_vote", {
        "question_ID": questionID,
      });
    });
  }
});

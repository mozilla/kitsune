// Collect wiki metrics.
import trackEvent from "sumo/js/analytics";

// The "DOMContentLoaded" event is guaranteed not to have been
// called by the time the following code is run, because it always
// waits until all deferred scripts have been loaded, and the code
// in this file is always bundled into a script that is deferred.
document.addEventListener("DOMContentLoaded", () => {
  const body = document.querySelector("body.document");
  if (body) {
    const versionSelect = document.querySelector("#showfor-panel select.version");
    const platformSelect = document.querySelector("#showfor-panel select.platform");

    // Track votes in GA.
    document.addEventListener("vote", (event) => {
      if (('helpful' in event.detail) || ('not-helpful' in event.detail)) {
        trackEvent("article_vote", {
          "vote": ("helpful" in event.detail) ? "helpful": "not-helpful",
        });
      }
    });

    document.addEventListener("survey-loaded", (event) => {
      const surveyCloseButton = document.querySelector("#unhelpful-survey .close-button");
      const surveySubmitButton = document.querySelector('#unhelpful-survey button[type="submit"]');

      function trackCloseEvent(event) {
        trackEvent("article_unhelpful_survey_close");
      }

      if (surveySubmitButton) {
        surveySubmitButton.addEventListener("click", function(event) {
          trackEvent("article_unhelpful_survey_submit");
          if (surveyCloseButton) {
            // After the survey is submitted, we don't want to track the
            // close of the final message.
            surveyCloseButton.removeEventListener("click", trackCloseEvent)
          }
        });
      }
      if (surveyCloseButton) {
        surveyCloseButton.addEventListener("click", trackCloseEvent);
      }
    });

    // Track showfor changes in GA.
    if (versionSelect) {
      versionSelect.addEventListener("change", function(event) {
        trackEvent("showfor_version_change", {
          "showfor_version": this.value,
        });
      });
    }
    if (platformSelect) {
      platformSelect.addEventListener("change", function(event) {
        trackEvent("showfor_platform_change", {
          "showfor_platform": this.value,
        });
      });
    }
  }
});

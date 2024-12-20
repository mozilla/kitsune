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
          "vote": ("helpful" in event.detail) ? "helpful" : "not-helpful",
        });
      }
    });

    // Track survey interactions
    const surveyContainer = document.querySelector('.survey-container');
    if (surveyContainer) {
      // Track when survey is closed
      const closeButton = surveyContainer.querySelector('button[type="button"]');
      if (closeButton) {
        closeButton.addEventListener("click", () => {
          trackEvent("article_unhelpful_survey_close");
        });
      }

      // Track when survey is submitted
      const form = surveyContainer.querySelector('form');
      if (form) {
        form.addEventListener("submit", () => {
          trackEvent("article_unhelpful_survey_submit");
        });
      }
    }

    // Track showfor changes in GA.
    if (versionSelect) {
      versionSelect.addEventListener("change", function (event) {
        trackEvent("showfor_version_change", {
          "showfor_version": this.value,
        });
      });
    }
    if (platformSelect) {
      platformSelect.addEventListener("change", function (event) {
        trackEvent("showfor_platform_change", {
          "showfor_platform": this.value,
        });
      });
    }
  }
});

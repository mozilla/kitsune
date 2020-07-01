/* globals $:false */
(function () {
  function launchWindow(url) {
    var sg_div = document.createElement("div");
    sg_div.innerHTML =
      "<h1>You have been selected for a survey</h1>" +
      '<p>We appreciate your feedback!</p><p><a href="' +
      url +
      '">Please click here to start it now.</a></p>' +
      "<a href=\"#\" onclick=\"document.getElementById('sg-popup').style.display = 'none';return false;\">No, thank you.</a>";
    sg_div.id = "sg-popup";
    document.body.appendChild(sg_div);
  }

  function basicSurvey(surveyGizmoURL) {
    // This is adapted from a snipptet given by Survey Gizmo.
    // It has been formatted to fit your screen. Bug 782809.
    if (!$.cookie("hasSurveyed")) {
      window.addEventListener("load", function (e) {
        launchWindow(surveyGizmoURL);
        $.cookie("hasSurveyed", "1", { expires: 365 });
      });
    }
  }

  var surveys = {
    mobile: function () {
      basicSurvey("https://qsurvey.mozilla.com/s3/63ac9fdb1ce1");
    },

    questions: function () {
      basicSurvey(
        "https://www.surveygizmo.com/s3/1717268/SUMO-Survey-candidate-collection-forum"
      );
    },

    firefox_refresh: function () {
      var surveyGizmoURL =
        "https://www.surveygizmo.com/s3/2010802/69cc2a79f50b";
      if (
        $.cookie("showFirefoxResetSurvey") === "1" &&
        !$.cookie("hasEverFirefoxResetSurvey")
      ) {
        window.addEventListener("load", function (e) {
          launchWindow(surveyGizmoURL);
          $.cookie("showFirefoxResetSurvey", "0", { expires: 365 });
          $.cookie("hasEverFirefoxResetSurvey", "1", { expires: 365 });
        });
      }
    },

    /* This sets up a couple of globals that SurveyGizmo can use to hook
     * into the UI and provide surveys to users.
     *
     * This code was derived from the minified version of code posted in bug 1175880
     *
     * This isn't actually a survey. It injects some JS that allows folks to enable
     * any survey they'd like through the SurveyGizmo admin.
     */
    beacon: function () {
      // set up temp SG reciever, until the main script loads
      window.SurveyGizmoBeacon = "sg_beacon";
      window.sg_beacon =
        window.sg_beacon ||
        function () {
          window.sg_beacon.q = window.sg_beacon.q || [];
          window.sg_beacon.q.push(arguments);
        };

      // load SG beacon script
      var beaconScript = document.createElement("script");
      beaconScript.async = 1;
      beaconScript.src =
        "//d2bnxibecyz4h5.cloudfront.net/runtimejs/intercept/intercept.js";
      var lastScriptTag = document.getElementsByTagName("script")[0];
      lastScriptTag.parentNode.insertBefore(beaconScript, lastScriptTag);

      // Initialize
      window.sg_beacon(
        "init",
        "MjgwNDktQUYyRDQ3ODk0MjY1NEVFNUIwNTI3MjhFMDk2QTE3RDU="
      );
    },
  };

  $(function () {
    var surveyList = $("body").data("survey-gizmos") || [];
    for (var i = 0; i < surveyList.length; i++) {
      var survey = surveys[surveyList[i]];
      if (survey) {
        survey();
      }
    }
  });
})();

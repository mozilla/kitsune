;(function() {
    function launchWindow(url) {
        var sg_div = document.createElement("div");
        sg_div.innerHTML = (
            '<h1>You have been selected for a survey</h1>' +
            '<p>We appreciate your feedback!</p><p><a href="' + url + '">Please click here start it now.</a></p>' +
            '<a href="#" onclick="document.getElementById(\'sg-popup\').style.display = \'none\';return false;">No, thank you.</a>'
        );
        sg_div.id = "sg-popup";
        document.body.appendChild(sg_div);
    }

    var surveys = {
        site_survey: function() {
            var surveyGizmoURL = $('body').data('surveygizmo-url') ||
                "https://www.surveygizmo.com/s3/popup/1002970/46488f9ad4eb";
            // This is adapted from a snipptet given by Survey Gizmo.
            // It has been formatted to fit your screen. Bug 782809.
            if (!$.cookie('hasSurveyed')) {
                window.addEventListener("load", function(e) {
                    launchWindow(surveyGizmoURL);
                    $.cookie('hasSurveyed', '1', {expires: 365});
                });
            }
        },

        firefox_refresh: function() {
            var surveyGizmoURL = 'https://www.surveygizmo.com/s3/2010802/69cc2a79f50b';
            if ($.cookie('showFirefoxResetSurvey') === '1' && !$.cookie('hasEverFirefoxResetSurvey')) {
                window.addEventListener("load", function(e) {
                    launchWindow(surveyGizmoURL);
                    $.cookie('showFirefoxResetSurvey', '0', {expires: 365});
                    $.cookie('hasEverFirefoxResetSurvey', '1', {expires: 365});
                });
            }
        }
    };

    $(function() {
        var surveyList = $('body').data('survey-gizmos') || [];
        for (var i = 0; i < surveyList.length; i++) {
            survey = surveys[surveyList[i]];
            if (survey) {
                survey();
            }
        }
    });
})();

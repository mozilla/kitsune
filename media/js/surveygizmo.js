;(function() {
    var surveys = {
        site_survey: function() {
            // This ugly pile is generated code from Survey Gizmo. Bug 782809.
            window.addEventListener("load",function(e) {if (!readCookie("hasSurveyed")) {launchWindow(document.getElementById("sg_div"));createCookie("hasSurveyed", 1, 365);}});function launchWindow(){var sg_div = document.createElement("div");sg_div.innerHTML = "<h1>You have been selected for a survey</h1><p>We appreciate your feedback!</p><p><a href=\"http://www.surveygizmo.com/s3/popup/1002970/46488f9ad4eb\">Please click here start it now.</a> </p> <a href=\"#\" onclick=\"document.getElementById('sg-popup').style.display = 'none';return false;\">No, thank you.</a> ";sg_div.id = "sg-popup";sg_div.style.position = "absolute";sg_div.style.width = "500px";sg_div.style.top = "100px";sg_div.style.left = "400px";sg_div.style.backgroundColor = "#ffffff";sg_div.style.borderColor = "#000000";sg_div.style.borderStyle = "solid";sg_div.style.padding = "20px";sg_div.style.fontSize = "16px";sg_div.style.zIndex = "1000";document.body.appendChild(sg_div);}function createCookie(name,value,days) {if (days) {var date = new Date();date.setTime(date.getTime()+(days*24*60*60*1000));var expires = "; expires="+date.toGMTString();}else var expires = "";document.cookie = name+"="+value+expires+"; path=/";}function readCookie(name) {var nameEQ = name + "=";var ca = document.cookie.split(";");for(var i=0;i < ca.length;i++) {var c = ca[i];while (c.charAt(0)==" ") c = c.substring(1,c.length);if (c.indexOf(nameEQ) == 0) return c.substring(nameEQ.length,c.length);}return null;}
        },

        register_survey: function() {
            // This ugly pile is generated code from Survey Gizmo. Bug 809433
            var sg_div = document.createElement("div");
            sg_div.innerHTML = "<h1>You have been selected for a survey</h1><p>We appreciate your feedback!</p><p><a href=\"http://www.surveygizmo.com/s3/popup/1076431/ba695bdef132\">Please click here start it now.</a> </p> <a href=\"#\" onclick=\"document.getElementById('sg-popup').style.display = 'none';return false;\">No, thank you.</a> "; sg_div.id = "sg-popup";sg_div.style.position = "absolute";sg_div.style.width = "500px";sg_div.style.top = "100px";sg_div.style.left = "400px";sg_div.style.backgroundColor = "#ffffff";sg_div.style.borderColor = "#000000";sg_div.style.borderStyle = "solid";sg_div.style.padding = "20px";sg_div.style.fontSize = "16px";document.body.appendChild(sg_div);
        }
    };

    $(function() {
        var survey_list = $('body').data('survey-gizmos');
        for (var i = 0; i < survey_list.length; i++) {
            survey = surveys[survey_list[i]];
            if (survey) {
                survey();
            }
        }
    });
})();

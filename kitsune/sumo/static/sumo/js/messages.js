/* globals $:false, Marky:false, k:false, gettext:false, interpolate:false */
/*
 * Make textarea in replies auto expanding.
 * Private messaging.
 */

$(document).ready(function () {
  // Show the ajax preview on the new message page.
  Marky.createSimpleToolbar("#new-message .editor-tools", "#id_message");
  new k.AjaxPreview($("#preview-btn"), {
    // eslint-disable-line
    changeHash: false,
  });

  // Hide reply button and shrink the textarea.
  var $area = $("#read-message textarea#id_message");
  $area.attr("placeholder", gettext("Reply..."));
  $("#read-message .editor-tools").hide();
  $("#read-message input[type=submit]").hide();

  // Show the orginal button and expanding textarea.
  $area.one("focus", function () {
    $area.autoResize({ minHeight: 150 }).addClass("focused");
    $("#read-message .editor-tools").show();
    $("#read-message input[type=submit]").show();
    Marky.createSimpleToolbar("#read-message .editor-tools", "#id_message", {
      privateMessaging: true,
    });
    new k.AjaxPreview($("#preview-btn"), {
      // eslint-disable-line
      changeHash: false,
    });
  });

  // Character counter for message box.
  var $summaryCount = $("#remaining-characters");
  var $summaryBox = $($summaryCount.data("input"));
  var maxCount = $summaryCount.data("max-characters");
  var updateCount = function () {
    var currentCount = $summaryBox.val().length;
    var delta = maxCount - currentCount;
    var message;

    if (delta < 0) {
      delta = 0;
    }
    message = interpolate(gettext("%s characters remaining"), [delta]);
    $summaryCount.text(message);
    if (maxCount - currentCount >= 10) {
      $summaryCount.css("color", "black");
    } else {
      $summaryCount.css("color", "red");
      if (currentCount >= maxCount) {
        $summaryBox.val($summaryBox.val().substr(0, maxCount));
      }
    }
  };

  updateCount();
  $summaryBox.bind("input", updateCount);
});

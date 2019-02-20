document.addEventListener('DOMContentLoaded', function() {

  var sCookiesFeedback = document.querySelector('#enable-cookies-submit-feedback');
  var sInsecureWarningFeedback = document.querySelector('#insecure-warning-submit-feedback');
  var sInsecureWarningVideoFeedback = document.querySelector('#insecure-warning-submit-video-feedback');

  function postData(url, payload) {
    var xhr = new XMLHttpRequest();
    xhr.open('POST', url);

    xhr.setRequestHeader('Accept', 'application/xml, text/xml, */*; q=0.01');
    xhr.setRequestHeader('Content-type', 'application/x-www-form-urlencoded; charset=UTF-8');

    var data = Object.keys(payload).map(
      function(k) {
        return k + '=' + encodeURIComponent(payload[k]);
      }).join('&');
    xhr.send(data);
  }

  function submitForm(action, selection, feedback) {
    var payload = {};

    if (selection !== null && selection.value) {
      payload[selection.name] = selection.value;
    }

    if (feedback !== null && feedback.value) {
      payload[feedback.name] = feedback.value;
    }

    postData(action, payload);
  }

  if (sCookiesFeedback !== null) {
    sCookiesFeedback.addEventListener('click', function(e) {
    e.preventDefault();

    var formAction = 'https://docs.google.com/forms/u/1/d/e/1FAIpQLSeI-9VEpU2jRghTxvT2XXr2TVGopieqAIG04z6goSQ4-a4s1Q/formResponse';
    var radioButton = document.querySelector('input[name="entry.437614058"]:checked');
    var feedbackText = document.querySelector('#enable-cookies-feedback-text');

    if (radioButton !== null && feedbackText.value.trim().length > 0) {
      submitForm(formAction, radioButton, feedbackText);
      }
    });
  }

  if (sInsecureWarningFeedback !== null) {
    sInsecureWarningFeedback.addEventListener('click', function(e) {
    e.preventDefault();

    var formAction = 'https://docs.google.com/forms/u/1/d/e/1FAIpQLSeQ6zNL1SNfTXJz_rZt5jtz76FUOFfPkAphLwrJf1SZdlItXQ/formResponse';
    var radioButton = document.querySelector('input[name="entry.1877592314"]:checked');
    var feedbackText = document.querySelector('#insecure-warning-feedback-text');
    if (radioButton !== null && feedbackText.value.trim().length > 0) {
      submitForm(formAction, radioButton, feedbackText);
      }
    });
  }

  if (sInsecureWarningVideoFeedback !== null) {
    sInsecureWarningVideoFeedback.addEventListener('click', function(e) {
    e.preventDefault();

    var formAction = 'https://docs.google.com/forms/d/e/1FAIpQLSfql3Latc6U9EE7fgBrtFXfJSU7n5w_19H86wB7z8CYDgChiQ/formResponse';
    var radioButton = document.querySelector('input[name="entry.575379247"]:checked');
    var feedbackText = document.querySelector('#insecure-warning-video-feedback-text');
    if (radioButton !== null && feedbackText.value.trim().length > 0) {
      submitForm(formAction, radioButton, feedbackText);
      }
    });
  }

});

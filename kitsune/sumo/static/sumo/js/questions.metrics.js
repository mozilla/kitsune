/* globals _gaq:false, trackEvent:false, jQuery:false */
// Collect questions metrics.

(function ($) {

  function init() {
    // Collect some metrics on the answers page.
    if (!$('body').is('.answers')) {
      return;
    }

    // Collect metrics on answer votes.
    $(document).on('vote', function(t, data) {
      var value;
      var urlParts = data.url.split('/');
      var lastPart = urlParts[urlParts.length - 1];
      var secondToLastPart = urlParts[urlParts.length - 2];
      var questionPart;
      var answerPart;

      if (_gaq) {
        if (lastPart === 'vote') {
          // This is a vote on the question.
          value = 'Me Too';
          questionPart = secondToLastPart;
          answerPart = '';

        } else if (secondToLastPart === 'vote') {
          // This is a vote on an answer.
          if ('helpful' in data) {
            value = 'Helpful';
          } else if ('not-helpful' in data) {
            value = 'Not Helpful';
          }
          questionPart = urlParts[urlParts.length - 3];
          answerPart = ' - ' + lastPart;
        } else {
          // This isn't a vote form we are interested in.
          return;
        }

        trackEvent(
          'Support Forum Vote',
          value,
          questionPart + answerPart);
      }
    });
  }

  $(document).ready(init);

})(jQuery);

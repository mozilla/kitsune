/*
 * Track the time spent on a KB article.
 */

(function($) {

"use strict";

if (!waffle.switch('track-article-reads')) {
    return;
}

var duration = 0,
    timer,
    currentLapStarted,
    durationsToRecord = [10, 30, 90],
    documentId = $('body').data('document-id'),
    trackUrl = $('body').data('track-url'),
    trackId = $.now();

function startTimer(startedTime) {
    currentLapStarted = startedTime;
    if (durationsToRecord.length > 0) {
        timer = setTimeout(stopTimer, 10000);
    }
}

function stopTimer() {
    var now = new Date();
    if (timer) {
        clearTimeout(timer);
        timer = null;
    }
    duration += now - currentLapStarted;

    if (durationsToRecord.length > 0) {
        if (duration >= durationsToRecord[0] * 1000) {
            record(duration);
            durationsToRecord = durationsToRecord.slice(1);
        }
        startTimer(now);
    }
}

function record(duration, sync) {
    var options = {
        url: trackUrl,
        data: {
            duration: duration / 1000,
            documentid: documentId,
            trackid: trackId
        }
    };
    if (sync) {
        options['async'] = false;
        options['timeout'] = 250;
    }
    $.ajax(options);
}

$(window).bind('beforeunload', function() {
    stopTimer();
    record(duration, true);
});

$(window).bind('load', function() {
    $(document).bind('focus', function() {
        startTimer(new Date());
        console.log('focus');
    });
    $(document).bind('blur', function() {
        stopTimer();
        console.log('blur');
    });
    if(document.hasFocus()) {
        startTimer(new Date());
    }
});

})(jQuery);
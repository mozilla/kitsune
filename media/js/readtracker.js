/*
 * Track the time spent on a KB article.
 */

(function($) {

"use strict";

var DEBUG = false,
    console;

if (DEBUG && window.console) {
    console = window.console;
} else {
    console = {};
    console.log = function(msg) {};
}

if (!waffle['switch']('track-article-reads')) {
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
    console.log('starting timer');
    currentLapStarted = startedTime;
    if (durationsToRecord.length > 0) {
        timer = setTimeout(stopTimer, 2500);
    }
}

function stopTimer(dontRestart) {
    console.log('stopping timer');
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
        if (!dontRestart) {
            startTimer(now);
        }
    }
}

function record(duration, sync) {
    // Make the request to record the duration so far.
    console.log('phoning home');
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
    // Stop timer and record total duration on the page.
    stopTimer(true);
    record(duration, true);
});

$(window).bind('load', function() {
    // Start timer on focus and stop on blur
    $(window).bind('focus', function() {
        console.log('focus');
        startTimer(new Date());
    });
    $(window).bind('blur', function() {
        console.log('blur');
        stopTimer(true); 
    });
    // If we have focus, start the timer.
    if(document.hasFocus()) {
        startTimer(new Date());
    }
});

})(jQuery);
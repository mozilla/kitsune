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
    trackId = $.now(),
    urlParams = getQueryParamsAsDict(window.location.search.substring(1)),
    referrer = getReferrer(),
    query = getSearchQuery();


function getQueryParamsAsDict(queryString) {
    // Parse the url query parameters into a dict. Mostly stolen from:
    // http://stackoverflow.com/questions/901115/get-query-string-values-in-javascript/2880929#2880929
    var urlParams = {},
        e,
        a = /\+/g,  // Regex for replacing addition symbol with a space
        r = /([^&=]+)=?([^&]*)/g,
        d = function (s) { return decodeURIComponent(s.replace(a, " ")); };

    while (e = r.exec(queryString)) {
       urlParams[d(e[1])] = d(e[2]);
    }
    return urlParams;
}

function getReferrer() {
    /*
    Get the referrer to the current page. Returns:
    - 'search' - if current url has as=s
    - 'inproduct' - if current url has as=u
    - actual referrer URL - if none of the above
    */
    if (urlParams['as'] === 's') {
        return 'search';
    } else if (urlParams['as'] === 'u') {
        return 'inproduct';
    } else {
        return document.referrer;
    }
}

function getSearchQuery() {
    // If the referrer is a search page, return the search keywords.
    if (referrer === 'search') {
        return urlParams['s'];
    } else if (referrer !== 'inproduct') {
        var splitUrl = referrer.split('?');
        if (splitUrl.length > 1) {
            return getQueryParamsAsDict(
                splitUrl.splice(1).join(''))['q'] || '';
        }
    }
    return '';
}

/*
startTimer and stopTimer are needed so we can properly handle blur and focus
events: blur stops the timer and focus restarts it. If we didn't need to take
that into account, we could just start setTimeout for each of the
durationsToRecord and be done.
*/

function startTimer(startedTime) {
    console.log('starting timer');
    currentLapStarted = startedTime;
    if (durationsToRecord.length > 0) {
        timer = setTimeout(stopTimer, 2500);
    }
}

function stopTimer(lateness, dontRestart) {
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
            trackid: trackId,
            referrer: referrer,
            query: query
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
    stopTimer(null, true);
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
        stopTimer(null, true);
    });
    // If we have focus, start the timer.
    if(document.hasFocus()) {
        startTimer(new Date());
    }
});

})(jQuery);

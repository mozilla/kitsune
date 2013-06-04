//
// Adapter for JS TestNet
// https://github.com/kumar303/jstestnet
//
// Be sure this file is loaded *after* qunit/testrunner.js or whatever else
// you're using

(function() {

    var canPost = false;
    try {
        canPost = !!window.top.postMessage;
    } catch(e){}
    if (!canPost) {
        return;
    }

    function postMsg(data) {
        var msg = '';
        for (var k in data) {
            if (msg.length > 0) {
                msg += '&';
            }
            msg += k + '=' + encodeURI(data[k]);
        }
        window.top.postMessage(msg, '*');
    }

    window.onerror = function(errorMsg, url, lineNumber) {
        var msg = {
            action: 'log',
            result: false, // failure
            message: 'Exception: ' + errorMsg + ' at ' + url + ':' + lineNumber,
            // TODO(Kumar) add stacktrace on platforms that support it
            // (like Firefox)
            stacktrace: null
        };
        postMsg(msg);
    };

    // QUnit (jQuery)
    // http://docs.jquery.com/QUnit
    if ( typeof QUnit !== "undefined" ) {

        QUnit.begin = function() {
            postMsg({
                action: 'hello',
                user_agent: navigator.userAgent
            });
        };

        QUnit.done = function(failures, total) {
            // // Clean up the HTML (remove any un-needed test markup)
            // $("nothiddendiv").remove();
            // $("loadediframe").remove();
            // $("dl").remove();
            // $("main").remove();
            //
            // // Show any collapsed results
            // $('ol').show();

            postMsg({
                action: 'done',
                failures: failures,
                total: total
            });
        };

        QUnit.log = function(result, message, details) {
            // Strip out html:
            message = message.replace(/&amp;/g, '&');
            message = message.replace(/&gt;/g, '>');
            message = message.replace(/&lt;/g, '<');
            message = message.replace(/<[^>]+>/g, '');
            var msg = {
                action: 'log',
                result: result,
                message: message,
                stacktrace: null
            };
            if (details) {
                if (typeof(details.source) !== 'undefined') {
                    msg.stacktrace = details.source;
                }
                if(typeof(details.actual) !== 'undefined' &&
                   typeof(details.expected) !== 'undefined') {
                    msg.actual = details.actual;
                    msg.expected = details.expected;
                }
            }
            postMsg(msg);
        };

        QUnit.moduleStart = function(name) {
            postMsg({
                action: 'set_module',
                name: name
            });
        };

        QUnit.testStart = function(name) {
            postMsg({
                action: 'set_test',
                name: name
            });
        };

        // window.TestSwarm.serialize = function(){
        //  // Clean up the HTML (remove any un-needed test markup)
        //  remove("nothiddendiv");
        //  remove("loadediframe");
        //  remove("dl");
        //  remove("main");
        //
        //  // Show any collapsed results
        //  var ol = document.getElementsByTagName("ol");
        //  for ( var i = 0; i < ol.length; i++ ) {
        //      ol[i].style.display = "block";
        //  }
        //
        //  return trimSerialize();
        // };
    } else {
        throw new Error("Cannot adapt to jstestnet: Unknown test runner");
    }

})();

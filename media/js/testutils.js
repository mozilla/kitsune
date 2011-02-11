
/*
    Functions that tests can use.
*/
tests = {};

tests.waitFor = function(checkCondition, config) {
    /*
        Wait for a condition before doing anything else.

        Good for making async tests fast on fast machines.
        Use it like this:

        tests.waitFor(function() {
            return (thing == 'done');
        }).thenDo(function() {
            equals(1,1);
            ok(stuff());
        });

        You can pass in a config object as the second argument
        with these possible attributed:

        config.interval = milliseconds to wait between polling condition
        config.timeout = milliseconds to wait before giving up on condition
    */
    if (typeof(config) === 'undefined') {
        config = {};
    }
    var interval = config.interval || 5,
        timeout = config.timeout || 300,
        run,
        runWhenReady,
        timeSpent = 0;

    run = function() {
        if (timeSpent > timeout) {
            throw new Error("Spent too long waiting for condition");
        }
        timeSpent += interval;
        var ready = checkCondition();
        if (!ready) {
            setTimeout(run, interval);
        } else {
            if (typeof runWhenReady === 'function') {
                runWhenReady();
            }
        }
    };
    setTimeout(run, interval);
    return {
        thenDo: function(fn) {
            runWhenReady = fn;
        }
    }
};

tests._sbCounter = 0;

tests.createSandbox = function(tmpl) {
    /*
        Returns a jQuery object for a temporary, unique div filled with html
        from a template.

        tmpl: an optional jQuery locator from which to copy html.  This would
              typically be the ID of a div in qunit.html

        Example::

            module('Group of tests', {
                setup: function() {
                    this.sandbox = tests.createSandbox('#foobar-template');
                },
                teardown: function() {
                    this.sandbox.remove();
                }
            });

            test('some test', function() {
                this.sandbox.append('...');
            });
    */
    tests._sbCounter++;
    var sb = $('<div id="sandbox-'+tests._sbCounter.toString()+'"></div>');
    if (tmpl) {
        sb.append($(tmpl).html());
    }
    $('#sandbox').append(sb);
    return sb;
};

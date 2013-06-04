/*
    Utilities for testing jQuery-based JavaScript code.
*/
tests = {};

tests.waitFor = function(checkCondition, config) {
    /*
        Wait for a condition before doing anything else.

        Good for making async tests fast on fast machines.
        Use it like this::

          tests.waitFor(function() {
              return (thing == 'done);
          }).thenDo(function() {
              equals(1,1);
              ok(stuff());
          });

        You can pass in a config object as the second argument
        with these possible attributes:

        **config.interval**
          milliseconds to wait between polling condition
        **config.timeout**
          milliseconds to wait before giving up on condition
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
            var cond = checkCondition.toString();
            ok(false, "Spent too long waiting for: " + cond);
            start();
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

        **tmpl**
          An optional jQuery locator from which to copy html.  This would
          typically be the ID of a div in your test runner HTML (e.g. qunit.html)

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

tests.StubOb = function(Orig, overrides) {
    /*
        Returns a class-like replacement for Orig.

        **Orig**
          object you want to replace.
        **overrides**
          object containing properties to override in the original.

        All properties in the overrides object will replace those of Orig's
        prototype when you create an instance of the class.  This is useful
        for stubbing out certain methods.  For example::

            z.FileData = tests.StubOb(z.FormData, {
                send: function() {}
            });

        This allows the creation of a FormData object that behaves just like
        the original except that send() does not actually post data during
        a test::

            var fileData = new z.FileData();
            fileData.send(); // does nothing

        Be sure to assign the original class back when you're done testing.
    */
    return function() {
        var ob = {}
        Orig.apply(ob, this.arguments);
        for (k in overrides) {
            ob[k] = overrides[k];
        }
        return ob;
    }
};

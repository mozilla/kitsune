'use strict';

var ajaxVoteFixture = {
    setup: function() {
        this.sandbox = tests.createSandbox('#ajaxvote');
        $.mockjax({
            url: '/vote',
            status: 200,
            contentType: 'text/json',
            responseTime: 0,
            response: function(settings) {
                // set the response message to the key/values POSTed
                var message = '';
                $.each(settings.data, function(key, val) {
                    message += key + ':' + val + ';';
                });
                this.responseText = { message: message };
            }
        });
    },
    teardown: function() {
        this.sandbox.remove();
        $.mockjaxClear();
    }
};

module('ajaxvote', ajaxVoteFixture);

asyncTest('helpful vote', function() {
    var $sandbox = this.sandbox,
        $messageBox;
    new k.AjaxVote($sandbox.find('form.vote'), {
        positionMessage: true,
        removeForm: true
    });
    $sandbox.find('input[name="helpful"]').click();
    tests.waitFor(function() {
        $messageBox = $('.ajax-vote-box');
        return $messageBox.length > 0;
    }, {
        timeout: 2000
    }).thenDo(function() {
        equals('foo:bar;helpful:Yes;', $messageBox.text(), 'Correct message returned.');
        $messageBox.remove();
        start();
    });
});

asyncTest('not helpful vote', function() {
    var $sandbox = this.sandbox,
        $messageBox;
    new k.AjaxVote($sandbox.find('form.vote'), {
        positionMessage: false,
        removeForm: true
    });
    $sandbox.find('input[name="not-helpful"]').click();
    tests.waitFor(function() {
        $messageBox = $('.ajax-vote-box');
        return $messageBox.length > 0;
    }, {
        timeout: 2000
    }).thenDo(function() {
        equals('foo:bar;not-helpful:No;', $messageBox.text(), 'Correct message returned.');
        $messageBox.remove();
        start();
    });
});

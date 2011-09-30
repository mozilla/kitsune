$(document).ready(function(){

"use strict";

var ajaxPreviewFixture = {
    setup: function() {
        this.sandbox = tests.createSandbox('#ajaxpreview');
        $.mockjax({
            url: '/preview',
            status: 200,
            contentType: 'text/json',
            responseTime: 0,
            response: function(settings) {
                equals('tokenvalue', settings.data.csrfmiddlewaretoken);
                equals('The content to preview.', settings.data.content)
                this.responseText = '<p>The content to preview.</p>';
            }
        });
    },
    teardown: function() {
        this.sandbox.remove();
        $.mockjaxClear();
    }
};

module('ajaxpreview', ajaxPreviewFixture);

asyncTest('ajax preview events', function() {
    var $sandbox = this.sandbox,
        $preview = $sandbox.find('#preview-container'),
        ajaxPreview = new k.AjaxPreview($sandbox.find('#preview')),
        calledShow = false,
        calledDone = false;
    $(ajaxPreview).bind('show-preview', function(e, success, content) {
        equals(content, '<p>The content to preview.</p>');
        ok(success);
        calledShow = true;
    });
    $(ajaxPreview).bind('done', function(e, success) {
        ok(success);
        calledDone = true;
    });
    $(ajaxPreview).trigger('get-preview');
    tests.waitFor(function() {
        return calledShow && calledDone;
    }, {
        timeout: 2000
    }).thenDo(function() {
        start();
    });
});

asyncTest('integrated (with DOM events) ajax preview', function() {
    var $sandbox = this.sandbox,
        $preview = $sandbox.find('#preview-container');
    new k.AjaxPreview($sandbox.find('#preview'));
    $sandbox.find('#preview').click();
    tests.waitFor(function() {
        return $preview.text().length > 0;
    }, {
        timeout: 2000
    }).thenDo(function() {
        equals('<p>The content to preview.</p>', $preview.html(),
               'Correct preview displayed.');
        start();
    });
});


});

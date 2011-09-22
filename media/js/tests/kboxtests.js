$(document).ready(function(){

"use strict";

var kboxFixture = {
    setup: function() {
        this.sandbox = tests.createSandbox('#kbox');
    },
    teardown: function() {
        this.sandbox.remove();
    }
};

module('kbox', kboxFixture);

test('declarative', function() {
    var $sandbox = this.sandbox;
    $sandbox.find('.kbox').kbox().each(function() {
        // kboxes shouldn't be visible initially
        ok($(this).is(':hidden'), 'kbox starts hidden');
        // If there is a target, click it. Otherwise, open programmatically.
        var target = $(this).attr('data-target');
        if (target) {
            $(target).click();
        } else {
            $(this).data('kbox').open();
        }
        ok($(this).is(':visible'), 'kbox is now visible');
        equals($(this).attr('title') || $(this).attr('data-title'),
               $sandbox.find('.kbox-title').text(),
               'kbox title is correct');
        if($(this).data('modal')) {
            ok($('#kbox-overlay').length === 1 &&
               $('#kbox-overlay').is(':visible'), 'overlay for modal kbox');
        }
        var kbox = $(this).data('kbox');
        kbox.close();
        ok($(this).is(':hidden'), 'kbox is not visible anymore');
        kbox.destroy();
        equals(0, $sandbox.find('.kbox-container').length,
               'destroy cleans up kbox properly');
        ok($('#kbox-overlay').length === 0, 'overlay cleaned up')
    });
});

});

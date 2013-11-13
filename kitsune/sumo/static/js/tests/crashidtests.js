(function() {

'use strict';

var crashidLinking = {
    setup: function() {
        this.sandbox = tests.createSandbox('#postwithcrashids');
    },
    teardown: function() {
        this.sandbox.remove();
    }
};

module('crashid_linking', crashidLinking);

test('link_one_crash_id', function() {
    var $sandbox = this.sandbox;
    var numIds = 0;
    var content = $sandbox.find('.content_1');
    k.linkCrashIds(content);
    numIds = content.find('.crash-report').length;
    equals(numIds, 1);
});

test('link_multiple_crash_ids', function() {
    var $sandbox = this.sandbox;
    var numIds = 0;
    var content = $sandbox.find('.content_2');
    k.linkCrashIds(content);
    numIds = content.find('.crash-report').length;
    equals(numIds, 5);
});

test('dont_link_invalid_crash_id', function() {
    var $sandbox = this.sandbox;
    var numIds = 0;
    var content = $sandbox.find('.content_3');
    k.linkCrashIds(content);
    numIds = content.find('.crash-report').length;
    equals(numIds, 0);
});

test('dont_link_crash_id_without_bp', function() {
    var $sandbox = this.sandbox;
    var numIds = 0;
    var content = $sandbox.find('.content_4');
    k.linkCrashIds(content);
    numIds = content.find('.crash-report').length;
    equals(numIds, 0);
});

})();

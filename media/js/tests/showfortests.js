/*jshint*/
/*globals tests:true, ShowFor:true, module:true, equals:true, test:true, $:true */
$(document).ready(function(){

"use strict";

var showforFixture = {
    setup: function() {
        var $sandbox = tests.createSandbox('#showfor'),
            options = {
                osSelector: 'select.os',
                browserSelector: 'select.browser'
            },
            $b = $sandbox.find(options.browserSelector),
            $o = $sandbox.find(options.osSelector);
        ShowFor.initForTags(options, $sandbox);
        this.$sandbox = $sandbox;
        this.$b = $b;
        this.$o = $o;
    },
    teardown: function() {
        this.$sandbox.remove();
    }
};

module('showfor', showforFixture);

function assertNotVisible($sandbox, forVals) {
    for (var i=0,l=forVals.length; i<l; i++) {
        equals($sandbox.find('[data-for="' + forVals[i] + '"]:visible').length, 0,
               '[data-for=' + forVals[i] + '] is not visible');
    }
}
function assertNotHidden($sandbox, forVals) {
    for (var i=0,l=forVals.length; i<l; i++) {
        equals($sandbox.find('[data-for="' + forVals[i] + '"]:hidden').length, 0,
               '[data-for=' + forVals[i] + '] is not hidden');
    }
}

test('default', function() {
    // Make sure initial setup is good (for example, on mac: data-for="mac"
    // shows and data-for="not mac" doesn't show)
    assertNotHidden(this.$sandbox, [this.$b.val(), this.$o.val()]);
    assertNotVisible(this.$sandbox, ['not ' + this.$b.val(), 'not ' + this.$o.val()]);
});

test('windows fx4', function() {
    $('#_input_win').click();
    $('#_input_fx4').click();
    equals(this.$o.val(), 'win', 'Windows is now selected');
    equals(this.$b.val(), 'fx4', 'Firefox 4 is now selected');
    assertNotHidden(this.$sandbox, ['win', 'not mac', 'android', 'fx35,fx4', 'fx4', 'm4', 'm5', 'win,fx4']);
    assertNotVisible(this.$sandbox, ['mac,linux', 'maemo', 'fx3', 'fx5', 'fx6', 'win,fx35']);
});

test('windows versions', function() {
    $('#_input_winxp').click();
    equals(this.$o.val(), 'winxp', 'Windows XP is now selected');
    assertNotHidden(this.$sandbox, ['win', 'winxp']);
    assertNotVisible(this.$sandbox, ['win8', 'win7', 'mac', 'linux']);

    $('#_input_win7').click();
    equals(this.$o.val(), 'win7', 'Windows 7/Vista is now selected');
    assertNotHidden(this.$sandbox, ['win', 'win7']);
    assertNotVisible(this.$sandbox, ['win8', 'winxp', 'mac', 'linux']);

    $('#_input_win8').click();
    equals(this.$o.val(), 'win8', 'Windows 8 is now selected');
    assertNotHidden(this.$sandbox, ['win', 'win8']);
    assertNotVisible(this.$sandbox, ['winxp', 'win7', 'mac', 'linux']);
});

test('linux fx35', function() {
    $('#_input_linux').click();
    $('#_input_fx35').click();
    equals(this.$o.val(), 'linux', 'Linux is now selected');
    equals(this.$b.val(), 'fx35', 'Firefox 3.5/6 is now selected');
    assertNotHidden(this.$sandbox, ['not mac', 'mac,linux', 'android', 'fx35,fx4', 'm4', 'm5']);
    assertNotVisible(this.$sandbox, ['win', 'maemo', 'fx3', 'fx4', 'fx5', 'fx6', 'win,fx4', 'win,fx35']);
});

test('mac fx5', function() {
    $('#_input_mac').click();
    $('#_input_fx5').click();
    equals(this.$o.val(), 'mac', 'Mac is now selected');
    equals(this.$b.val(), 'fx5', 'Firefox 5 is now selected');
    assertNotHidden(this.$sandbox, ['mac,linux', 'android', 'm4', 'fx35,fx4', 'fx4', 'fx5', 'm5']);
    assertNotVisible(this.$sandbox, ['not mac', 'win', 'maemo', 'fx3', 'fx6''win,fx4', 'win,fx35']);
});

test('windows fx6', function() {
    $('#_input_win').click();
    $('#_input_fx6').click();
    equals(this.$o.val(), 'win', 'Windows is now selected');
    equals(this.$b.val(), 'fx6', 'Firefox 6 is now selected');
    assertNotHidden(this.$sandbox, ['win', 'not mac', 'android', 'fx35,fx4', 'fx4', 'fx5', 'fx6', 'm4', 'm5', 'win,fx4']);
    assertNotVisible(this.$sandbox, ['mac,linux', 'maemo', 'fx3''win,fx35']);
});

test('android m4', function() {
    $('#_input_android').click();
    $('#_input_m4').click();
    equals(this.$o.val(), 'android', 'Android is now selected');
    equals(this.$b.val(), 'm4', 'Firefox 4 is now selected');
    assertNotHidden(this.$sandbox, ['win', 'win7', 'not mac', 'android', 'm4', 'fx35,fx4', 'fx4', 'fx5', 'win,fx4']);
    assertNotVisible(this.$sandbox, ['mac,linux', 'maemo', 'fx3', 'm5', 'fx6', 'winxp', 'win8', 'win,fx35']);
});

test('maemo m5', function() {
    $('#_input_maemo').click();
    $('#_input_m5').click();
    equals(this.$o.val(), 'maemo', 'Maemo is now selected');
    equals(this.$b.val(), 'm5', 'Firefox 5 is now selected');
    assertNotHidden(this.$sandbox, ['win', 'not mac', 'maemo', 'm4', 'm5', 'fx35,fx4', 'fx4', 'fx5', 'win,fx4']);
    assertNotVisible(this.$sandbox, ['mac,linux', 'android', 'fx3', 'fx6', 'win,fx35']);
});

module('ShowFor.addBrowserToSelect', showforFixture);
// Test that browser versions get inserted in the right spot.

test('fx9', function() {
    var $select = this.$sandbox.find('select.browser-insert-test'),
        length = $select.find('option').length;
    ShowFor.addBrowserToSelect($select, 'fx9');
    equals($select.find('option').length, length + 1);
    equals($select.find('option')[0].value, 'fx9');
});

test('fx5', function() {
    var $select = this.$sandbox.find('select.browser-insert-test'),
        length = $select.find('option').length;
    ShowFor.addBrowserToSelect($select, 'fx5');
    equals($select.find('option').length, length + 1);
    equals($select.find('option')[length - 1].value, 'fx5');
});

test('fx4', function() {
    var $select = this.$sandbox.find('select.browser-insert-test'),
        length = $select.find('option').length;
    ShowFor.addBrowserToSelect($select, 'fx4');
    equals($select.find('option').length, length + 1);
    equals($select.find('option')[length - 1].value, 'fx4');
});

test('fx3', function() {
    var $select = this.$sandbox.find('select.browser-insert-test'),
        length = $select.find('option').length;
    ShowFor.addBrowserToSelect($select, 'fx3');
    equals($select.find('option').length, length + 1);
    equals($select.find('option')[length].value, 'fx3');
});


var showforMobileOnlyFixture = {
    setup: function() {
        var $sandbox = tests.createSandbox('#showfor-mobile-only'),
            options = {
                osSelector: 'select.os',
                browserSelector: 'select.browser'
            },
            $b = $sandbox.find(options.browserSelector),
            $o = $sandbox.find(options.osSelector);
        ShowFor.initForTags(options, $sandbox);
        this.$sandbox = $sandbox;
        this.$b = $b;
        this.$o = $o;
    },
    teardown: function() {
        this.$sandbox.remove();
    }
};

module('showforMobileOnly', showforMobileOnlyFixture);

test('android m15', function() {
    $('#_input_android').click();
    $('#_input_m15').click();
    equals(this.$o.val(), 'android', 'Android is now selected');
    equals(this.$b.val(), 'm15', 'Firefox 15 is now selected');
    assertNotHidden(this.$sandbox, ['android', 'm15']);
    assertNotVisible(this.$sandbox, ['m16', 'maemo']);
});

test('android m16', function() {
    $('#_input_android').click();
    $('#_input_m16').click();
    equals(this.$o.val(), 'android', 'Android is now selected');
    equals(this.$b.val(), 'm16', 'Firefox 16 is now selected');
    assertNotHidden(this.$sandbox, ['android', 'm15', 'm16']);
    assertNotVisible(this.$sandbox, ['maemo']);
});


var showforDesktopOnlyFixture = {
    setup: function() {
        var $sandbox = tests.createSandbox('#showfor-desktop-only'),
            options = {
                osSelector: 'select.os',
                browserSelector: 'select.browser'
            },
            $b = $sandbox.find(options.browserSelector),
            $o = $sandbox.find(options.osSelector);
        ShowFor.initForTags(options, $sandbox);
        this.$sandbox = $sandbox;
        this.$b = $b;
        this.$o = $o;
    },
    teardown: function() {
        this.$sandbox.remove();
    }
};

module('showforDesktopOnly', showforDesktopOnlyFixture);

test('win fx15', function() {
    $('#_input_win').click();
    $('#_input_fx15').click();
    equals(this.$o.val(), 'win', 'Windows is now selected');
    equals(this.$b.val(), 'fx15', 'Firefox 15 is now selected');
    assertNotHidden(this.$sandbox, ['win', 'fx15']);
    assertNotVisible(this.$sandbox, ['fx16', 'fx17', 'mac', 'linux']);
});

test('mac fx16', function() {
    $('#_input_mac').click();
    $('#_input_fx16').click();
    equals(this.$o.val(), 'mac', 'Mac is now selected');
    equals(this.$b.val(), 'fx16', 'Firefox 16 is now selected');
    assertNotHidden(this.$sandbox, ['mac', 'fx15', 'fx16']);
    assertNotVisible(this.$sandbox, ['fx17', 'win', 'linux']);
});

test('linux fx17', function() {
    $('#_input_linux').click();
    $('#_input_fx17').click();
    equals(this.$o.val(), 'linux', 'Linux is now selected');
    equals(this.$b.val(), 'fx17', 'Firefox 17 is now selected');
    assertNotHidden(this.$sandbox, ['linux', 'fx17', 'fx16', 'fx15']);
    assertNotVisible(this.$sandbox, ['win', 'mac']);
});

});
